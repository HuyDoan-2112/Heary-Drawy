from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from services.api.app.main import create_app


SHAPE_CODE = ["circle", "triangle", "square"]


def make_client(tmp_path):
    return TestClient(create_app(db_path=tmp_path / "rooms.sqlite3", fixture_room=True))


def join(client: TestClient, nickname: str, avatar_id: str = "mango"):
    return client.post(
        "/api/v1/rooms/join",
        json={"shape_code": SHAPE_CODE, "nickname": nickname, "avatar_id": avatar_id},
    )


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_default_app_does_not_provision_a_public_known_code(tmp_path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "empty.sqlite3"))

    assert join(client, "Mango").status_code == 404


def test_case_folded_concurrent_nickname_conflict(tmp_path) -> None:
    client = make_client(tmp_path)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda name: join(client, name), ["Sam", " sam "]))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json() == {
        "error": {
            "code": "nickname_taken",
            "message": "That nickname is already being used in this room. Try another one.",
            "retryable": True,
        }
    }


def test_same_name_without_token_cannot_take_over_but_token_resumes(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango").json()

    duplicate = join(client, "mango", "kiwi")
    assert duplicate.status_code == 409

    state = client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(first["guest_session_token"]))
    assert state.status_code == 200
    assert state.json()["session_player_id"] == first["player_id"]
    assert state.json()["admission_status"] == "waiting_for_teammate"


def test_pair_roles_persist_across_recreated_app(tmp_path) -> None:
    db_path = tmp_path / "rooms.sqlite3"
    client = TestClient(create_app(db_path=db_path, fixture_room=True))
    first = join(client, "Mango", "mango").json()
    second = join(client, "Kiwi", "kiwi").json()

    first_state = client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(first["guest_session_token"])).json()
    second_state = client.get(f"/api/v1/rooms/{second['room_id']}/state", headers=auth_header(second["guest_session_token"])).json()

    restarted = TestClient(create_app(db_path=db_path, fixture_room=True))
    first_after = restarted.get(
        f"/api/v1/rooms/{first['room_id']}/state",
        headers=auth_header(first["guest_session_token"]),
    ).json()
    second_after = restarted.get(
        f"/api/v1/rooms/{second['room_id']}/state",
        headers=auth_header(second["guest_session_token"]),
    ).json()

    assert first_state["room"]["pair_id"] == second_state["room"]["pair_id"]
    assert first_state["round"]["role"] != second_state["round"]["role"]
    assert first_after["round"]["role"] == first_state["round"]["role"]
    assert second_after["round"]["role"] == second_state["round"]["role"]
    assert first_after["round"]["round_id"] == first_state["round"]["round_id"]


def test_wrong_room_guesses_and_drawer_projection_reveal_no_secrets(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango", "mango").json()
    second = join(client, "Kiwi", "kiwi").json()

    guessed = client.get("/api/v1/rooms/not-the-room/state", headers=auth_header(first["guest_session_token"]))
    assert guessed.status_code == 403
    assert guessed.json()["error"]["code"] == "not_authorized"

    states = [
        client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(first["guest_session_token"])).json(),
        client.get(f"/api/v1/rooms/{second['room_id']}/state", headers=auth_header(second["guest_session_token"])).json(),
    ]
    drawer_state = next(state for state in states if state["round"]["role"] == "drawer")
    assert "edit_drawing" not in drawer_state["round"]["permissions"]
    assert "hold_to_talk" not in drawer_state["round"]["permissions"]
    serialized = str(drawer_state)
    assert "object_access" not in drawer_state
    assert "object_id" not in serialized
    assert "rubric" not in serialized
    assert "image_url" not in serialized
    assert "model_url" not in serialized


def test_teacher_nickname_gets_no_host_access(tmp_path) -> None:
    client = make_client(tmp_path)
    join(client, "Teacher")

    response = client.post("/api/v1/rooms", json={"shape_code": SHAPE_CODE})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "host_authorization_unavailable"


def test_socket_authenticates_before_state_and_rejects_wrong_room(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango", "mango").json()
    join(client, "Kiwi", "kiwi")

    with client.websocket_connect(f"/api/v1/rooms/{first['room_id']}/socket", headers={"origin": "http://testserver"}) as websocket:
        websocket.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": first["guest_session_token"]}})
        authenticated = websocket.receive_json()
        snapshot = websocket.receive_json()

    assert authenticated["type"] == "session.authenticated"
    assert snapshot["type"] == "state.snapshot"
    assert snapshot["payload"]["session_player_id"] == first["player_id"]

    with client.websocket_connect("/api/v1/rooms/wrong-room/socket", headers={"origin": "http://testserver"}) as websocket:
        websocket.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": first["guest_session_token"]}})
        error = websocket.receive_json()

    assert error["type"] == "command.error"
    assert error["payload"]["error"]["code"] == "not_authorized"


def test_expired_session_and_room_are_rejected(tmp_path) -> None:
    db_path = tmp_path / "rooms.sqlite3"
    client = TestClient(create_app(db_path=db_path, fixture_room=True))
    first = join(client, "Mango").json()

    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE guest_sessions SET expires_at = '2000-01-01T00:00:00Z'")

    response = client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(first["guest_session_token"]))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "session_invalid"

    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE rooms SET expires_at = '2000-01-01T00:00:00Z'")

    assert join(client, "Kiwi", "kiwi").status_code == 404


def test_socket_state_request_refreshes_waiting_snapshot_after_pairing(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango").json()

    with client.websocket_connect(
        f"/api/v1/rooms/{first['room_id']}/socket", headers={"origin": "http://testserver"}
    ) as websocket:
        websocket.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": first["guest_session_token"]}})
        assert websocket.receive_json()["type"] == "session.authenticated"
        assert websocket.receive_json()["payload"]["admission_status"] == "waiting_for_teammate"
        join(client, "Kiwi", "kiwi")
        websocket.send_json({"protocol_version": 1, "type": "state.request", "payload": {}})
        snapshot = websocket.receive_json()
        assert snapshot["type"] == "state.snapshot"
        assert snapshot["payload"]["round"]["phase"] == "role_intro"


def test_role_intro_requires_both_acknowledgements_and_is_idempotent(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango").json()
    second = join(client, "Kiwi", "kiwi").json()
    url = f"/api/v1/rooms/{first['room_id']}/state"
    before = client.get(url, headers=auth_header(first["guest_session_token"])).json()
    round_id = before["round"]["round_id"]
    phase_version = before["round"]["phase_version"]
    payload = {"command_id": "intro-1", "round_id": round_id, "expected_round_version": phase_version}
    path = f"/api/v1/rounds/{round_id}/intro-seen"

    first_ack = client.post(path, json=payload, headers=auth_header(first["guest_session_token"]))
    assert first_ack.status_code == 200
    assert first_ack.json()["phase"] == "role_intro"
    assert client.post(path, json=payload, headers=auth_header(first["guest_session_token"])).json() == first_ack.json()
    changed = client.post(path, json={**payload, "expected_round_version": 99}, headers=auth_header(first["guest_session_token"]))
    assert changed.status_code == 409

    restarted = make_client(tmp_path)
    assert restarted.get(url, headers=auth_header(second["guest_session_token"])).json()["round"]["phase"] == "role_intro"
    second_ack = restarted.post(path, json=payload, headers=auth_header(second["guest_session_token"]))
    assert second_ack.status_code == 200
    assert second_ack.json()["phase"] == "collaborating"
    after = client.get(url, headers=auth_header(first["guest_session_token"])).json()
    assert after["round"]["phase_version"] == phase_version + 1
    if after["round"]["role"] == "drawer":
        assert "edit_drawing" in after["round"]["permissions"]
    assert client.post(path, json=payload, headers=auth_header(first["guest_session_token"])).json() == first_ack.json()
    stale = client.post(path, json={**payload, "command_id": "intro-stale"}, headers=auth_header(first["guest_session_token"]))
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "wrong_phase"


def test_socket_intro_seen_command_requires_both_players(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango").json()
    second = join(client, "Kiwi", "kiwi").json()
    path = f"/api/v1/rooms/{first['room_id']}/socket"
    with client.websocket_connect(path, headers={"origin": "http://testserver"}) as ws:
        ws.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": first["guest_session_token"]}})
        ws.receive_json()
        state = ws.receive_json()["payload"]
        command = {"protocol_version": 1, "type": "round.intro.seen", "command_id": "intro-ws-1",
                   "round_id": state["round"]["round_id"],
                   "payload": {"expected_round_version": state["round"]["phase_version"]}}
        ws.send_json(command)
        assert ws.receive_json()["type"] == "command.ack"
        assert ws.receive_json()["payload"]["round"]["phase"] == "role_intro"
    with client.websocket_connect(path, headers={"origin": "http://testserver"}) as ws:
        ws.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": second["guest_session_token"]}})
        ws.receive_json()
        ws.receive_json()
        ws.send_json({**command, "command_id": "intro-ws-2"})
        assert ws.receive_json()["type"] == "command.ack"
        assert ws.receive_json()["payload"]["round"]["phase"] == "collaborating"


def test_old_or_other_pair_round_cannot_be_acknowledged(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango").json()
    join(client, "Kiwi", "kiwi")
    another = join(client, "Sam", "sky").json()
    join(client, "Jo", "mint")
    round_id = client.get(f"/api/v1/rooms/{first['room_id']}/state", headers=auth_header(first["guest_session_token"])).json()["round"]["round_id"]
    path = f"/api/v1/rounds/{round_id}/intro-seen"
    response = client.post(path, json={"command_id": "guess", "round_id": round_id, "expected_round_version": 1}, headers=auth_header(another["guest_session_token"]))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_authorized"
    missing = client.post("/api/v1/rounds/round_missing/intro-seen", json={"command_id": "guess", "round_id": "round_missing", "expected_round_version": 1}, headers=auth_header(first["guest_session_token"]))
    assert missing.status_code == 403


def test_socket_rejects_untrusted_origin_and_bad_first_message(tmp_path) -> None:
    client = make_client(tmp_path)
    first = join(client, "Mango").json()

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/api/v1/rooms/{first['room_id']}/socket", headers={"origin": "https://untrusted.example"}
        ):
            pytest.fail("Untrusted origin was accepted")

    with client.websocket_connect(
        f"/api/v1/rooms/{first['room_id']}/socket", headers={"origin": "http://testserver"}
    ) as websocket:
        websocket.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": []})
        response = websocket.receive_json()
        assert response["type"] == "command.error"
        assert response["payload"]["error"]["code"] == "session_invalid"
