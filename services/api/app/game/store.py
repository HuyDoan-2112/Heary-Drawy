"""Postgres-backed authority for guest sessions, pairing, and round transitions.

Every mutation is one transaction. Rooms are locked while admitting guests and
rounds are locked while applying commands, so concurrent requests serialize on
the record they would otherwise race for.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import unicodedata
from collections.abc import Callable, Collection, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from services.api.app.contracts.schemas import (
    ConnectionStatus,
    DrawingSnapshot,
    PendingRoomSnapshot,
    PendingRoomSummary,
    PlayerSummary,
    ReadyState,
    Role,
    RoleFilteredSnapshot,
    RoomSummary,
    RoundPhase,
    RoundSummary,
    VoiceState,
)
from services.api.app.db import connect

ALLOWED_AVATARS = {"sky", "mint", "grape", "berry", "pepper", "lemon", "mango", "plum", "coco", "kiwi"}
SESSION_TTL = timedelta(hours=12)

# The only legal phase moves. Later features add the triggers for the middle steps;
# every transition goes through GameStore._advance so this table is the single guard.
ALLOWED_TRANSITIONS: dict[RoundPhase, RoundPhase] = {
    RoundPhase.role_intro: RoundPhase.collaborating,
    RoundPhase.collaborating: RoundPhase.finalizing,
    RoundPhase.finalizing: RoundPhase.feedback,
    RoundPhase.feedback: RoundPhase.exploring,
    RoundPhase.exploring: RoundPhase.finished,
}


# Phases that wait for both children to acknowledge; the table name is a constant, never user input.
READINESS_TABLES: dict[RoundPhase, str] = {
    RoundPhase.role_intro: "intro_seen",
    RoundPhase.exploring: "play_again_intents",
}


class GameError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


@dataclass(frozen=True)
class AdmissionResult:
    room_id: str
    player_id: str
    guest_session_token: str
    expires_at: str
    admission_status: str
    # Players whose projection changed because of this admission (the new pair).
    notify_player_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommandOutcome:
    response: dict[str, Any]
    # Empty for a replayed command: nothing changed, so nobody needs a new snapshot.
    notify_player_ids: tuple[str, ...] = ()


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def normalize_nickname(nickname: str) -> str:
    normalized = unicodedata.normalize("NFKC", nickname).strip().casefold()
    return " ".join(normalized.split())


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def payload_digest(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode("utf-8")).hexdigest()


class GameStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    @contextmanager
    def _tx(self) -> Iterator[psycopg.Connection]:
        """One transaction on a short-lived connection; commits on success, rolls back on error."""
        with connect(self.database_url) as db:
            yield db

    # ------------------------------------------------------------------ rooms

    def provision_room(self, ttl: timedelta) -> str:
        """Server-side Room provisioning. No public API admits guests to the Room."""
        if ttl <= timedelta(0):
            raise ValueError("ttl must be positive")
        room_id = f"room_{uuid4().hex}"
        with self._tx() as db:
            db.execute(
                "insert into rooms(room_id, admission_status, expires_at) values (%s, 'open', %s)",
                (room_id, utc_now() + ttl),
            )
        return room_id

    def admit_guest(self, room_id: str, nickname: str, avatar_id: str) -> AdmissionResult:
        """Internal matching seam for already-authorized guests. Do not expose as a public route."""
        cleaned_nickname = nickname.strip()
        normalized_nickname = normalize_nickname(nickname)
        if not normalized_nickname:
            raise GameError("payload_invalid", "Choose a nickname to join.", 422)
        if avatar_id not in ALLOWED_AVATARS:
            raise GameError("payload_invalid", "Choose one of the available characters.", 422)
        now = utc_now()
        expires_at = now + SESSION_TTL
        token = secrets.token_urlsafe(32)
        player_id = f"player_{uuid4().hex}"

        with self._tx() as db:
            # The row lock serializes admissions and pairing within a Room.
            room = db.execute(
                "select room_id from rooms where room_id = %s and admission_status = 'open' "
                "and expires_at > now() for update",
                (room_id,),
            ).fetchone()
            if room is None:
                raise GameError("room_unavailable", "That room is not available.", 404)
            room_id = room["room_id"]
            try:
                with db.transaction():
                    db.execute(
                        "insert into players(player_id, room_id, nickname, normalized_nickname, avatar_id, "
                        "membership_status) values (%s, %s, %s, %s, %s, 'admitted')",
                        (player_id, room_id, cleaned_nickname, normalized_nickname, avatar_id),
                    )
            except UniqueViolation as exc:
                if exc.diag.constraint_name == "players_room_nickname_key":
                    raise GameError(
                        "nickname_taken",
                        "That nickname is already being used in this room. Try another one.",
                        409,
                        retryable=True,
                    ) from exc
                raise
            db.execute(
                "insert into guest_sessions(session_id, player_id, room_id, token_hash, expires_at) "
                "values (%s, %s, %s, %s, %s)",
                (f"session_{uuid4().hex}", player_id, room_id, token_hash(token), expires_at),
            )
            paired = self._pair_waiting_players(db, room_id)

        return AdmissionResult(
            room_id=room_id,
            player_id=player_id,
            guest_session_token=token,
            expires_at=iso(expires_at),
            admission_status="admitted",
            notify_player_ids=paired,
        )

    def _pair_waiting_players(self, db: psycopg.Connection, room_id: str) -> tuple[str, ...]:
        waiting = db.execute(
            """
            select p.player_id from players p
            left join pair_members m on m.player_id = p.player_id
            where p.room_id = %s and p.membership_status = 'admitted' and m.player_id is null
            order by p.created_at, p.player_id
            limit 2
            """,
            (room_id,),
        ).fetchall()
        if len(waiting) < 2:
            return ()

        first, second = waiting[0]["player_id"], waiting[1]["player_id"]
        speaker_id, drawer_id = (first, second) if secrets.randbelow(2) == 0 else (second, first)
        pair_id = f"pair_{uuid4().hex}"
        round_id = f"round_{uuid4().hex}"
        db.execute(
            "insert into pairs(pair_id, room_id, initial_speaker_player_id, initial_drawer_player_id, current_round_id) "
            "values (%s, %s, %s, %s, %s)",
            (pair_id, room_id, speaker_id, drawer_id, round_id),
        )
        db.execute(
            "insert into pair_members(player_id, pair_id, seat) values (%s, %s, 1), (%s, %s, 2)",
            (first, pair_id, second, pair_id),
        )
        self._insert_round(db, round_id, pair_id, 1, speaker_id, drawer_id)
        return (first, second)

    def _insert_round(
        self, db: psycopg.Connection, round_id: str, pair_id: str, index: int, speaker_id: str, drawer_id: str
    ) -> None:
        db.execute(
            "insert into rounds(round_id, pair_id, round_index, phase, phase_version, speaker_player_id, "
            "drawer_player_id, drawing_revision) values (%s, %s, %s, %s, 1, %s, %s, 0)",
            (round_id, pair_id, index, RoundPhase.role_intro.value, speaker_id, drawer_id),
        )

    # --------------------------------------------------------------- sessions

    def authenticate(self, token: str, room_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        with self._tx() as db:
            session = db.execute(
                """
                select s.* from guest_sessions s join rooms r on r.room_id = s.room_id
                where s.token_hash = %s and s.revoked_at is null and s.expires_at > now()
                  and r.expires_at > now() and r.admission_status = 'open'
                """,
                (token_hash(token),),
            ).fetchone()
            if session is None:
                raise GameError("session_invalid", "Join again to continue.", 401)
            if room_id is not None and session["room_id"] != room_id:
                raise GameError("not_authorized", "That room is not available for this session.", 403)
            player = db.execute(
                "select * from players where player_id = %s and membership_status = 'admitted'",
                (session["player_id"],),
            ).fetchone()
            if player is None:
                raise GameError("session_invalid", "Join again to continue.", 401)
            return session, player

    def pair_member_ids(self, player_id: str) -> tuple[str, ...]:
        """Both members of the player's pair, or an empty tuple while waiting."""
        with self._tx() as db:
            rows = db.execute(
                "select m.player_id from pair_members m where m.pair_id = "
                "(select pair_id from pair_members where player_id = %s) order by m.seat",
                (player_id,),
            ).fetchall()
        return tuple(row["player_id"] for row in rows)

    # -------------------------------------------------------------- snapshots

    def get_snapshot(
        self, token: str, room_id: str, connected_player_ids: Collection[str] = ()
    ) -> RoleFilteredSnapshot | PendingRoomSnapshot:
        session, player = self.authenticate(token, room_id)
        with self._tx() as db:
            pair = db.execute(
                "select p.* from pairs p join pair_members m on m.pair_id = p.pair_id where m.player_id = %s",
                (player["player_id"],),
            ).fetchone()
            if pair is None:
                return PendingRoomSnapshot(
                    session_player_id=player["player_id"],
                    admission_status="waiting_for_teammate",
                    room=PendingRoomSummary(room_id=room_id, participant=self._player_summary(player, True)),
                )
            round_row = db.execute("select * from rounds where round_id = %s", (pair["current_round_id"],)).fetchone()
            teammate = db.execute(
                "select p.* from players p join pair_members m on m.player_id = p.player_id "
                "where m.pair_id = %s and m.player_id <> %s",
                (pair["pair_id"], player["player_id"]),
            ).fetchone()
            ready_ids: set[str] | None = None
            ready_table = READINESS_TABLES.get(RoundPhase(round_row["phase"]))
            if ready_table:
                ready_ids = {
                    row["player_id"]
                    for row in db.execute(f"select player_id from {ready_table} where round_id = %s", (round_row["round_id"],))
                }

        phase = RoundPhase(round_row["phase"])
        role = Role.speaker if round_row["speaker_player_id"] == player["player_id"] else Role.drawer
        return RoleFilteredSnapshot(
            snapshot_id=f"snapshot_{uuid4().hex}",
            session_player_id=session["player_id"],
            room=RoomSummary(
                room_id=room_id,
                pair_id=pair["pair_id"],
                participant=self._player_summary(player, True),
                teammate=self._player_summary(teammate, teammate["player_id"] in connected_player_ids),
            ),
            round=RoundSummary(
                round_id=round_row["round_id"],
                role=role,
                phase=phase,
                phase_version=round_row["phase_version"],
                permissions=self._permissions_for(role, phase),
            ),
            drawing=DrawingSnapshot(round_id=round_row["round_id"], revision=round_row["drawing_revision"], strokes=[]),
            voice=VoiceState(provider_available=False),
            ready=(
                None
                if ready_ids is None
                else ReadyState(
                    self_ready=player["player_id"] in ready_ids, teammate_ready=teammate["player_id"] in ready_ids
                )
            ),
        )

    # --------------------------------------------------------------- commands

    def acknowledge_intro(self, token: str, round_id: str, command_id: str, expected_version: int) -> CommandOutcome:
        return self._round_command(
            token, "intro_seen", round_id, command_id, expected_version, RoundPhase.role_intro, self._apply_intro_seen
        )

    def play_again(self, token: str, round_id: str, command_id: str, expected_version: int) -> CommandOutcome:
        return self._round_command(
            token, "play_again", round_id, command_id, expected_version, RoundPhase.exploring, self._apply_play_again
        )

    def _round_command(
        self,
        token: str,
        kind: str,
        round_id: str,
        command_id: str,
        expected_version: int,
        required_phase: RoundPhase,
        apply: Callable[[psycopg.Connection, dict[str, Any], dict[str, Any]], dict[str, Any]],
    ) -> CommandOutcome:
        session, player = self.authenticate(token)
        digest = payload_digest(kind, round_id, expected_version)
        with self._tx() as db:
            # Locking the round serializes both children's commands for it, including
            # a double-sent command, so replay detection below cannot race.
            row = db.execute(
                """
                select r.*, p.room_id, p.current_round_id
                from rounds r
                join pairs p on p.pair_id = r.pair_id
                join pair_members m on m.pair_id = p.pair_id
                where r.round_id = %s and m.player_id = %s
                for update of r
                """,
                (round_id, player["player_id"]),
            ).fetchone()
            if row is None or row["room_id"] != session["room_id"]:
                raise GameError("not_authorized", "That round is not available.", 403)
            prior = db.execute(
                "select payload_hash, response from commands where player_id = %s and command_id = %s",
                (player["player_id"], command_id),
            ).fetchone()
            if prior:
                if prior["payload_hash"] != digest:
                    raise GameError("payload_invalid", "Command ID was already used with different data.", 409)
                return CommandOutcome(prior["response"])
            if row["round_id"] != row["current_round_id"]:
                raise GameError("stale_round", "The round has changed. Refresh to continue.", 409, True)
            if row["phase_version"] != expected_version:
                raise GameError("stale_round", "The round has changed. Refresh to continue.", 409, True)
            if row["phase"] != required_phase.value:
                raise GameError("wrong_phase", "This round is not ready for that yet.", 409)
            response = apply(db, row, player)
            db.execute(
                "insert into commands(player_id, command_id, payload_hash, response) values (%s, %s, %s, %s)",
                (player["player_id"], command_id, digest, Jsonb(response)),
            )
            members = db.execute(
                "select player_id from pair_members where pair_id = %s order by seat", (row["pair_id"],)
            ).fetchall()
            return CommandOutcome(response, tuple(m["player_id"] for m in members))

    def _apply_intro_seen(self, db: psycopg.Connection, row: dict[str, Any], player: dict[str, Any]) -> dict[str, Any]:
        round_id = row["round_id"]
        db.execute(
            "insert into intro_seen(round_id, player_id) values (%s, %s) on conflict do nothing",
            (round_id, player["player_id"]),
        )
        seen = db.execute("select count(*) as n from intro_seen where round_id = %s", (round_id,)).fetchone()["n"]
        if seen < 2:
            return {"round_id": round_id, "phase": RoundPhase.role_intro.value, "phase_version": row["phase_version"]}
        version = self._advance(db, row, RoundPhase.collaborating)
        return {"round_id": round_id, "phase": RoundPhase.collaborating.value, "phase_version": version}

    def _apply_play_again(self, db: psycopg.Connection, row: dict[str, Any], player: dict[str, Any]) -> dict[str, Any]:
        round_id = row["round_id"]
        db.execute(
            "insert into play_again_intents(round_id, player_id) values (%s, %s) on conflict do nothing",
            (round_id, player["player_id"]),
        )
        ready = db.execute("select count(*) as n from play_again_intents where round_id = %s", (round_id,)).fetchone()["n"]
        if ready < 2:
            return {"round_id": round_id, "status": "waiting_for_teammate", "next_round_id": None}
        self._advance(db, row, RoundPhase.finished)
        next_round_id = f"round_{uuid4().hex}"
        # Roles swap each Round. The new Round has its own identity, so late messages for the
        # old one cannot mutate it.
        self._insert_round(
            db, next_round_id, row["pair_id"], row["round_index"] + 1, row["drawer_player_id"], row["speaker_player_id"]
        )
        db.execute("update pairs set current_round_id = %s where pair_id = %s", (next_round_id, row["pair_id"]))
        return {"round_id": round_id, "status": "started", "next_round_id": next_round_id}

    def _advance(self, db: psycopg.Connection, row: dict[str, Any], to_phase: RoundPhase) -> int:
        """The only place a round changes phase; refuses anything not in ALLOWED_TRANSITIONS."""
        from_phase = RoundPhase(row["phase"])
        if ALLOWED_TRANSITIONS.get(from_phase) != to_phase:
            raise GameError("wrong_phase", "This round cannot move there yet.", 409)
        moved = db.execute(
            "update rounds set phase = %s, phase_version = phase_version + 1 "
            "where round_id = %s and phase = %s and phase_version = %s returning phase_version",
            (to_phase.value, row["round_id"], from_phase.value, row["phase_version"]),
        ).fetchone()
        if moved is None:
            raise GameError("stale_round", "The round has changed. Refresh to continue.", 409, True)
        return moved["phase_version"]

    # ---------------------------------------------------------------- helpers

    def _player_summary(self, player: dict[str, Any], connected: bool) -> PlayerSummary:
        return PlayerSummary(
            player_id=player["player_id"],
            nickname=player["nickname"],
            avatar_id=player["avatar_id"],
            connection_status=ConnectionStatus.connected if connected else ConnectionStatus.disconnected,
        )

    def _permissions_for(self, role: Role, phase: RoundPhase) -> list[str]:
        if phase == RoundPhase.role_intro:
            return ["view_drawing", "role_intro"]
        if phase == RoundPhase.collaborating:
            return ["view_drawing", "hold_to_talk"] if role == Role.speaker else ["edit_drawing", "hold_to_talk"]
        if phase == RoundPhase.exploring:
            return ["view_drawing", "play_again"]
        return ["view_drawing"]

    def error_payload(self, error: GameError) -> dict[str, Any]:
        return {"error": {"code": error.code, "message": error.message, "retryable": error.retryable}}
