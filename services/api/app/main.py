import asyncio
import json
from pathlib import Path
from tempfile import gettempdir
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from services.api.app.contracts.schemas import IntroSeenRequest, IntroSeenResponse, JoinRoomRequest, JoinRoomResponse
from services.api.app.game.store import GameError, GameStore

DEFAULT_DB_PATH = Path(gettempdir()) / "heary-drawy-api.sqlite3"


class DisabledHostRoomRequest(BaseModel):
    shape_code: list[str] | None = None


def bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise GameError("session_invalid", "Join again to continue.", 401)
    return authorization.removeprefix("Bearer ").strip()


def error_response(error: GameError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message, "retryable": error.retryable}},
    )


def receive_message(text: str) -> dict[str, Any]:
    if len(text.encode("utf-8")) > 8192:
        raise GameError("payload_invalid", "Message is too large.", 422)
    try:
        message = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GameError("payload_invalid", "Message could not be read.", 422) from exc
    if not isinstance(message, dict):
        raise GameError("payload_invalid", "Message could not be read.", 422)
    return message


def create_app(db_path: str | Path = DEFAULT_DB_PATH, *, fixture_room: bool = False) -> FastAPI:
    app = FastAPI(title="Heary Drawy API", version="0.1.0")
    store = GameStore(db_path, fixture_room=fixture_room)
    app.state.game_store = store

    @app.exception_handler(GameError)
    async def game_error_handler(_request: Any, error: GameError) -> JSONResponse:
        return error_response(error)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/rooms")
    def create_room_disabled(_request: DisabledHostRoomRequest | None = None) -> JSONResponse:
        return error_response(
            GameError(
                "host_authorization_unavailable",
                "Grown-up room controls need separate authorization before they can be used.",
                403,
            )
        )

    @app.post("/api/v1/rooms/join", response_model=JoinRoomResponse, status_code=201)
    def join_room(request: JoinRoomRequest) -> JoinRoomResponse:
        result = store.join_room(request.shape_code, request.nickname, request.avatar_id)
        return JoinRoomResponse(**result.__dict__)

    @app.get("/api/v1/rooms/{room_id}/state")
    def room_state(room_id: str, token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        snapshot = store.get_snapshot(token, room_id)
        return snapshot.model_dump(mode="json", exclude_none=True)

    @app.post("/api/v1/rounds/{round_id}/intro-seen", response_model=IntroSeenResponse)
    def intro_seen(round_id: str, request: IntroSeenRequest, token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        if request.round_id != round_id:
            raise GameError("stale_round", "The round has changed. Refresh to continue.", 409)
        return store.acknowledge_intro(token, round_id, request.command_id, request.expected_round_version)

    @app.websocket("/api/v1/rooms/{room_id}/socket")
    async def room_socket(websocket: WebSocket, room_id: str) -> None:
        origin = websocket.headers.get("origin")
        if origin not in {"http://localhost:5173", "http://127.0.0.1:5173", "http://testserver"}:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            message = receive_message(await asyncio.wait_for(websocket.receive_text(), timeout=5))
            if not isinstance(message, dict) or message.get("protocol_version") != 1 or message.get("type") != "session.authenticate":
                await websocket.send_json(
                    {
                        "protocol_version": 1,
                        "type": "command.error",
                        "payload": {"error": {"code": "session_invalid", "message": "Authenticate before state is sent.", "retryable": False}},
                    }
                )
                await websocket.close(code=1008)
                return
            auth_payload = message.get("payload")
            token = auth_payload.get("guest_session_token") if isinstance(auth_payload, dict) else None
            if not isinstance(token, str):
                raise GameError("session_invalid", "Join again to continue.", 401)
            snapshot = store.get_snapshot(token, room_id)
            payload = snapshot.model_dump(mode="json", exclude_none=True)
            await websocket.send_json(
                {
                    "protocol_version": 1,
                    "type": "session.authenticated",
                    "event_id": f"event_{uuid4().hex}",
                    "payload": {"connection_epoch": uuid4().hex, "player_id": payload["session_player_id"]},
                }
            )
            await websocket.send_json(
                {
                    "protocol_version": 1,
                    "type": "state.snapshot",
                    "event_id": payload.get("snapshot_id", f"event_{uuid4().hex}"),
                    "round_id": payload.get("round", {}).get("round_id"),
                    "payload": payload,
                }
            )
            while True:
                incoming = receive_message(await websocket.receive_text())
                try:
                    if incoming.get("protocol_version") != 1:
                        raise GameError("payload_invalid", "Unsupported socket message.", 422)
                    if incoming.get("type") == "round.intro.seen":
                        raw_payload = incoming.get("payload")
                        if not isinstance(raw_payload, dict):
                            raise GameError("payload_invalid", "Invalid intro acknowledgement.", 422)
                        try:
                            command = IntroSeenRequest.model_validate({
                                **raw_payload, "command_id": incoming.get("command_id"),
                                "round_id": incoming.get("round_id"),
                            })
                        except ValidationError as exc:
                            raise GameError("payload_invalid", "Invalid intro acknowledgement.", 422) from exc
                        outcome = store.acknowledge_intro(token, command.round_id, command.command_id, command.expected_round_version)
                        await websocket.send_json({"protocol_version": 1, "type": "command.ack", "command_id": command.command_id,
                                                   "event_id": f"event_{uuid4().hex}", "payload": outcome})
                    elif incoming.get("type") != "state.request":
                        raise GameError("payload_invalid", "This command is not available yet.", 422)
                    snapshot = store.get_snapshot(token, room_id)
                    payload = snapshot.model_dump(mode="json", exclude_none=True)
                    await websocket.send_json(
                        {"protocol_version": 1, "type": "state.snapshot", "event_id": payload.get("snapshot_id", f"event_{uuid4().hex}"),
                         "round_id": payload.get("round", {}).get("round_id"), "payload": payload}
                    )
                except GameError as error:
                    await websocket.send_json({"protocol_version": 1, "type": "command.error",
                                               "command_id": incoming.get("command_id"), "payload": store.error_payload(error)})
        except GameError as error:
            await websocket.send_json(
                {
                    "protocol_version": 1,
                    "type": "command.error",
                    "payload": store.error_payload(error),
                }
            )
            await websocket.close(code=1008)
        except WebSocketDisconnect:
            return
        except TimeoutError:
            await websocket.close(code=1008)

    return app


app = create_app()
