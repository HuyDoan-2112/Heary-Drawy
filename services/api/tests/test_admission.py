"""Grown-up passcode admission, leaving, match length, and retention (Feature 02 decisions)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import psycopg
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from services.api.app.game.store import PASSCODE_ALPHABET, TOTAL_ROUNDS
from services.api.tests.helpers import bearer, join, state_of, unlock, ws_authenticate

ORIGIN = {"origin": "http://testserver"}


def set_round(database_url: str, round_id: str, *, phase: str, index: int | None = None) -> None:
    """Later-feature phase trigger fixture (Features 03-08 own the real triggers)."""
    with psycopg.connect(database_url) as db:
        db.execute("update rounds set phase = %s, phase_version = phase_version + 1 where round_id = %s", (phase, round_id))
        if index is not None:
            db.execute("update rounds set round_index = %s where round_id = %s", (index, round_id))


def two_children(client: TestClient) -> tuple[dict, dict, dict, dict]:
    ipad, iphone = unlock(client), unlock(client)
    mango = join(client, ipad, "mango")
    kiwi = join(client, iphone, "kiwi")
    return ipad, iphone, mango, kiwi


def test_passcode_is_shown_once_and_only_its_hash_is_stored(client: TestClient, database_url: str) -> None:
    passcode = client.app.state.test_room_passcode
    groups = passcode.split("-")
    assert [len(group) for group in groups] == [4, 4, 4]
    assert all(char in PASSCODE_ALPHABET for char in "".join(groups))

    with psycopg.connect(database_url) as db:
        dump = str(db.execute("select * from rooms").fetchall())
    assert passcode not in dump
    assert passcode.replace("-", "") not in dump


def test_grown_up_passcode_unlocks_a_device_and_is_forgiving_to_type(client: TestClient) -> None:
    passcode = client.app.state.test_room_passcode
    typed = f"  {passcode.replace('-', ' ').lower()} "

    device = unlock(client, typed)

    assert device["room_id"] == client.app.state.test_room_id
    assert device["device_token"]


def test_wrong_passcode_says_nothing_about_rooms(client: TestClient) -> None:
    for attempt in ("ABCD-EFGH-JKMN", "short", "x" * 64):
        response = client.post("/api/v1/device-enrollments", json={"passcode": attempt})
        assert response.status_code == 401
        assert response.json()["error"] == {
            "code": "passcode_invalid",
            "message": "That passcode did not work. Check it and try again.",
            "retryable": False,
        }


def test_child_is_admitted_on_an_unlocked_device_with_an_optional_name(client: TestClient) -> None:
    ipad, iphone = unlock(client), unlock(client)

    mango = join(client, ipad, "mango")
    named = join(client, iphone, "kiwi", "  Sam   Lee ")

    mango_state, sam_state = state_of(client, mango), state_of(client, named)
    assert mango_state["room"]["participant"]["nickname"] == "Mango"
    assert sam_state["room"]["participant"]["nickname"] == "Sam Lee"
    assert mango_state["room"]["pair_id"] == sam_state["room"]["pair_id"]
    assert mango_state["round"]["round_index"] == 1
    assert mango_state["round"]["total_rounds"] == TOTAL_ROUNDS


def test_lobby_shows_taken_characters_and_duplicates_are_refused(client: TestClient) -> None:
    ipad, iphone = unlock(client), unlock(client)
    lobby_path = f"/api/v1/rooms/{ipad['room_id']}/lobby"
    assert client.get(lobby_path, headers=bearer(ipad["device_token"])).json() == {"taken_avatar_ids": []}

    join(client, ipad, "mango", "Mango")
    assert client.get(lobby_path, headers=bearer(iphone["device_token"])).json() == {"taken_avatar_ids": ["mango"]}

    same_character = client.post(
        f"/api/v1/rooms/{iphone['room_id']}/guests", json={"avatar_id": "mango", "nickname": "Other"},
        headers=bearer(iphone["device_token"]),
    )
    assert same_character.status_code == 409
    assert same_character.json()["error"]["code"] == "avatar_taken"
    same_name = client.post(
        f"/api/v1/rooms/{iphone['room_id']}/guests", json={"avatar_id": "kiwi", "nickname": " MANGO "},
        headers=bearer(iphone["device_token"]),
    )
    assert same_name.status_code == 409
    assert same_name.json()["error"]["code"] == "nickname_taken"


def test_concurrent_admissions_cannot_share_a_character(client: TestClient) -> None:
    devices = [unlock(client), unlock(client)]

    def attempt(job: tuple[dict, str]):
        device, name = job
        return client.post(
            f"/api/v1/rooms/{device['room_id']}/guests", json={"avatar_id": "plum", "nickname": name},
            headers=bearer(device["device_token"]),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(attempt, zip(devices, ["One", "Two"], strict=True)))

    assert sorted(response.status_code for response in responses) == [201, 409]


def test_device_and_guest_credentials_are_not_interchangeable(client: TestClient) -> None:
    ipad = unlock(client)
    mango = join(client, ipad, "mango")
    room_id = ipad["room_id"]

    as_guest = client.get(f"/api/v1/rooms/{room_id}/state", headers=bearer(ipad["device_token"]))
    assert as_guest.status_code == 401
    as_device = client.get(f"/api/v1/rooms/{room_id}/lobby", headers=bearer(mango["guest_session_token"]))
    assert as_device.status_code == 401
    assert as_device.json()["error"]["code"] == "device_not_enrolled"
    no_token = client.post(f"/api/v1/rooms/{room_id}/guests", json={"avatar_id": "kiwi"})
    assert no_token.status_code == 401
    wrong_room = client.get("/api/v1/rooms/room_guess/lobby", headers=bearer(ipad["device_token"]))
    assert wrong_room.status_code == 403
    assert "taken_avatar_ids" not in wrong_room.text


def test_pairing_is_pushed_to_the_waiting_child(client: TestClient) -> None:
    ipad, iphone = unlock(client), unlock(client)
    mango = join(client, ipad, "mango")

    with client.websocket_connect(f"/api/v1/rooms/{mango['room_id']}/socket", headers=ORIGIN) as ws:
        assert ws_authenticate(ws, mango)["payload"]["admission_status"] == "waiting_for_teammate"
        join(client, iphone, "kiwi")
        pushed = ws.receive_json()["payload"]

    assert pushed["round"]["phase"] == "role_intro"
    assert pushed["room"]["teammate"]["nickname"] == "Kiwi"


def test_done_ends_the_session_and_tells_the_teammate(client: TestClient) -> None:
    _ipad, _iphone, mango, kiwi = two_children(client)
    path = f"/api/v1/rooms/{mango['room_id']}/socket"
    round_summary = state_of(client, kiwi)["round"]

    with client.websocket_connect(path, headers=ORIGIN) as mango_ws, client.websocket_connect(path, headers=ORIGIN) as kiwi_ws:
        ws_authenticate(mango_ws, mango)
        ws_authenticate(kiwi_ws, kiwi)
        mango_ws.receive_json()  # Kiwi connected.

        response = client.post("/api/v1/session/leave", headers=bearer(mango["guest_session_token"]))
        assert response.json() == {"status": "left"}

        teammate_view = kiwi_ws.receive_json()["payload"]
        assert teammate_view["admission_status"] == "teammate_left"
        assert "teammate" not in teammate_view["room"]
        try:
            mango_ws.receive_json()
            raise AssertionError("the leaving child's socket stayed open")
        except WebSocketDisconnect:
            pass

    gone = client.get(f"/api/v1/rooms/{mango['room_id']}/state", headers=bearer(mango["guest_session_token"]))
    assert gone.status_code == 401
    late = client.post(
        f"/api/v1/rounds/{round_summary['round_id']}/intro-seen",
        json={"command_id": "late", "round_id": round_summary["round_id"], "expected_round_version": round_summary["phase_version"]},
        headers=bearer(kiwi["guest_session_token"]),
    )
    assert late.status_code == 409
    assert late.json()["error"]["code"] == "match_ended"


def test_rejoining_on_the_same_device_releases_the_previous_child(client: TestClient) -> None:
    ipad, _iphone, mango, kiwi = two_children(client)

    again = join(client, ipad, "mango")

    assert client.get(f"/api/v1/rooms/{mango['room_id']}/state", headers=bearer(mango["guest_session_token"])).status_code == 401
    assert state_of(client, again)["admission_status"] == "waiting_for_teammate"
    assert state_of(client, kiwi)["admission_status"] == "teammate_left"


def test_match_is_three_rounds(client: TestClient, database_url: str) -> None:
    _ipad, _iphone, mango, kiwi = two_children(client)
    round_id = state_of(client, mango)["round"]["round_id"]
    set_round(database_url, round_id, phase="exploring", index=TOTAL_ROUNDS)

    final = state_of(client, mango)["round"]
    assert final["round_index"] == final["total_rounds"] == TOTAL_ROUNDS
    assert "play_again" not in final["permissions"]
    response = client.post(
        f"/api/v1/rounds/{round_id}/play-again",
        json={"command_id": "again", "round_id": round_id, "expected_round_version": final["phase_version"]},
        headers=bearer(mango["guest_session_token"]),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "match_complete"

    client.post("/api/v1/session/leave", headers=bearer(mango["guest_session_token"]))
    assert state_of(client, kiwi)["admission_status"] == "teammate_left"
    with psycopg.connect(database_url) as db:
        assert db.execute("select end_reason from pairs").fetchone()[0] == "completed"


def test_closing_a_room_signs_everyone_out(client: TestClient) -> None:
    ipad, _iphone, mango, _kiwi = two_children(client)
    store = client.app.state.game_store

    signed_out = store.close_room(ipad["room_id"])

    assert len(signed_out) == 2
    assert client.get(f"/api/v1/rooms/{mango['room_id']}/state", headers=bearer(mango["guest_session_token"])).status_code == 401
    assert client.get(f"/api/v1/rooms/{ipad['room_id']}/lobby", headers=bearer(ipad["device_token"])).status_code == 401
    retry = client.post("/api/v1/device-enrollments", json={"passcode": client.app.state.test_room_passcode})
    assert retry.status_code == 401


def test_a_new_demo_room_signs_out_tabs_left_in_the_old_one(client: TestClient) -> None:
    ipad, _iphone, mango, _kiwi = two_children(client)
    store = client.app.state.game_store

    assert store.close_open_rooms() == 1
    store.provision_room(timedelta(hours=1))

    assert client.get(f"/api/v1/rooms/{mango['room_id']}/state", headers=bearer(mango["guest_session_token"])).status_code == 401
    assert client.get(f"/api/v1/rooms/{ipad['room_id']}/lobby", headers=bearer(ipad["device_token"])).status_code == 401
    assert store.close_open_rooms() == 1


def test_cleanup_deletes_rooms_seven_days_after_they_end(client: TestClient, database_url: str) -> None:
    store = client.app.state.game_store
    old_room = client.app.state.test_room_id
    two_children(client)
    recent = store.provision_room(timedelta(days=1))
    store.close_room(old_room)

    with psycopg.connect(database_url) as db:
        db.execute("update rooms set closed_at = now() - interval '6 days' where room_id = %s", (old_room,))
    assert store.delete_expired_rooms() == 0

    with psycopg.connect(database_url) as db:
        db.execute("update rooms set closed_at = now() - interval '8 days' where room_id = %s", (old_room,))
    assert store.delete_expired_rooms() == 1

    with psycopg.connect(database_url) as db:
        tables = ("players", "guest_sessions", "device_enrollments", "pairs", "pair_members", "rounds", "commands")
        counts = {table: db.execute(f"select count(*) from {table}").fetchone()[0] for table in tables}
        rooms = [row[0] for row in db.execute("select room_id from rooms").fetchall()]
    assert counts == dict.fromkeys(tables, 0)
    assert rooms == [recent.room_id]
