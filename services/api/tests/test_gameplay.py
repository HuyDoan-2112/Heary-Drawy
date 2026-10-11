"""One full demo round: secret picture, live drawing, submit, reveal, and voice relay."""

from fastapi.testclient import TestClient

from services.api.app.game.objects import CATALOG
from services.api.tests.helpers import (
    bearer,
    join,
    start_collaborating,
    state_of,
    unlock,
    wait_for_phase,
    ws_authenticate,
)

ORIGIN = {"origin": "http://testserver"}
STROKE = {"stroke_id": "s1", "color": "#E5483D", "width": 14, "points": [{"x": 0.2, "y": 0.3}, {"x": 0.5, "y": 0.6}]}


def speaker_and_drawer(client: TestClient) -> tuple[dict, dict]:
    first = join(client, unlock(client), "mango")
    second = join(client, unlock(client), "kiwi")
    start_collaborating(client, first, second)
    if state_of(client, first)["round"]["role"] == "speaker":
        return first, second
    return second, first


def test_only_the_speaker_sees_the_picture_before_reveal(client: TestClient) -> None:
    speaker, drawer = speaker_and_drawer(client)
    speaker_state, drawer_state = state_of(client, speaker), state_of(client, drawer)
    round_id = speaker_state["round"]["round_id"]

    assert speaker_state["object_access"]["image_url"] == f"/api/v1/rounds/{round_id}/picture"
    assert speaker_state["object_access"]["model_url"] == f"/api/v1/rounds/{round_id}/model"
    assert "object_access" not in drawer_state
    assert "feedback" not in drawer_state
    for kind, media_type, magic in (("picture", "image/png", b"\x89PNG"), ("model", "model/gltf-binary", b"glTF")):
        allowed = client.get(f"/api/v1/rounds/{round_id}/{kind}", headers=bearer(speaker["guest_session_token"]))
        assert allowed.status_code == 200
        assert allowed.headers["content-type"] == media_type
        assert allowed.content.startswith(magic)
        blocked = client.get(f"/api/v1/rounds/{round_id}/{kind}", headers=bearer(drawer["guest_session_token"]))
        assert blocked.status_code == 403
        assert magic not in blocked.content


def test_drawer_strokes_reach_the_speaker_live_and_speaker_cannot_draw(client: TestClient) -> None:
    speaker, drawer = speaker_and_drawer(client)
    round_id = state_of(client, drawer)["round"]["round_id"]
    path = f"/api/v1/rooms/{drawer['room_id']}/socket"

    with client.websocket_connect(path, headers=ORIGIN) as speaker_ws, client.websocket_connect(path, headers=ORIGIN) as drawer_ws:
        ws_authenticate(speaker_ws, speaker)
        ws_authenticate(drawer_ws, drawer)
        speaker_ws.receive_json()  # Drawer connected.

        drawer_ws.send_json({"protocol_version": 1, "type": "drawing.add", "round_id": round_id, "payload": {"stroke": STROKE}})
        seen = speaker_ws.receive_json()["payload"]["drawing"]
        assert seen["revision"] == 1
        assert seen["strokes"][0]["points"] == STROKE["points"]
        drawer_ws.receive_json()

        drawer_ws.send_json({"protocol_version": 1, "type": "drawing.undo", "round_id": round_id, "payload": {}})
        assert speaker_ws.receive_json()["payload"]["drawing"]["strokes"] == []
        drawer_ws.receive_json()

        speaker_ws.send_json({"protocol_version": 1, "type": "drawing.add", "round_id": round_id, "payload": {"stroke": STROKE}})
        assert speaker_ws.receive_json()["payload"]["error"]["code"] == "not_authorized"


def test_submit_reveals_the_picture_with_a_neutral_result(client: TestClient) -> None:
    speaker, drawer = speaker_and_drawer(client)
    summary = state_of(client, drawer)["round"]
    body = {"command_id": "done-1", "round_id": summary["round_id"], "expected_round_version": summary["phase_version"]}

    by_speaker = client.post(f"/api/v1/rounds/{summary['round_id']}/submit", json=body, headers=bearer(speaker["guest_session_token"]))
    assert by_speaker.status_code == 403
    done = client.post(f"/api/v1/rounds/{summary['round_id']}/submit", json={**body, "command_id": "done-2"},
                       headers=bearer(drawer["guest_session_token"]))
    assert done.json()["phase"] == "finalizing"  # Drawy is looking.
    assert "object_access" not in state_of(client, drawer)

    revealed = wait_for_phase(client, drawer, "exploring")
    assert revealed["object_access"]["object_id"] == state_of(client, speaker)["object_access"]["object_id"]
    assert revealed["feedback"]["shared_result"]["status"] == "neutral_unscored"
    assert "stars" not in revealed["feedback"]["shared_result"]
    picture = client.get(revealed["object_access"]["image_url"], headers=bearer(drawer["guest_session_token"]))
    assert picture.status_code == 200


def test_voice_setup_messages_are_relayed_only_to_the_teammate(client: TestClient) -> None:
    speaker, drawer = speaker_and_drawer(client)
    path = f"/api/v1/rooms/{speaker['room_id']}/socket"

    with client.websocket_connect(path, headers=ORIGIN) as one, client.websocket_connect(path, headers=ORIGIN) as two:
        ws_authenticate(one, speaker)
        ws_authenticate(two, drawer)
        one.receive_json()  # Teammate connected.

        one.send_json({"protocol_version": 1, "type": "voice.signal", "payload": {"description": {"type": "offer", "sdp": "v=0"}}})
        relayed = two.receive_json()
        assert relayed == {"protocol_version": 1, "type": "voice.signal", "payload": {"description": {"type": "offer", "sdp": "v=0"}}}
        two.send_json({"protocol_version": 1, "type": "voice.talking", "payload": {"talking": True}})
        assert one.receive_json()["payload"] == {"talking": True}


def test_every_secret_object_has_its_3d_model_and_picture() -> None:
    for item in CATALOG:
        assert item.model_path.read_bytes().startswith(b"glTF"), item.object_id
        assert item.image_path.read_bytes().startswith(b"\x89PNG"), item.object_id
        assert len(item.features) >= 3, item.object_id
