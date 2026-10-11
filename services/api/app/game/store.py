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
    FeedbackSnapshot,
    ObjectAccess,
    PendingRoomSnapshot,
    PendingRoomSummary,
    PlayerSummary,
    ReadyState,
    ResultStatus,
    Role,
    RoleFeedback,
    RoleFilteredSnapshot,
    RoomSummary,
    RoundPhase,
    RoundSummary,
    SharedResult,
    Stroke,
    VoiceState,
)
from services.api.app.db import connect
from services.api.app.game.objects import BY_ID, CATALOG

ALLOWED_AVATARS = {"sky", "mint", "grape", "berry", "pepper", "lemon", "mango", "plum", "coco", "kiwi"}

# Product decisions (docs/product.md): sessions and device unlocks last 24 hours, Room data is
# deleted 7 days after the Room closes or expires, and a match is 3 rounds.
SESSION_TTL = timedelta(hours=24)
DEVICE_ENROLLMENT_TTL = timedelta(hours=24)
RETENTION_AFTER_ROOM_END = timedelta(days=7)
TOTAL_ROUNDS = 3

# Room passcodes are 12 random Crockford base32 characters (60 bits), shown as XXXX-XXXX-XXXX.
# That is far beyond online guessing, so a fast hash is enough to keep them out of the database.
PASSCODE_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
PASSCODE_LENGTH = 12

# The only legal phase moves. Later features add the triggers for the middle steps;
# every transition goes through GameStore._advance so this table is the single guard.
ALLOWED_TRANSITIONS: dict[RoundPhase, RoundPhase] = {
    RoundPhase.role_intro: RoundPhase.collaborating,
    RoundPhase.collaborating: RoundPhase.finalizing,
    RoundPhase.finalizing: RoundPhase.feedback,
    RoundPhase.feedback: RoundPhase.exploring,
    RoundPhase.exploring: RoundPhase.finished,
}


# The secret picture is revealed to the Drawer from feedback onwards.
REVEALED_PHASES = {RoundPhase.feedback, RoundPhase.exploring, RoundPhase.finished}

# AI scoring is not part of the demo, so every round gets the friendly neutral result.
NEUTRAL_RESULT_LINES = (
    "Drawy had trouble checking this one, but you still finished the round together!",
    "Let's look at the picture and try another one.",
)

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
class ProvisionedRoom:
    room_id: str
    # Shown once to the operator; only its hash is stored.
    passcode: str


@dataclass(frozen=True)
class DeviceEnrollment:
    room_id: str
    device_token: str
    expires_at: str


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


def new_passcode() -> str:
    raw = "".join(secrets.choice(PASSCODE_ALPHABET) for _ in range(PASSCODE_LENGTH))
    return "-".join(raw[i : i + 4] for i in range(0, PASSCODE_LENGTH, 4))


def normalize_passcode(passcode: str) -> str:
    """Forgive spacing, dashes, case, and the Crockford look-alikes O/0 and I/L/1."""
    cleaned = "".join(passcode.split()).replace("-", "").upper()
    return cleaned.translate(str.maketrans({"O": "0", "I": "1", "L": "1"}))


def default_nickname(avatar_id: str) -> str:
    return avatar_id.capitalize()


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

    def provision_room(self, ttl: timedelta) -> ProvisionedRoom:
        """Server-side Room provisioning. The passcode lets a grown-up unlock devices for it."""
        if ttl <= timedelta(0):
            raise ValueError("ttl must be positive")
        room_id = f"room_{uuid4().hex}"
        passcode = new_passcode()
        with self._tx() as db:
            db.execute(
                "insert into rooms(room_id, admission_status, expires_at, host_passcode_hash) values (%s, 'open', %s, %s)",
                (room_id, utc_now() + ttl, token_hash(normalize_passcode(passcode))),
            )
        return ProvisionedRoom(room_id=room_id, passcode=passcode)

    def close_room(self, room_id: str) -> tuple[str, ...]:
        """Stop the Room: no new admissions, and every session and device unlock stops working.

        Returns the players who were admitted, so connected sockets can be told.
        """
        with self._tx() as db:
            room = db.execute(
                "update rooms set admission_status = 'closed', closed_at = coalesce(closed_at, now()) "
                "where room_id = %s returning room_id",
                (room_id,),
            ).fetchone()
            if room is None:
                raise GameError("room_unavailable", "That room is not available.", 404)
            db.execute("update guest_sessions set revoked_at = now() where room_id = %s and revoked_at is null", (room_id,))
            db.execute(
                "update device_enrollments set revoked_at = now() where room_id = %s and revoked_at is null", (room_id,)
            )
            rows = db.execute(
                "select player_id from players where room_id = %s and membership_status = 'admitted'", (room_id,)
            ).fetchall()
        return tuple(row["player_id"] for row in rows)

    def delete_expired_rooms(self, retention: timedelta = RETENTION_AFTER_ROOM_END) -> int:
        """Delete every Room (and all of its data) that closed or expired more than `retention` ago."""
        with self._tx() as db:
            rooms = [
                row["room_id"]
                for row in db.execute(
                    "select room_id from rooms where least(closed_at, expires_at) < now() - %s "
                    "for update",
                    (retention,),
                ).fetchall()
            ]
            if not rooms:
                return 0
            pair_ids = "select pair_id from pairs where room_id = any(%(rooms)s)"
            round_ids = f"select round_id from rounds where pair_id in ({pair_ids})"
            player_ids = "select player_id from players where room_id = any(%(rooms)s)"
            for statement in (
                f"delete from commands where player_id in ({player_ids})",
                f"delete from intro_seen where round_id in ({round_ids})",
                f"delete from clips where round_id in ({round_ids})",
                f"delete from play_again_intents where round_id in ({round_ids})",
                "update pairs set current_round_id = null where room_id = any(%(rooms)s)",
                f"delete from rounds where pair_id in ({pair_ids})",
                f"delete from pair_members where pair_id in ({pair_ids})",
                "delete from pairs where room_id = any(%(rooms)s)",
                "delete from device_enrollments where room_id = any(%(rooms)s)",
                "delete from guest_sessions where room_id = any(%(rooms)s)",
                "delete from players where room_id = any(%(rooms)s)",
                "delete from rooms where room_id = any(%(rooms)s)",
            ):
                db.execute(statement, {"rooms": rooms})
        return len(rooms)

    # ------------------------------------------------------------- admission

    def enroll_device(self, passcode: str) -> DeviceEnrollment:
        """A grown-up's Room passcode unlocks this device. Errors never say whether a Room exists."""
        normalized = normalize_passcode(passcode)
        if len(normalized) != PASSCODE_LENGTH:
            raise GameError("passcode_invalid", "That passcode did not work. Check it and try again.", 401)
        token = secrets.token_urlsafe(32)
        with self._tx() as db:
            room = db.execute(
                "select room_id, expires_at from rooms where host_passcode_hash = %s "
                "and admission_status = 'open' and expires_at > now()",
                (token_hash(normalized),),
            ).fetchone()
            if room is None:
                raise GameError("passcode_invalid", "That passcode did not work. Check it and try again.", 401)
            expires_at = min(utc_now() + DEVICE_ENROLLMENT_TTL, room["expires_at"])
            db.execute(
                "insert into device_enrollments(device_id, room_id, token_hash, expires_at) values (%s, %s, %s, %s)",
                (f"device_{uuid4().hex}", room["room_id"], token_hash(token), expires_at),
            )
        return DeviceEnrollment(room_id=room["room_id"], device_token=token, expires_at=iso(expires_at))

    def _authenticate_device(self, db: psycopg.Connection, device_token: str, room_id: str) -> dict[str, Any]:
        device = db.execute(
            """
            select d.* from device_enrollments d join rooms r on r.room_id = d.room_id
            where d.token_hash = %s and d.revoked_at is null and d.expires_at > now()
              and r.expires_at > now() and r.admission_status = 'open'
            for update of d
            """,
            (token_hash(device_token),),
        ).fetchone()
        if device is None:
            raise GameError("device_not_enrolled", "Ask a grown-up to unlock this device again.", 401)
        if device["room_id"] != room_id:
            raise GameError("not_authorized", "That room is not available for this device.", 403)
        return device

    def lobby(self, device_token: str, room_id: str) -> list[str]:
        """Characters already taken in the Room, for the Picked badges. Nothing else is revealed."""
        with self._tx() as db:
            self._authenticate_device(db, device_token, room_id)
            rows = db.execute(
                "select avatar_id from players where room_id = %s and membership_status = 'admitted' order by avatar_id",
                (room_id,),
            ).fetchall()
        return [row["avatar_id"] for row in rows]

    def admit_with_device(self, device_token: str, room_id: str, nickname: str, avatar_id: str) -> AdmissionResult:
        """Admit the child on an unlocked device. Whoever played on this device before is released."""
        with self._tx() as db:
            device = self._authenticate_device(db, device_token, room_id)
            released: tuple[str, ...] = ()
            if device["current_player_id"]:
                released = self._release_player(db, device["current_player_id"])
            result = self._admit(db, room_id, nickname.strip() or default_nickname(avatar_id), avatar_id)
            db.execute(
                "update device_enrollments set current_player_id = %s where device_id = %s",
                (result.player_id, device["device_id"]),
            )
        return AdmissionResult(
            room_id=result.room_id,
            player_id=result.player_id,
            guest_session_token=result.guest_session_token,
            expires_at=result.expires_at,
            admission_status=result.admission_status,
            notify_player_ids=result.notify_player_ids + released,
        )

    def leave(self, token: str) -> tuple[str, tuple[str, ...]]:
        """The child taps Done: their session ends and an unfinished match ends for their teammate.

        Returns the leaving player and the teammate to notify, if any.
        """
        session, player = self.authenticate(token)
        with self._tx() as db:
            db.execute("select room_id from rooms where room_id = %s for update", (session["room_id"],))
            return player["player_id"], self._release_player(db, player["player_id"])

    def admit_guest(self, room_id: str, nickname: str, avatar_id: str) -> AdmissionResult:
        """Internal seam for tests and operator tooling. Children are admitted through admit_with_device."""
        with self._tx() as db:
            return self._admit(db, room_id, nickname, avatar_id)

    def _admit(self, db: psycopg.Connection, room_id: str, nickname: str, avatar_id: str) -> AdmissionResult:
        cleaned_nickname = " ".join(nickname.split())
        normalized_nickname = normalize_nickname(nickname)
        if not normalized_nickname:
            raise GameError("payload_invalid", "Choose a nickname to join.", 422)
        if avatar_id not in ALLOWED_AVATARS:
            raise GameError("payload_invalid", "Choose one of the available characters.", 422)
        now = utc_now()
        token = secrets.token_urlsafe(32)
        player_id = f"player_{uuid4().hex}"

        # The row lock serializes admissions and pairing within a Room.
        room = db.execute(
            "select room_id, expires_at from rooms where room_id = %s and admission_status = 'open' "
            "and expires_at > now() for update",
            (room_id,),
        ).fetchone()
        if room is None:
            raise GameError("room_unavailable", "That room is not available.", 404)
        expires_at = min(now + SESSION_TTL, room["expires_at"])
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
            if exc.diag.constraint_name == "players_room_avatar_key":
                raise GameError(
                    "avatar_taken", "A friend already picked that character. Pick another one.", 409, retryable=True
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

    def _release_player(self, db: psycopg.Connection, player_id: str) -> tuple[str, ...]:
        """Remove a player from the Room and end their unfinished match. Returns the teammate, if any."""
        db.execute(
            "update players set membership_status = 'removed' where player_id = %s and membership_status = 'admitted'",
            (player_id,),
        )
        db.execute("update guest_sessions set revoked_at = now() where player_id = %s and revoked_at is null", (player_id,))
        db.execute("update device_enrollments set current_player_id = null where current_player_id = %s", (player_id,))
        pair = db.execute(
            """
            select p.pair_id, r.round_index, r.phase from pairs p
            join pair_members m on m.pair_id = p.pair_id
            join rounds r on r.round_id = p.current_round_id
            where m.player_id = %s and p.ended_at is null
            for update of p
            """,
            (player_id,),
        ).fetchone()
        if pair is None:
            return ()
        finished = pair["round_index"] >= TOTAL_ROUNDS and pair["phase"] in (
            RoundPhase.exploring.value,
            RoundPhase.finished.value,
        )
        db.execute(
            "update pairs set ended_at = now(), end_reason = %s where pair_id = %s",
            ("completed" if finished else "left", pair["pair_id"]),
        )
        teammates = db.execute(
            "select player_id from pair_members where pair_id = %s and player_id <> %s", (pair["pair_id"], player_id)
        ).fetchall()
        return tuple(row["player_id"] for row in teammates)

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
        used = {row["object_id"] for row in db.execute("select object_id from rounds where pair_id = %s", (pair_id,))}
        choices = [item.object_id for item in CATALOG if item.object_id not in used] or [item.object_id for item in CATALOG]
        db.execute(
            "insert into rounds(round_id, pair_id, round_index, phase, phase_version, speaker_player_id, "
            "drawer_player_id, drawing_revision, object_id) values (%s, %s, %s, %s, 1, %s, %s, 0, %s)",
            (round_id, pair_id, index, RoundPhase.role_intro.value, speaker_id, drawer_id, secrets.choice(choices)),
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
            if pair is None or pair["ended_at"] is not None:
                return PendingRoomSnapshot(
                    session_player_id=player["player_id"],
                    admission_status="waiting_for_teammate" if pair is None else "teammate_left",
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
                round_index=round_row["round_index"],
                total_rounds=TOTAL_ROUNDS,
                permissions=self._permissions_for(role, phase, round_row["round_index"]),
            ),
            drawing=DrawingSnapshot(
                round_id=round_row["round_id"], revision=round_row["drawing_revision"], strokes=round_row["strokes"]
            ),
            voice=VoiceState(provider_available=False),
            **self._reveal_fields(round_row, role, phase),
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
            # Locking the round and pair serializes both children's commands for it, including
            # a double-sent command and a teammate leaving, so the checks below cannot race.
            row = db.execute(
                """
                select r.*, p.room_id, p.current_round_id, p.ended_at
                from rounds r
                join pairs p on p.pair_id = r.pair_id
                join pair_members m on m.pair_id = p.pair_id
                where r.round_id = %s and m.player_id = %s
                for update of r, p
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
            if row["ended_at"] is not None:
                raise GameError("match_ended", "This game has ended.", 409)
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
        if row["round_index"] >= TOTAL_ROUNDS:
            raise GameError("match_complete", "That was the last round. Tap Done to finish.", 409)
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

    # ---------------------------------------------------------------- picture

    def _reveal_fields(self, round_row: dict[str, Any], role: Role, phase: RoundPhase) -> dict[str, Any]:
        """Picture access for the Speaker, and for both children once revealed; neutral result after."""
        fields: dict[str, Any] = {}
        item = BY_ID.get(round_row["object_id"] or "")
        if item and (role == Role.speaker or phase in REVEALED_PHASES):
            fields["object_access"] = ObjectAccess(
                object_id=item.object_id,
                display_name=item.display_name,
                image_url=f"/api/v1/rounds/{round_row['round_id']}/picture",
            )
        if phase in REVEALED_PHASES:
            result = round_row["result"]
            if result:
                # AI feedback (D2): each child gets their own lines; the stars are shared.
                lines = result[f"{role.value}_lines"]
                shared = SharedResult(status=ResultStatus.scored, stars=result["stars"], child_summary=lines[0])
            else:
                lines = list(NEUTRAL_RESULT_LINES)
                shared = SharedResult(status=ResultStatus.neutral_unscored, child_summary=lines[0])
            fields["feedback"] = FeedbackSnapshot(
                shared_result=shared,
                role_feedback=RoleFeedback(role=role, lines=lines),
                sticker_id=item.object_id if item else "star",
            )
        return fields

    def picture_svg(self, token: str, round_id: str) -> str:
        """The round's secret picture, only for its Speaker or after the reveal."""
        _session, player = self.authenticate(token)
        with self._tx() as db:
            row = db.execute(
                "select r.* from rounds r join pair_members m on m.pair_id = r.pair_id "
                "where r.round_id = %s and m.player_id = %s",
                (round_id, player["player_id"]),
            ).fetchone()
        if row is None or BY_ID.get(row["object_id"] or "") is None:
            raise GameError("not_authorized", "That picture is not available.", 403)
        is_speaker = row["speaker_player_id"] == player["player_id"]
        if not is_speaker and RoundPhase(row["phase"]) not in REVEALED_PHASES:
            raise GameError("not_authorized", "That picture is not available.", 403)
        return BY_ID[row["object_id"]].svg

    # ---------------------------------------------------------------- drawing

    def edit_drawing(self, token: str, round_id: str, action: str, stroke: dict[str, Any] | None = None) -> tuple[str, ...]:
        """Drawer-only stroke add, undo, or clear during collaboration. Returns the pair to notify."""
        _session, player = self.authenticate(token)
        with self._tx() as db:
            row = db.execute(
                """
                select r.*, p.current_round_id, p.ended_at from rounds r
                join pairs p on p.pair_id = r.pair_id
                where r.round_id = %s and r.drawer_player_id = %s
                for update of r
                """,
                (round_id, player["player_id"]),
            ).fetchone()
            if row is None:
                raise GameError("not_authorized", "Only the drawer can draw.", 403)
            if row["ended_at"] is not None or row["round_id"] != row["current_round_id"]:
                raise GameError("stale_round", "The round has changed. Refresh to continue.", 409, True)
            if row["phase"] != RoundPhase.collaborating.value:
                raise GameError("wrong_phase", "Drawing is not open right now.", 409)
            strokes: list[dict[str, Any]] = list(row["strokes"])
            if action == "add":
                try:
                    strokes.append(Stroke.model_validate(stroke).model_dump(mode="json", exclude_none=True))
                except ValueError as exc:
                    raise GameError("payload_invalid", "That stroke could not be read.", 422) from exc
                strokes = strokes[-256:]
            elif action == "undo":
                strokes = strokes[:-1]
            elif action == "clear":
                strokes = []
            else:
                raise GameError("payload_invalid", "Unknown drawing action.", 422)
            db.execute(
                "update rounds set strokes = %s, drawing_revision = drawing_revision + 1 where round_id = %s",
                (Jsonb(strokes), round_id),
            )
            members = db.execute("select player_id from pair_members where pair_id = %s", (row["pair_id"],)).fetchall()
        return tuple(member["player_id"] for member in members)

    def submit_drawing(self, token: str, round_id: str, command_id: str, expected_version: int) -> CommandOutcome:
        return self._round_command(
            token, "submit", round_id, command_id, expected_version, RoundPhase.collaborating, self._apply_submit
        )

    def _apply_submit(self, db: psycopg.Connection, row: dict[str, Any], player: dict[str, Any]) -> dict[str, Any]:
        if row["drawer_player_id"] != player["player_id"]:
            raise GameError("not_authorized", "Only the drawer can finish the drawing.", 403)
        # The round waits in finalizing ("Drawy is looking") until publish_result.
        version = self._advance(db, row, RoundPhase.finalizing)
        return {"round_id": row["round_id"], "phase": RoundPhase.finalizing.value, "phase_version": version}

    # ------------------------------------------------------- clips and feedback (D2)

    def add_clip(self, token: str, round_id: str) -> str:
        """Record a pending clip for a child of this round. Clips released just after Done still count."""
        _session, player = self.authenticate(token)
        with self._tx() as db:
            row = db.execute(
                "select r.* from rounds r join pair_members m on m.pair_id = r.pair_id "
                "where r.round_id = %s and m.player_id = %s",
                (round_id, player["player_id"]),
            ).fetchone()
            if row is None:
                raise GameError("not_authorized", "That round is not available.", 403)
            if row["phase"] not in (RoundPhase.collaborating.value, RoundPhase.finalizing.value):
                raise GameError("wrong_phase", "Talking is not open right now.", 409)
            role = Role.speaker if row["speaker_player_id"] == player["player_id"] else Role.drawer
            clip_id = f"clip_{uuid4().hex}"
            db.execute(
                "insert into clips(clip_id, round_id, player_id, role, status) values (%s, %s, %s, %s, 'pending')",
                (clip_id, round_id, player["player_id"], role.value),
            )
        return clip_id

    def finish_clip(self, clip_id: str, text: str | None) -> None:
        """Store the transcript, or mark the clip failed. The audio itself is never stored."""
        with self._tx() as db:
            db.execute(
                "update clips set status = %s, text = %s where clip_id = %s",
                ("done" if text else "failed", text or None, clip_id),
            )

    def pending_clips(self, round_id: str) -> int:
        with self._tx() as db:
            return db.execute(
                "select count(*) as n from clips where round_id = %s and status = 'pending'", (round_id,)
            ).fetchone()["n"]

    def feedback_input(self, round_id: str) -> dict[str, Any] | None:
        """What the AI needs for a round in finalizing: picture, strokes, and transcripts in order."""
        with self._tx() as db:
            row = db.execute("select phase, object_id, strokes from rounds where round_id = %s", (round_id,)).fetchone()
            if row is None or row["phase"] != RoundPhase.finalizing.value:
                return None
            clips = db.execute(
                "select role, text from clips where round_id = %s and status = 'done' order by created_at", (round_id,)
            ).fetchall()
        item = BY_ID.get(row["object_id"] or "")
        return {
            "name": item.display_name if item else "",
            "features": item.features if item else (),
            "strokes": row["strokes"],
            "transcript": [(clip["role"], clip["text"]) for clip in clips],
        }

    def rounds_in_finalizing(self) -> list[str]:
        with self._tx() as db:
            rows = db.execute("select round_id from rounds where phase = %s", (RoundPhase.finalizing.value,)).fetchall()
        return [row["round_id"] for row in rows]

    def publish_result(self, round_id: str, result: dict[str, Any] | None) -> tuple[str, ...]:
        """Save the AI result (None = neutral) and reveal. Returns the pair to notify; empty if already done."""
        with self._tx() as db:
            row = db.execute("select * from rounds where round_id = %s for update", (round_id,)).fetchone()
            if row is None or row["phase"] != RoundPhase.finalizing.value:
                return ()
            db.execute("update rounds set result = %s where round_id = %s", (Jsonb(result) if result else None, round_id))
            version = row["phase_version"]
            for to_phase in (RoundPhase.feedback, RoundPhase.exploring):
                version = self._advance(db, {**row, "phase_version": version}, to_phase)
                row = {**row, "phase": to_phase.value}
            members = db.execute("select player_id from pair_members where pair_id = %s order by seat", (row["pair_id"],))
            return tuple(member["player_id"] for member in members)

    # ---------------------------------------------------------------- helpers

    def _player_summary(self, player: dict[str, Any], connected: bool) -> PlayerSummary:
        return PlayerSummary(
            player_id=player["player_id"],
            nickname=player["nickname"],
            avatar_id=player["avatar_id"],
            connection_status=ConnectionStatus.connected if connected else ConnectionStatus.disconnected,
        )

    def _permissions_for(self, role: Role, phase: RoundPhase, round_index: int) -> list[str]:
        if phase == RoundPhase.role_intro:
            return ["view_drawing", "role_intro"]
        if phase == RoundPhase.collaborating:
            return ["view_drawing", "hold_to_talk"] if role == Role.speaker else ["edit_drawing", "hold_to_talk"]
        if phase == RoundPhase.exploring:
            return ["view_drawing", "play_again"] if round_index < TOTAL_ROUNDS else ["view_drawing"]
        return ["view_drawing"]

    def error_payload(self, error: GameError) -> dict[str, Any]:
        return {"error": {"code": error.code, "message": error.message, "retryable": error.retryable}}
