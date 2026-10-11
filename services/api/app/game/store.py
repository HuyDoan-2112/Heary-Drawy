from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import threading
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from services.api.app.contracts.schemas import (
    ConnectionStatus,
    DrawingSnapshot,
    PlayerSummary,
    Role,
    RoleFilteredSnapshot,
    RoomSummary,
    RoundPhase,
    RoundSummary,
    VoiceState,
)

DEMO_SHAPE_CODE = ["circle", "triangle", "square"]
ALLOWED_AVATARS = {"sky", "mint", "grape", "berry", "pepper", "lemon", "mango", "plum", "coco", "kiwi"}
SESSION_TTL = timedelta(hours=12)


class GameError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


@dataclass(frozen=True)
class JoinResult:
    room_id: str
    player_id: str
    guest_session_token: str
    expires_at: str
    admission_status: str


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def normalize_nickname(nickname: str) -> str:
    normalized = unicodedata.normalize("NFKC", nickname).strip().casefold()
    return " ".join(normalized.split())


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class GameStore:
    def __init__(self, db_path: str | Path, *, fixture_room: bool = False) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize(fixture_room)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self, fixture_room: bool) -> None:
        with self._lock, self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS rooms (
                  room_id TEXT PRIMARY KEY,
                  shape_code TEXT NOT NULL UNIQUE,
                  admission_status TEXT NOT NULL,
                  expires_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS players (
                  player_id TEXT PRIMARY KEY,
                  room_id TEXT NOT NULL REFERENCES rooms(room_id),
                  nickname TEXT NOT NULL,
                  normalized_nickname TEXT NOT NULL,
                  avatar_id TEXT NOT NULL,
                  membership_status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  UNIQUE(room_id, normalized_nickname)
                );

                CREATE TABLE IF NOT EXISTS guest_sessions (
                  session_id TEXT PRIMARY KEY,
                  player_id TEXT NOT NULL REFERENCES players(player_id),
                  room_id TEXT NOT NULL REFERENCES rooms(room_id),
                  token_hash TEXT NOT NULL UNIQUE,
                  expires_at TEXT NOT NULL,
                  revoked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS pairs (
                  pair_id TEXT PRIMARY KEY,
                  room_id TEXT NOT NULL REFERENCES rooms(room_id),
                  player_one_id TEXT NOT NULL REFERENCES players(player_id),
                  player_two_id TEXT NOT NULL REFERENCES players(player_id),
                  speaker_player_id TEXT NOT NULL REFERENCES players(player_id),
                  drawer_player_id TEXT NOT NULL REFERENCES players(player_id),
                  current_round_id TEXT,
                  created_at TEXT NOT NULL,
                  UNIQUE(room_id, player_one_id),
                  UNIQUE(room_id, player_two_id)
                );

                CREATE TABLE IF NOT EXISTS rounds (
                  round_id TEXT PRIMARY KEY,
                  pair_id TEXT NOT NULL REFERENCES pairs(pair_id),
                  round_index INTEGER NOT NULL,
                  phase TEXT NOT NULL,
                  phase_version INTEGER NOT NULL,
                  speaker_player_id TEXT NOT NULL REFERENCES players(player_id),
                  drawer_player_id TEXT NOT NULL REFERENCES players(player_id),
                  drawing_revision INTEGER NOT NULL,
                  created_at TEXT NOT NULL,
                  UNIQUE(pair_id, round_index)
                );
                """
            )
            if fixture_room:
                self._ensure_demo_room(db)

    def _ensure_demo_room(self, db: sqlite3.Connection) -> None:
        shape_code = json.dumps(DEMO_SHAPE_CODE)
        exists = db.execute("SELECT room_id FROM rooms WHERE shape_code = ?", (shape_code,)).fetchone()
        if exists:
            return
        db.execute(
            "INSERT INTO rooms(room_id, shape_code, admission_status, expires_at) VALUES (?, ?, ?, ?)",
            (f"room_{uuid4().hex}", shape_code, "open", iso(utc_now() + timedelta(days=7))),
        )

    def join_room(self, shape_code: list[str], nickname: str, avatar_id: str) -> JoinResult:
        cleaned_nickname = nickname.strip()
        normalized_nickname = normalize_nickname(nickname)
        if not normalized_nickname:
            raise GameError("payload_invalid", "Choose a nickname to join.", 422)
        if avatar_id not in ALLOWED_AVATARS:
            raise GameError("payload_invalid", "Choose one of the available characters.", 422)
        shape_json = json.dumps(shape_code)
        now = utc_now()
        expires_at = now + SESSION_TTL
        token = secrets.token_urlsafe(32)

        with self._lock, self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                room = db.execute(
                    "SELECT * FROM rooms WHERE shape_code = ? AND admission_status = ?",
                    (shape_json, "open"),
                ).fetchone()
                if room is None or room["expires_at"] <= iso(now):
                    raise GameError("room_unavailable", "That room is not available.", 404)

                player_id = f"player_{uuid4().hex}"
                db.execute(
                    """
                    INSERT INTO players(player_id, room_id, nickname, normalized_nickname, avatar_id, membership_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (player_id, room["room_id"], cleaned_nickname, normalized_nickname, avatar_id, "admitted", iso(now)),
                )
                db.execute(
                    """
                    INSERT INTO guest_sessions(session_id, player_id, room_id, token_hash, expires_at, revoked_at)
                    VALUES (?, ?, ?, ?, ?, NULL)
                    """,
                    (f"session_{uuid4().hex}", player_id, room["room_id"], token_hash(token), iso(expires_at)),
                )
                self._pair_waiting_players(db, room["room_id"], now)
                db.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                db.execute("ROLLBACK")
                if "players.room_id, players.normalized_nickname" in str(exc):
                    raise GameError(
                        "nickname_taken",
                        "That nickname is already being used in this room. Try another one.",
                        409,
                        retryable=True,
                    ) from exc
                raise
            except Exception:
                db.execute("ROLLBACK")
                raise

        return JoinResult(
            room_id=room["room_id"],
            player_id=player_id,
            guest_session_token=token,
            expires_at=iso(expires_at),
            admission_status="admitted",
        )

    def _pair_waiting_players(self, db: sqlite3.Connection, room_id: str, now: datetime) -> None:
        waiting = db.execute(
            """
            SELECT p.* FROM players p
            WHERE p.room_id = ?
              AND p.membership_status = 'admitted'
              AND p.player_id NOT IN (SELECT player_one_id FROM pairs WHERE room_id = ?)
              AND p.player_id NOT IN (SELECT player_two_id FROM pairs WHERE room_id = ?)
            ORDER BY p.created_at ASC
            """,
            (room_id, room_id, room_id),
        ).fetchall()
        if len(waiting) < 2:
            return

        first, second = waiting[0], waiting[1]
        if secrets.randbelow(2) == 0:
            speaker_id, drawer_id = first["player_id"], second["player_id"]
        else:
            speaker_id, drawer_id = second["player_id"], first["player_id"]
        pair_id = f"pair_{uuid4().hex}"
        round_id = f"round_{uuid4().hex}"
        db.execute(
            """
            INSERT INTO pairs(pair_id, room_id, player_one_id, player_two_id, speaker_player_id, drawer_player_id, current_round_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pair_id, room_id, first["player_id"], second["player_id"], speaker_id, drawer_id, round_id, iso(now)),
        )
        db.execute(
            """
            INSERT INTO rounds(round_id, pair_id, round_index, phase, phase_version, speaker_player_id, drawer_player_id, drawing_revision, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (round_id, pair_id, 1, RoundPhase.role_intro.value, 1, speaker_id, drawer_id, 0, iso(now)),
        )

    def authenticate(self, token: str, room_id: str | None = None) -> tuple[sqlite3.Row, sqlite3.Row]:
        hashed = token_hash(token)
        with self._lock, self._connect() as db:
            session = db.execute(
                """
                SELECT s.* FROM guest_sessions s JOIN rooms r ON r.room_id = s.room_id
                WHERE s.token_hash = ? AND s.revoked_at IS NULL AND s.expires_at > ?
                  AND r.expires_at > ? AND r.admission_status = 'open'
                """,
                (hashed, iso(utc_now()), iso(utc_now())),
            ).fetchone()
            if session is None:
                raise GameError("session_invalid", "Join again to continue.", 401)
            if room_id is not None and session["room_id"] != room_id:
                raise GameError("not_authorized", "That room is not available for this session.", 403)
            player = db.execute("SELECT * FROM players WHERE player_id = ?", (session["player_id"],)).fetchone()
            if player is None:
                raise GameError("session_invalid", "Join again to continue.", 401)
            return session, player

    def get_snapshot(self, token: str, room_id: str) -> RoleFilteredSnapshot | dict[str, Any]:
        session, player = self.authenticate(token, room_id)
        with self._lock, self._connect() as db:
            pair = db.execute(
                """
                SELECT * FROM pairs
                WHERE room_id = ? AND (player_one_id = ? OR player_two_id = ?)
                """,
                (room_id, player["player_id"], player["player_id"]),
            ).fetchone()
            if pair is None:
                return {
                    "session_player_id": player["player_id"],
                    "admission_status": "waiting_for_teammate",
                    "room": {"room_id": room_id, "participant": self._player_summary(player).model_dump(mode="json")},
                }
            round_row = db.execute("SELECT * FROM rounds WHERE round_id = ?", (pair["current_round_id"],)).fetchone()
            teammate_id = pair["player_two_id"] if pair["player_one_id"] == player["player_id"] else pair["player_one_id"]
            teammate = db.execute("SELECT * FROM players WHERE player_id = ?", (teammate_id,)).fetchone()

        role = Role.speaker if round_row["speaker_player_id"] == player["player_id"] else Role.drawer
        permissions = self._permissions_for(role, RoundPhase(round_row["phase"]))
        return RoleFilteredSnapshot(
            snapshot_id=f"snapshot_{uuid4().hex}",
            session_player_id=session["player_id"],
            room=RoomSummary(
                room_id=room_id,
                pair_id=pair["pair_id"],
                participant=self._player_summary(player),
                teammate=self._player_summary(teammate),
            ),
            round=RoundSummary(
                round_id=round_row["round_id"],
                role=role,
                phase=RoundPhase(round_row["phase"]),
                phase_version=round_row["phase_version"],
                permissions=permissions,
            ),
            drawing=DrawingSnapshot(round_id=round_row["round_id"], revision=round_row["drawing_revision"], strokes=[]),
            voice=VoiceState(provider_available=False),
        )

    def _player_summary(self, player: sqlite3.Row) -> PlayerSummary:
        return PlayerSummary(
            player_id=player["player_id"],
            nickname=player["nickname"],
            avatar_id=player["avatar_id"],
            connection_status=ConnectionStatus.connected,
        )

    def _permissions_for(self, role: Role, phase: RoundPhase) -> list[str]:
        if phase == RoundPhase.role_intro:
            return ["view_drawing", "role_intro"] if role == Role.speaker else ["edit_drawing", "role_intro"]
        if phase == RoundPhase.collaborating:
            return ["view_drawing", "hold_to_talk"] if role == Role.speaker else ["edit_drawing", "hold_to_talk"]
        return ["view_drawing"]

    def error_payload(self, error: GameError) -> dict[str, Any]:
        return {"error": {"code": error.code, "message": error.message, "retryable": error.retryable}}
