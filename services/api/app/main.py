import asyncio
import json
import logging
import os
import tempfile
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Annotated, Any
from uuid import uuid4

import anyio
from fastapi import Depends, FastAPI, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from services.api.app.contracts.schemas import (
    DeviceEnrollmentRequest,
    DeviceEnrollmentResponse,
    GuestAdmissionRequest,
    GuestAdmissionResponse,
    IntroSeenRequest,
    IntroSeenResponse,
    LeaveResponse,
    LobbyResponse,
    PlayAgainRequest,
    PlayAgainResponse,
    SubmitDrawingResponse,
)
from services.api.app.game.feedback import ask_deepseek, render_png
from services.api.app.game.store import CommandOutcome, GameError, GameStore
from services.api.app.game.transcribe import transcribe_file
from services.api.app.realtime import Connection, ConnectionHub

DEFAULT_ALLOWED_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
MAX_CLIP_BYTES = 2 * 1024 * 1024  # About a minute of compressed speech.
logger = logging.getLogger("heary_drawy.api")


def bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise GameError("session_invalid", "Join again to continue.", 401)
    return authorization.removeprefix("Bearer ").strip()


def device_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise GameError("device_not_enrolled", "Ask a grown-up to unlock this device again.", 401)
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


def create_app(
    database_url: str | None = None,
    *,
    allowed_origins: tuple[str, ...] | None = None,
    transcribe: Callable[[str], str] = transcribe_file,
    ask_ai: Callable[..., dict[str, Any] | None] = ask_deepseek,
    clip_grace_seconds: float = 1.0,
    clip_wait_seconds: float = 15.0,
) -> FastAPI:
    """Build the API. The database must already be migrated (see supabase/migrations).

    `transcribe` and `ask_ai` default to local Whisper and DeepSeek; tests pass stand-ins.
    """
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    origins = frozenset(allowed_origins if allowed_origins is not None else allowed_origins_from_env())
    store = GameStore(url)
    hub = ConnectionHub(store)
    background: set[asyncio.Task[None]] = set()

    def spawn(work: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(work)
        background.add(task)
        task.add_done_callback(background.discard)

    async def transcribe_clip(clip_id: str, audio: bytes, suffix: str) -> None:
        """Whisper turns the clip into text; the audio file is deleted right after."""
        text: str | None = None
        with tempfile.NamedTemporaryFile(suffix=suffix) as file:
            file.write(audio)
            file.flush()
            try:
                text = await run_in_threadpool(transcribe, file.name)
            except Exception as exc:  # noqa: BLE001 - a bad clip must never stop the round.
                logger.info("clip transcription failed: %s", type(exc).__name__)
        await run_in_threadpool(store.finish_clip, clip_id, text)

    async def check_round(round_id: str) -> None:
        """Drawy is looking: wait briefly for the last clips, ask the AI once, then reveal."""
        await asyncio.sleep(clip_grace_seconds)  # A clip released together with Done is still uploading.
        deadline = asyncio.get_running_loop().time() + clip_wait_seconds
        while await run_in_threadpool(store.pending_clips, round_id) and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.5)
        result = None
        data = await run_in_threadpool(store.feedback_input, round_id)
        if data:
            png = await run_in_threadpool(render_png, data["strokes"])
            result = await run_in_threadpool(ask_ai, data["name"], data["features"], data["transcript"], png)
        await hub.push_snapshots(await run_in_threadpool(store.publish_result, round_id, result))

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # A restart mid-check would leave a round on the checking screen; finish those first.
        for round_id in await run_in_threadpool(store.rounds_in_finalizing):
            spawn(check_round(round_id))
        yield

    app = FastAPI(title="Heary Drawy API", version="0.1.0", lifespan=lifespan)
    app.state.game_store = store

    @app.exception_handler(GameError)
    async def game_error_handler(_request: Any, error: GameError) -> JSONResponse:
        return error_response(error)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Rooms are provisioned by the operator command, which prints the grown-up passcode.
    @app.post("/api/v1/rooms")
    def create_room_disabled() -> JSONResponse:
        return error_response(
            GameError(
                "host_authorization_unavailable",
                "Grown-up room controls need separate authorization before they can be used.",
                403,
            )
        )

    @app.post("/api/v1/device-enrollments", status_code=201, response_model=DeviceEnrollmentResponse)
    async def enroll_device(request: DeviceEnrollmentRequest) -> dict[str, Any]:
        enrollment = await run_in_threadpool(store.enroll_device, request.passcode)
        return {"room_id": enrollment.room_id, "device_token": enrollment.device_token, "expires_at": enrollment.expires_at}

    @app.get("/api/v1/rooms/{room_id}/lobby", response_model=LobbyResponse)
    async def lobby(room_id: str, token: Annotated[str, Depends(device_token)]) -> dict[str, Any]:
        return {"taken_avatar_ids": await run_in_threadpool(store.lobby, token, room_id)}

    @app.post("/api/v1/rooms/{room_id}/guests", status_code=201, response_model=GuestAdmissionResponse)
    async def admit_guest(
        room_id: str, request: GuestAdmissionRequest, token: Annotated[str, Depends(device_token)]
    ) -> dict[str, Any]:
        result = await run_in_threadpool(store.admit_with_device, token, room_id, request.nickname, request.avatar_id)
        await hub.push_snapshots(result.notify_player_ids)
        return {
            "room_id": result.room_id,
            "player_id": result.player_id,
            "guest_session_token": result.guest_session_token,
            "expires_at": result.expires_at,
            "admission_status": result.admission_status,
        }

    @app.post("/api/v1/session/leave", response_model=LeaveResponse)
    async def leave(token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        player_id, teammates = await run_in_threadpool(store.leave, token)
        await hub.close_player(player_id)
        await hub.push_snapshots(teammates)
        return {"status": "left"}

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

    @app.post("/api/v1/rounds/{round_id}/submit", response_model=SubmitDrawingResponse)
    async def submit(round_id: str, request: IntroSeenRequest, token: Annotated[str, Depends(bearer_token)]) -> dict[str, Any]:
        response = await run_round_command(store.submit_drawing, token, round_id, request)
        spawn(check_round(round_id))
        return response

    @app.post("/api/v1/rounds/{round_id}/clips", status_code=202)
    async def upload_clip(round_id: str, request: Request, token: Annotated[str, Depends(bearer_token)]) -> dict[str, str]:
        """One hold-to-talk clip, sent after release. Partner audio never waits for this."""
        if int(request.headers.get("content-length") or 0) > MAX_CLIP_BYTES:
            raise GameError("payload_invalid", "That clip is too long.", 422)
        audio = await request.body()
        if not audio or len(audio) > MAX_CLIP_BYTES:
            raise GameError("payload_invalid", "That clip could not be used.", 422)
        clip_id = await run_in_threadpool(store.add_clip, token, round_id)
        suffix = ".webm" if "webm" in request.headers.get("content-type", "") else ".mp4"
        spawn(transcribe_clip(clip_id, audio, suffix))
        return {"clip_id": clip_id}

    @app.get("/api/v1/rounds/{round_id}/picture")
    async def picture(round_id: str, token: Annotated[str, Depends(bearer_token)]) -> Response:
        svg = await run_in_threadpool(store.picture_svg, token, round_id)
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store"})

    socket_commands: dict[str, tuple[type[IntroSeenRequest], Callable[[str, str, str, int], CommandOutcome]]] = {
        "round.intro.seen": (IntroSeenRequest, store.acknowledge_intro),
        "round.play_again": (PlayAgainRequest, store.play_again),
        "round.submit": (IntroSeenRequest, store.submit_drawing),
    }
    drawing_actions = {"drawing.add": "add", "drawing.undo": "undo", "drawing.clear": "clear"}

    async def handle_socket_message(connection: Connection, incoming: dict[str, Any]) -> None:
        if incoming.get("protocol_version") != 1:
            raise GameError("payload_invalid", "Unsupported socket message.", 422)
        message_type = incoming.get("type")
        if message_type == "state.request":
            await hub.send_snapshot(connection)
            return
        payload = incoming.get("payload")
        if message_type in drawing_actions:
            round_id = incoming.get("round_id")
            stroke = payload.get("stroke") if isinstance(payload, dict) else None
            if not isinstance(round_id, str):
                raise GameError("payload_invalid", "That message could not be read.", 422)
            members = await run_in_threadpool(
                store.edit_drawing, connection.token, round_id, drawing_actions[message_type], stroke
            )
            await hub.push_snapshots(members)
            return
        if message_type in ("voice.signal", "voice.talking"):
            # Peer-to-peer voice setup and talking indicators are relayed to the teammate, never stored.
            members = await run_in_threadpool(store.pair_member_ids, connection.player_id)
            await hub.relay(
                (m for m in members if m != connection.player_id),
                {"protocol_version": 1, "type": message_type, "payload": payload if isinstance(payload, dict) else {}},
            )
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
        if message_type == "round.submit" and outcome.notify_player_ids:
            spawn(check_round(command.round_id))

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
