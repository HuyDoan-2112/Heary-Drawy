"""Shared API test steps: unlock a device, admit a child, read state, reach collaboration."""

import time

from fastapi.testclient import TestClient


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def unlock(client: TestClient, passcode: str | None = None) -> dict:
    response = client.post("/api/v1/device-enrollments", json={"passcode": passcode or client.app.state.test_room_passcode})
    assert response.status_code == 201, response.text
    return response.json()


def join(client: TestClient, device: dict, avatar_id: str, nickname: str = "") -> dict:
    response = client.post(
        f"/api/v1/rooms/{device['room_id']}/guests",
        json={"nickname": nickname, "avatar_id": avatar_id},
        headers=bearer(device["device_token"]),
    )
    assert response.status_code == 201, response.text
    return response.json()


def state_of(client: TestClient, session: dict) -> dict:
    response = client.get(f"/api/v1/rooms/{session['room_id']}/state", headers=bearer(session["guest_session_token"]))
    assert response.status_code == 200, response.text
    return response.json()


def ws_authenticate(ws, session: dict) -> dict:
    ws.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": session["guest_session_token"]}})
    assert ws.receive_json()["type"] == "session.authenticated"
    return ws.receive_json()


def start_collaborating(client: TestClient, *children: dict) -> None:
    """Both children acknowledge the role intro."""
    for index, child in enumerate(children):
        summary = state_of(client, child)["round"]
        response = client.post(
            f"/api/v1/rounds/{summary['round_id']}/intro-seen",
            json={"command_id": f"intro-{index}", "round_id": summary["round_id"], "expected_round_version": summary["phase_version"]},
            headers=bearer(child["guest_session_token"]),
        )
        assert response.status_code == 200, response.text


def wait_for_phase(client: TestClient, session: dict, phase: str, timeout: float = 5) -> dict:
    """Poll state until the round reaches `phase` (the AI check runs in the background)."""
    deadline = time.monotonic() + timeout
    while True:
        state = state_of(client, session)
        if state["round"]["phase"] == phase or time.monotonic() > deadline:
            assert state["round"]["phase"] == phase
            return state
        time.sleep(0.05)
