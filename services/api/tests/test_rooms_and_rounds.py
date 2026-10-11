from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from services.api.app.db import apply_migrations
from services.api.app.game.store import GameError
from services.api.app.main import create_app

ORIGIN = {"origin": "http://testserver"}


def admit(client: TestClient, nickname: str, avatar_id: str = "mango", room_id: str | None = None) -> httpx.Response:
    """Internal fixture for already-authorized guests, never a child-facing HTTP join."""
    store = client.app.state.game_store
    target = room_id or getattr(client.app.state, "test_room_id", "room_missing")
    try:
        result = store.admit_guest(target, nickname, avatar_id)
        return httpx.Response(201, json={
            "room_id": result.room_id, "player_id": result.player_id,
            "guest_session_token": result.guest_session_token, "expires_at": result.expires_at,
            "admission_status": result.admission_status,
        })
    except GameError as error:
        return httpx.Response(error.status_code, json=store.error_payload(error))


def auth_header(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['guest_session_token']}"}


def state_of(client: TestClient, session: dict) -> dict:
    response = client.get(f"/api/v1/rooms/{session['room_id']}/state", headers=auth_header(session))
    assert response.status_code == 200
    return response.json()


def paired(client: TestClient) -> tuple[dict, dict]:
    first = admit(client, "Mango", "mango").json()
    second = admit(client, "Kiwi", "kiwi").json()
    return first, second


def ws_authenticate(ws, session: dict) -> tuple[dict, dict]:
    ws.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": session["guest_session_token"]}})
    return ws.receive_json(), ws.receive_json()


def command_body(client: TestClient, session: dict, command_id: str) -> tuple[str, dict]:
    round_summary = state_of(client, session)["round"]
    return round_summary["round_id"], {
        "command_id": command_id,
        "round_id": round_summary["round_id"],
        "expected_round_version": round_summary["phase_version"],
    }


def set_phase(database_url: str, round_id: str, phase: str) -> None:
    with psycopg.connect(database_url) as db:
        db.execute("update rounds set phase = %s, phase_version = phase_version + 1 where round_id = %s", (phase, round_id))


def test_no_child_facing_private_room_join_route(client: TestClient) -> None:
    response = client.post('/api/v1/rooms/join', json={'nickname': 'Mango', 'avatar_id': 'mango'})
    assert response.status_code == 404


def test_default_app_provisions_no_room(database_url: str) -> None:
    client = TestClient(create_app(database_url))

    assert admit(client, "Mango").status_code == 404


def test_migrations_are_idempotent(database_url: str) -> None:
    assert apply_migrations(database_url) == []


def test_case_folded_concurrent_nickname_conflict(client: TestClient) -> None:
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda name: admit(client, name), ["Sam", " sam "]))

    assert sorted(response.status_code for response in responses) == [201, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json() == {
        "error": {
            "code": "nickname_taken",
            "message": "That nickname is already being used in this room. Try another one.",
            "retryable": True,
        }
    }


def test_database_rejects_duplicate_normalized_nickname(client: TestClient, database_url: str) -> None:
    first = admit(client, "Mango").json()

    with psycopg.connect(database_url) as db, pytest.raises(psycopg.errors.UniqueViolation):
        db.execute(
            "insert into players(player_id, room_id, nickname, normalized_nickname, avatar_id, membership_status) "
            "values ('p_dup', %s, 'MANGO', 'mango', 'sky', 'admitted')",
            (first["room_id"],),
        )


def test_same_name_without_token_cannot_take_over_but_token_resumes(client: TestClient) -> None:
    first = admit(client, "Mango").json()

    assert admit(client, "mango", "kiwi").status_code == 409

    state = state_of(client, first)
    assert state["session_player_id"] == first["player_id"]
    assert state["admission_status"] == "waiting_for_teammate"


def test_pair_roles_persist_across_recreated_app(client: TestClient, database_url: str) -> None:
    first, second = paired(client)
    first_state, second_state = state_of(client, first), state_of(client, second)

    restarted = TestClient(create_app(database_url))
    first_after, second_after = state_of(restarted, first), state_of(restarted, second)

    assert first_state["room"]["pair_id"] == second_state["room"]["pair_id"]
    assert first_state["round"]["role"] != second_state["round"]["role"]
    assert first_after["round"]["role"] == first_state["round"]["role"]
    assert second_after["round"]["role"] == second_state["round"]["role"]
    assert first_after["round"]["round_id"] == first_state["round"]["round_id"]


def test_database_allows_only_two_seats_per_pair(client: TestClient, database_url: str) -> None:
    first, _second = paired(client)
    third = admit(client, "Sam", "sky").json()
    pair_id = state_of(client, first)["room"]["pair_id"]

    with psycopg.connect(database_url) as db, pytest.raises(psycopg.errors.UniqueViolation):
        db.execute("insert into pair_members(player_id, pair_id, seat) values (%s, %s, 1)", (third["player_id"], pair_id))
    with psycopg.connect(database_url) as db, pytest.raises(psycopg.errors.UniqueViolation):
        db.execute("insert into pair_members(player_id, pair_id, seat) values (%s, %s, 2)", (first["player_id"], pair_id))


def test_wrong_room_guesses_and_drawer_projection_reveal_no_secrets(client: TestClient) -> None:
    first, second = paired(client)

    guessed = client.get("/api/v1/rooms/not-the-room/state", headers=auth_header(first))
    assert guessed.status_code == 403
    assert guessed.json()["error"]["code"] == "not_authorized"

    states = [state_of(client, first), state_of(client, second)]
    drawer_state = next(state for state in states if state["round"]["role"] == "drawer")
    assert "edit_drawing" not in drawer_state["round"]["permissions"]
    assert "hold_to_talk" not in drawer_state["round"]["permissions"]
    serialized = str(drawer_state)
    assert "object_access" not in drawer_state
    for secret in ("object_id", "rubric", "image_url", "model_url"):
        assert secret not in serialized


def test_guest_nickname_never_grants_host_access(client: TestClient) -> None:
    admit(client, "Mango")

    response = client.post("/api/v1/rooms", json={})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "host_authorization_unavailable"


def test_socket_authenticates_before_state_and_rejects_wrong_room(client: TestClient) -> None:
    first, _second = paired(client)

    with client.websocket_connect(f"/api/v1/rooms/{first['room_id']}/socket", headers=ORIGIN) as websocket:
        authenticated, snapshot = ws_authenticate(websocket, first)

    assert authenticated["type"] == "session.authenticated"
    assert snapshot["type"] == "state.snapshot"
    assert snapshot["payload"]["session_player_id"] == first["player_id"]

    with client.websocket_connect("/api/v1/rooms/wrong-room/socket", headers=ORIGIN) as websocket:
        websocket.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": first["guest_session_token"]}})
        error = websocket.receive_json()

    assert error["type"] == "command.error"
    assert error["payload"]["error"]["code"] == "not_authorized"


def test_expired_session_and_room_are_rejected(client: TestClient, database_url: str) -> None:
    first = admit(client, "Mango").json()

    with psycopg.connect(database_url) as db:
        db.execute("update guest_sessions set expires_at = '2000-01-01T00:00:00Z'")
    response = client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(first))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "session_invalid"

    with psycopg.connect(database_url) as db:
        db.execute("update rooms set expires_at = '2000-01-01T00:00:00Z'")
    assert admit(client, "Kiwi", "kiwi").status_code == 404


def test_private_matching_is_scoped_to_server_provisioned_room(client: TestClient, database_url: str) -> None:
    store = client.app.state.game_store
    second_room = store.provision_room(timedelta(days=1)).room_id
    first = admit(client, "Mango").json()
    outsider = admit(client, "Mango", room_id=second_room).json()
    assert state_of(client, first)["admission_status"] == "waiting_for_teammate"
    assert state_of(client, outsider)["admission_status"] == "waiting_for_teammate"
    next_guest = admit(client, "Kiwi", "kiwi").json()
    assert state_of(client, first)["room"]["pair_id"] == state_of(client, next_guest)["room"]["pair_id"]
    assert state_of(client, outsider)["admission_status"] == "waiting_for_teammate"
    denied = client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(outsider))
    assert denied.status_code == 403

    with pytest.raises(ValueError):
        store.provision_room(timedelta(0))
    with psycopg.connect(database_url) as db:
        db.execute("update rooms set expires_at = '2000-01-01T00:00:00Z'")
    assert admit(client, "Sam", "sky").status_code == 404


def test_socket_state_request_refreshes_waiting_snapshot_after_pairing(client: TestClient) -> None:
    first = admit(client, "Mango").json()

    with client.websocket_connect(f"/api/v1/rooms/{first['room_id']}/socket", headers=ORIGIN) as websocket:
        authenticated, waiting = ws_authenticate(websocket, first)
        assert authenticated["type"] == "session.authenticated"
        assert waiting["payload"]["admission_status"] == "waiting_for_teammate"
        admit(client, "Kiwi", "kiwi")
        # The internal admission fixture has no public API to notify sockets;
        # a state request still resynchronizes from authoritative Postgres.
        websocket.send_json({"protocol_version": 1, "type": "state.request", "payload": {}})
        pushed = websocket.receive_json()
        assert pushed["type"] == "state.snapshot"
        assert pushed["payload"]["round"]["phase"] == "role_intro"


def test_role_intro_requires_both_acknowledgements_and_is_idempotent(client: TestClient, database_url: str) -> None:
    first, second = paired(client)
    round_id, payload = command_body(client, first, "intro-1")
    phase_version = payload["expected_round_version"]
    path = f"/api/v1/rounds/{round_id}/intro-seen"

    first_ack = client.post(path, json=payload, headers=auth_header(first))
    assert first_ack.status_code == 200
    assert first_ack.json()["phase"] == "role_intro"
    assert client.post(path, json=payload, headers=auth_header(first)).json() == first_ack.json()
    assert state_of(client, first)["ready"] == {"self_ready": True, "teammate_ready": False}
    assert state_of(client, second)["ready"] == {"self_ready": False, "teammate_ready": True}
    changed = client.post(path, json={**payload, "expected_round_version": 99}, headers=auth_header(first))
    assert changed.status_code == 409

    restarted = TestClient(create_app(database_url))
    assert state_of(restarted, second)["round"]["phase"] == "role_intro"
    second_ack = restarted.post(path, json=payload, headers=auth_header(second))
    assert second_ack.status_code == 200
    assert second_ack.json()["phase"] == "collaborating"
    after = state_of(client, first)
    assert after["round"]["phase_version"] == phase_version + 1
    if after["round"]["role"] == "drawer":
        assert "edit_drawing" in after["round"]["permissions"]
    assert client.post(path, json=payload, headers=auth_header(first)).json() == first_ack.json()

    stale = client.post(path, json={**payload, "command_id": "intro-stale"}, headers=auth_header(first))
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "stale_round"
    wrong_phase = client.post(
        path, json={**payload, "command_id": "intro-late", "expected_round_version": phase_version + 1}, headers=auth_header(first)
    )
    assert wrong_phase.status_code == 409
    assert wrong_phase.json()["error"]["code"] == "wrong_phase"


def test_concurrent_acknowledgements_transition_exactly_once(client: TestClient) -> None:
    first, second = paired(client)
    round_id, payload = command_body(client, first, "intro-race")
    path = f"/api/v1/rounds/{round_id}/intro-seen"
    jobs = [(first, "a"), (first, "a"), (second, "b"), (second, "b")]

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda job: client.post(path, json={**payload, "command_id": job[1]}, headers=auth_header(job[0])), jobs))

    assert [response.status_code for response in responses] == [200, 200, 200, 200]
    after = state_of(client, first)["round"]
    assert after["phase"] == "collaborating"
    assert after["phase_version"] == payload["expected_round_version"] + 1


def test_socket_intro_seen_command_requires_both_players(client: TestClient) -> None:
    first, second = paired(client)
    path = f"/api/v1/rooms/{first['room_id']}/socket"
    with client.websocket_connect(path, headers=ORIGIN) as ws:
        _, snapshot = ws_authenticate(ws, first)
        round_summary = snapshot["payload"]["round"]
        command = {"protocol_version": 1, "type": "round.intro.seen", "command_id": "intro-ws-1",
                   "round_id": round_summary["round_id"],
                   "payload": {"expected_round_version": round_summary["phase_version"]}}
        ws.send_json(command)
        assert ws.receive_json()["type"] == "command.ack"
        assert ws.receive_json()["payload"]["round"]["phase"] == "role_intro"
        ws.send_json({**command, "payload": {"expected_round_version": "nope"}})
        assert ws.receive_json()["payload"]["error"]["code"] == "payload_invalid"
    with client.websocket_connect(path, headers=ORIGIN) as ws:
        ws_authenticate(ws, second)
        ws.send_json({**command, "command_id": "intro-ws-2"})
        assert ws.receive_json()["type"] == "command.ack"
        assert ws.receive_json()["payload"]["round"]["phase"] == "collaborating"


def test_presence_and_transitions_are_pushed_to_both_children(client: TestClient) -> None:
    first, second = paired(client)
    path = f"/api/v1/rooms/{first['room_id']}/socket"
    with client.websocket_connect(path, headers=ORIGIN) as one:
        _, snapshot = ws_authenticate(one, first)
        assert snapshot["payload"]["room"]["teammate"]["connection_status"] == "disconnected"
        assert state_of(client, first)["room"]["teammate"]["connection_status"] == "disconnected"

        with client.websocket_connect(path, headers=ORIGIN) as two:
            _, own = ws_authenticate(two, second)
            assert own["payload"]["room"]["teammate"]["connection_status"] == "connected"
            assert one.receive_json()["payload"]["room"]["teammate"]["connection_status"] == "connected"
            assert state_of(client, first)["room"]["teammate"]["connection_status"] == "connected"

            round_id, payload = command_body(client, first, "push-1")
            for who, command_id in ((first, "push-1"), (second, "push-2")):
                response = client.post(
                    f"/api/v1/rounds/{round_id}/intro-seen", json={**payload, "command_id": command_id}, headers=auth_header(who)
                )
                assert response.status_code == 200
            assert one.receive_json()["payload"]["round"]["phase"] == "role_intro"
            assert one.receive_json()["payload"]["round"]["phase"] == "collaborating"
            assert two.receive_json()["payload"]["round"]["phase"] == "role_intro"
            assert two.receive_json()["payload"]["round"]["phase"] == "collaborating"

        assert one.receive_json()["payload"]["room"]["teammate"]["connection_status"] == "disconnected"


def test_old_or_other_pair_round_cannot_be_acknowledged(client: TestClient) -> None:
    first, _second = paired(client)
    another = admit(client, "Sam", "sky").json()
    admit(client, "Jo", "mint")
    round_id, payload = command_body(client, first, "guess")
    path = f"/api/v1/rounds/{round_id}/intro-seen"

    response = client.post(path, json=payload, headers=auth_header(another))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_authorized"
    missing = client.post(
        "/api/v1/rounds/round_missing/intro-seen",
        json={"command_id": "guess", "round_id": "round_missing", "expected_round_version": 1},
        headers=auth_header(first),
    )
    assert missing.status_code == 403


def test_play_again_needs_both_children_then_swaps_roles_in_a_new_round(client: TestClient, database_url: str) -> None:
    first, second = paired(client)
    before = {"first": state_of(client, first)["round"], "second": state_of(client, second)["round"]}
    round_id = before["first"]["round_id"]
    path = f"/api/v1/rounds/{round_id}/play-again"
    early = client.post(path, json={"command_id": "early", "round_id": round_id, "expected_round_version": 1}, headers=auth_header(first))
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "wrong_phase"

    # Feedback and exploring belong to later features; move there directly for this transition test.
    set_phase(database_url, round_id, "exploring")
    _, payload = command_body(client, first, "again-1")

    waiting = client.post(path, json=payload, headers=auth_header(first))
    assert waiting.json() == {"round_id": round_id, "status": "waiting_for_teammate", "next_round_id": None}
    assert state_of(client, first)["ready"] == {"self_ready": True, "teammate_ready": False}
    assert state_of(client, second)["ready"] == {"self_ready": False, "teammate_ready": True}
    assert client.post(path, json=payload, headers=auth_header(first)).json() == waiting.json()

    started = client.post(path, json={**payload, "command_id": "again-2"}, headers=auth_header(second))
    assert started.status_code == 200
    next_round_id = started.json()["next_round_id"]
    assert started.json()["status"] == "started"

    after_first, after_second = state_of(client, first), state_of(client, second)
    assert after_first["round"]["round_id"] == after_second["round"]["round_id"] == next_round_id
    assert after_first["round"]["phase"] == "role_intro"
    assert after_first["round"]["role"] != before["first"]["role"]
    assert after_second["round"]["role"] != before["second"]["role"]
    assert after_first["round"]["role"] != after_second["round"]["role"]
    assert after_first["ready"] == {"self_ready": False, "teammate_ready": False}

    # The finished round can no longer be mutated, and a replay still returns its original outcome.
    late = client.post(path, json={**payload, "command_id": "late"}, headers=auth_header(first))
    assert late.status_code == 409
    assert late.json()["error"]["code"] == "stale_round"
    assert client.post(path, json=payload, headers=auth_header(first)).json() == waiting.json()
    with psycopg.connect(database_url) as db:
        phases = dict(db.execute("select round_index, phase from rounds order by round_index").fetchall())
    assert phases == {1: "finished", 2: "role_intro"}


def test_socket_play_again_notifies_waiting_and_starts_new_round(client: TestClient, database_url: str) -> None:
    first, second = paired(client)
    round_id = state_of(client, first)["round"]["round_id"]
    set_phase(database_url, round_id, "exploring")  # Later-feature phase trigger fixture.
    path = f"/api/v1/rooms/{first['room_id']}/socket"
    with client.websocket_connect(path, headers=ORIGIN) as one:
        _, first_state = ws_authenticate(one, first)
        with client.websocket_connect(path, headers=ORIGIN) as two:
            _, second_state = ws_authenticate(two, second)
            one.receive_json()  # Teammate presence update.
            command = {"protocol_version": 1, "type": "round.play_again", "command_id": "again-ws-1",
                       "round_id": round_id,
                       "payload": {"expected_round_version": first_state["payload"]["round"]["phase_version"]}}
            one.send_json(command)
            assert one.receive_json()["type"] == "command.ack"
            assert one.receive_json()["payload"]["ready"] == {"self_ready": True, "teammate_ready": False}
            assert two.receive_json()["payload"]["ready"] == {"self_ready": False, "teammate_ready": True}
            two.send_json({**command, "command_id": "again-ws-2",
                           "payload": {"expected_round_version": second_state["payload"]["round"]["phase_version"]}})
            assert two.receive_json()["payload"]["status"] == "started"
            assert two.receive_json()["payload"]["round"]["phase"] == "role_intro"
            assert one.receive_json()["payload"]["round"]["phase"] == "role_intro"


def test_concurrent_play_again_creates_one_next_round(client: TestClient, database_url: str) -> None:
    first, second = paired(client)
    round_id = state_of(client, first)["round"]["round_id"]
    set_phase(database_url, round_id, "exploring")
    _, payload = command_body(client, first, "p")
    path = f"/api/v1/rounds/{round_id}/play-again"

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda who: client.post(path, json={**payload, "command_id": "c"}, headers=auth_header(who)), [first, second]))

    assert [response.status_code for response in responses] == [200, 200]
    with psycopg.connect(database_url) as db:
        assert db.execute("select count(*) from rounds").fetchone()[0] == 2


def test_socket_rejects_untrusted_origin_and_bad_first_message(client: TestClient) -> None:
    first = admit(client, "Mango").json()

    with pytest.raises(WebSocketDisconnect), client.websocket_connect(
        f"/api/v1/rooms/{first['room_id']}/socket", headers={"origin": "https://untrusted.example"}
    ):
        pytest.fail("Untrusted origin was accepted")

    with client.websocket_connect(f"/api/v1/rooms/{first['room_id']}/socket", headers=ORIGIN) as websocket:
        websocket.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": []})
        response = websocket.receive_json()
        assert response["type"] == "command.error"
        assert response["payload"]["error"]["code"] == "session_invalid"
