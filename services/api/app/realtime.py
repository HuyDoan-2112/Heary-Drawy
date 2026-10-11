"""In-process registry of authenticated sockets, presence, and snapshot push.

State lives in this process only. That is correct for the single-instance demo
deployment; running several API instances would need a shared pub/sub layer, and
presence would then have to move out of process memory. The database remains the
authority: a push is always a freshly built, role-filtered snapshot.
"""

import asyncio
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import WebSocket
from starlette.concurrency import run_in_threadpool

from services.api.app.game.store import GameError, GameStore

logger = logging.getLogger("heary_drawy.realtime")


@dataclass(eq=False)
class Connection:
    websocket: WebSocket
    token: str
    room_id: str
    player_id: str
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def send(self, message: dict) -> None:
        async with self.send_lock:
            await self.websocket.send_json(message)


class ConnectionHub:
    def __init__(self, store: GameStore) -> None:
        self._store = store
        self._by_player: dict[str, set[Connection]] = {}

    def connected_player_ids(self) -> frozenset[str]:
        return frozenset(self._by_player)

    def register(self, connection: Connection) -> None:
        self._by_player.setdefault(connection.player_id, set()).add(connection)

    def unregister(self, connection: Connection) -> None:
        connections = self._by_player.get(connection.player_id)
        if connections is None:
            return
        connections.discard(connection)
        if not connections:
            del self._by_player[connection.player_id]

    async def send_snapshot(self, connection: Connection) -> None:
        snapshot = await run_in_threadpool(
            self._store.get_snapshot, connection.token, connection.room_id, self.connected_player_ids()
        )
        payload = snapshot.model_dump(mode="json", exclude_none=True)
        await connection.send(
            {
                "protocol_version": 1,
                "type": "state.snapshot",
                "event_id": payload.get("snapshot_id", f"event_{uuid4().hex}"),
                "round_id": payload.get("round", {}).get("round_id"),
                "payload": payload,
            }
        )

    async def push_snapshots(self, player_ids: Iterable[str]) -> None:
        """Send each connected player a fresh snapshot. One bad socket never blocks the others."""
        targets = [c for player_id in player_ids for c in tuple(self._by_player.get(player_id, ()))]
        results = await asyncio.gather(*(self.send_snapshot(c) for c in targets), return_exceptions=True)
        for connection, result in zip(targets, results, strict=True):
            if isinstance(result, GameError):
                logger.info("snapshot push skipped: %s", result.code)
            elif isinstance(result, Exception):
                logger.info("snapshot push failed: %s", type(result).__name__)
                self.unregister(connection)
