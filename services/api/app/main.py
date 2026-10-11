import asyncio
import json
import os
from collections.abc import Callable
from typing import Annotated, Any
from uuid import uuid4

import anyio
from fastapi import Depends, FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from services.api.app.contracts.schemas import (
    IntroSeenRequest,
    IntroSeenResponse,
    PlayAgainRequest,
    PlayAgainResponse,
)
from services.api.app.game.store import CommandOutcome, GameError, GameStore
from services.api.app.realtime import Connection, ConnectionHub

DEFAULT_ALLOWED_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


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


def allowed_origins_from_env() -> tuple[str, ...]:
    configured = os.environ.get("ALLOWED_ORIGINS", "")
    origins = tuple(origin.strip() for origin in configured.split(",") if origin.strip())
    return origins or DEFAULT_ALLOWED_ORIGINS


def create_app(database_url: str | None = None, *, allowed_origins: tuple[str, ...] | None = None) -> FastAPI:
    """Build the API. The database must already be migrated (see supabase/migrations)."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    origins = frozenset(allowed_origins if allowed_origins is not None else allowed_origins_from_env())

    app = FastAPI(title="Heary Drawy API", version="0.1.0")
    store = GameStore(url)
    hub = ConnectionHub(store)
    app.state.game_store = store

    @app.exception_handler(GameError)
    async def game_error_handler(_request: Any, error: GameError) -> JSONResponse:
        return error_response(error)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/rooms")
    def create_room_disabled() -> JSONResponse:
        return error_response(
            GameError(
                "host_authorization_unavailable",
                "Grown-up room controls need separate authorization before they can be used.",
                403,
            )
        )

    @app.get("/api/v1/rooms/{room_id}/state")
    async def room_state(room_id: str, token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        snapshot = await run_in_threadpool(store.get_snapshot, token, room_id, hub.connected_player_ids())
        return snapshot.model_dump(mode="json", exclude_none=True)

    async def run_round_command(
        method: Callable[[str, str, str, int], CommandOutcome], token: str, round_id: str, command: IntroSeenRequest
    ) -> dict[str, Any]:
        if command.round_id != round_id:
            raise GameError("stale_round", "The round has changed. Refresh to continue.", 409)
        outcome = await run_in_threadpool(method, token, round_id, command.command_id, command.expected_round_version)
        await hub.push_snapshots(outcome.notify_player_ids)
        return outcome.response

    @app.post("/api/v1/rounds/{round_id}/intro-seen", response_model=IntroSeenResponse)
    async def intro_seen(round_id: str, request: IntroSeenRequest, token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        return await run_round_command(store.acknowledge_intro, token, round_id, request)

    @app.post("/api/v1/rounds/{round_id}/play-again", response_model=PlayAgainResponse)
    async def play_again(round_id: str, request: PlayAgainRequest, token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        return await run_round_command(store.play_again, token, round_id, request)

    socket_commands: dict[str, tuple[type[IntroSeenRequest], Callable[[str, str, str, int], CommandOutcome]]] = {
        "round.intro.seen": (IntroSeenRequest, store.acknowledge_intro),
        "round.play_again": (PlayAgainRequest, store.play_again),
    }

    async def handle_socket_message(connection: Connection, incoming: dict[str, Any]) -> None:
        if incoming.get("protocol_version") != 1:
            raise GameError("payload_invalid", "Unsupported socket message.", 422)
        message_type = incoming.get("type")
        if message_type == "state.request":
            await hub.send_snapshot(connection)
            return
        if message_type not in socket_commands:
            raise GameError("payload_invalid", "This command is not available yet.", 422)
        request_model, method = socket_commands[message_type]
        raw_payload = incoming.get("payload")
        if not isinstance(raw_payload, dict):
            raise GameError("payload_invalid", "That message could not be read.", 422)
        try:
            command = request_model.model_validate(
                {**raw_payload, "command_id": incoming.get("command_id"), "round_id": incoming.get("round_id")}
            )
        except ValidationError as exc:
            raise GameError("payload_invalid", "That message could not be read.", 422) from exc
        outcome = await run_in_threadpool(
            method, connection.token, command.round_id, command.command_id, command.expected_round_version
        )
        await connection.send(
            {
                "protocol_version": 1,
                "type": "command.ack",
                "command_id": command.command_id,
                "event_id": f"event_{uuid4().hex}",
                "payload": outcome.response,
            }
        )
        await hub.push_snapshots(outcome.notify_player_ids)

    @app.websocket("/api/v1/rooms/{room_id}/socket")
    async def room_socket(websocket: WebSocket, room_id: str) -> None:
        if websocket.headers.get("origin") not in origins:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        connection: Connection | None = None
        try:
            message = receive_message(await asyncio.wait_for(websocket.receive_text(), timeout=5))
            if message.get("protocol_version") != 1 or message.get("type") != "session.authenticate":
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
            _session, player = await run_in_threadpool(store.authenticate, token, room_id)
            connection = Connection(websocket, token, room_id, player["player_id"])
            hub.register(connection)
            await connection.send(
                {
                    "protocol_version": 1,
                    "type": "session.authenticated",
                    "event_id": f"event_{uuid4().hex}",
                    "payload": {"connection_epoch": uuid4().hex, "player_id": connection.player_id},
                }
            )
            # Everyone in the pair learns this player is connected; a waiting player just gets state.
            members = await run_in_threadpool(store.pair_member_ids, connection.player_id)
            await hub.push_snapshots(members or (connection.player_id,))
            while True:
                incoming = receive_message(await websocket.receive_text())
                try:
                    await handle_socket_message(connection, incoming)
                except GameError as error:
                    await connection.send(
                        {
                            "protocol_version": 1,
                            "type": "command.error",
                            "command_id": incoming.get("command_id"),
                            "payload": store.error_payload(error),
                        }
                    )
        except GameError as error:
            await websocket.send_json({"protocol_version": 1, "type": "command.error", "payload": store.error_payload(error)})
            await websocket.close(code=1008)
        except WebSocketDisconnect:
            pass
        except TimeoutError:
            await websocket.close(code=1008)
        finally:
            if connection is not None:
                hub.unregister(connection)
                # Shielded so the teammate still learns about the disconnect when this task is cancelled.
                with anyio.CancelScope(shield=True):
                    members = await run_in_threadpool(store.pair_member_ids, connection.player_id)
                    await hub.push_snapshots(m for m in members if m != connection.player_id)

    return app
