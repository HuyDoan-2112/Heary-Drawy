"""D2: hold-to-talk clips become text, and Done asks the AI once for feedback and stars."""

import json
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from services.api.app.game import feedback
from services.api.app.game.feedback import (
    FeatureCheck,
    ask_deepseek,
    render_png,
    stars_for,
)
from services.api.tests.conftest import make_client
from services.api.tests.helpers import (
    bearer,
    join,
    start_collaborating,
    state_of,
    unlock,
    wait_for_phase,
)

STROKE = {"stroke_id": "s1", "color": "#E5483D", "width": 14, "points": [{"x": 0.25, "y": 0.5}, {"x": 0.75, "y": 0.5}]}


def pair(client: TestClient) -> tuple[dict, dict]:
    """Returns (speaker, drawer) in collaboration."""
    first = join(client, unlock(client), "mango")
    second = join(client, unlock(client), "kiwi")
    start_collaborating(client, first, second)
    return (first, second) if state_of(client, first)["round"]["role"] == "speaker" else (second, first)


def upload(client: TestClient, child: dict, round_id: str, audio: bytes = b"fake-audio", kind: str = "audio/mp4"):
    headers = {**bearer(child["guest_session_token"]), "content-type": kind}
    return client.post(f"/api/v1/rounds/{round_id}/clips", content=audio, headers=headers)


def done(client: TestClient, drawer: dict) -> None:
    summary = state_of(client, drawer)["round"]
    body = {"command_id": "done", "round_id": summary["round_id"], "expected_round_version": summary["phase_version"]}
    response = client.post(f"/api/v1/rounds/{summary['round_id']}/submit", json=body, headers=bearer(drawer["guest_session_token"]))
    assert response.status_code == 200, response.text


def draw(client: TestClient, drawer: dict, round_id: str) -> None:
    path = f"/api/v1/rooms/{drawer['room_id']}/socket"
    with client.websocket_connect(path, headers={"origin": "http://testserver"}) as ws:
        ws.send_json({"protocol_version": 1, "type": "session.authenticate", "payload": {"guest_session_token": drawer["guest_session_token"]}})
        ws.receive_json()
        ws.receive_json()
        ws.send_json({"protocol_version": 1, "type": "drawing.add", "round_id": round_id, "payload": {"stroke": STROKE}})
        ws.receive_json()


def test_clips_become_text_for_the_right_child_and_role_and_feed_the_ai(database_url: str) -> None:
    heard = {"it is red and round": "speaker", "is it a ball": "drawer"}
    seen: dict = {}

    def fake_transcribe(path: str) -> str:
        with open(path, "rb") as file:
            return file.read().decode()

    def fake_ai(name, features, transcript, png):
        seen.update(name=name, features=features, transcript=transcript, png=png)
        return {"stars": 3, "speaker_lines": ["You said red and round!"], "drawer_lines": ["Great listening!", "What is on top?"]}

    with make_client(database_url, transcribe=fake_transcribe, ask_ai=fake_ai) as client:
        speaker, drawer = pair(client)
        round_id = state_of(client, drawer)["round"]["round_id"]
        draw(client, drawer, round_id)
        assert upload(client, speaker, round_id, b"it is red and round").status_code == 202
        assert upload(client, drawer, round_id, b"is it a ball", "audio/webm;codecs=opus").status_code == 202
        name = state_of(client, speaker)["object_access"]["display_name"]
        done(client, drawer)

        drawer_view = wait_for_phase(client, drawer, "exploring")
        speaker_view = state_of(client, speaker)

    assert seen["name"] == name
    assert seen["features"]
    assert sorted(seen["transcript"]) == sorted((role, text) for text, role in heard.items())
    assert Image.open(BytesIO(seen["png"])).getpixel((380, 340)) == (0xE5, 0x48, 0x3D)
    for view, lines in ((speaker_view, ["You said red and round!"]), (drawer_view, ["Great listening!", "What is on top?"])):
        assert view["feedback"]["shared_result"] == {"status": "scored", "stars": 3, "child_summary": lines[0]}
        assert view["feedback"]["role_feedback"]["lines"] == lines


def test_no_ai_answer_gives_the_neutral_result(client: TestClient) -> None:
    _speaker, drawer = pair(client)
    done(client, drawer)
    result = wait_for_phase(client, drawer, "exploring")["feedback"]["shared_result"]
    assert result["status"] == "neutral_unscored"
    assert "stars" not in result


def test_a_failed_transcription_is_marked_and_does_not_block_the_round(database_url: str) -> None:
    def broken(_path: str) -> str:
        raise RuntimeError("could not decode")

    with make_client(database_url, transcribe=broken) as client:
        speaker, drawer = pair(client)
        round_id = state_of(client, drawer)["round"]["round_id"]
        assert upload(client, speaker, round_id).status_code == 202
        done(client, drawer)
        wait_for_phase(client, drawer, "exploring")
        with client.app.state.game_store._tx() as db:
            statuses = [row["status"] for row in db.execute("select status from clips where round_id = %s", (round_id,))]
    assert statuses == ["failed"]


def test_clips_are_refused_outside_the_round_and_when_too_big(client: TestClient) -> None:
    speaker, drawer = pair(client)
    round_id = state_of(client, drawer)["round"]["round_id"]
    stranger = join(client, unlock(client), "plum")

    assert upload(client, stranger, round_id).status_code == 403
    assert upload(client, speaker, round_id, b"").status_code == 422
    assert upload(client, speaker, round_id, b"x" * (2 * 1024 * 1024 + 1)).status_code == 422


@pytest.mark.parametrize(
    ("described_and_drawn", "stars"),
    [(["red", "round body", "stem on top"], 3), (["red"], 2), ([], 1)],
)
def test_stars_come_from_the_checklist_never_zero(described_and_drawn: list[str], stars: int) -> None:
    features = ("red", "round body", "stem on top", "green leaf")
    checks = [FeatureCheck(feature=f, described=f in described_and_drawn, drawn=f in described_and_drawn) for f in features]
    checks.append(FeatureCheck(feature="invented by the model", described=True, drawn=True))
    assert stars_for(checks, features) == stars


def test_drawing_png_matches_the_stored_strokes() -> None:
    image = Image.open(BytesIO(render_png([STROKE]))).convert("RGB")
    assert image.size == (760, 680)
    assert image.getpixel((380, 340)) == (0xE5, 0x48, 0x3D)
    assert image.getpixel((380, 100)) == (255, 255, 255)


def fake_openai(reply: str):
    """Stands in for the OpenAI SDK client that talks to DeepSeek."""

    class Client:
        def __init__(self, **kwargs) -> None:
            assert kwargs["base_url"] == "https://api.deepseek.com"
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **request):
            content = request["messages"][0]["content"]
            assert request["model"] == "deepseek-flash"
            assert request["response_format"] == {"type": "json_object"}
            assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
            assert "Speaker: it is red" in content[0]["text"]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])

    return Client


def test_deepseek_reply_is_validated_and_bad_replies_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
    features = ("red", "round body")
    args = ("Apple", features, [("speaker", "it is red")], render_png([STROKE]))
    good = {
        "features": [{"feature": "red", "described": True, "drawn": True}, {"feature": "round body", "described": True, "drawn": True}],
        "speaker_lines": ["You described the color!"],
        "drawer_lines": ["You drew it red!"],
    }
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert ask_deepseek(*args) is None  # No key: neutral result, no network call.

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(feedback, "OpenAI", fake_openai(json.dumps(good)))
    assert ask_deepseek(*args) == {"stars": 3, "speaker_lines": ["You described the color!"], "drawer_lines": ["You drew it red!"]}
    for bad in ("", "not json", json.dumps({**good, "speaker_lines": []}), json.dumps({"features": "all"})):
        monkeypatch.setattr(feedback, "OpenAI", fake_openai(bad))
        assert ask_deepseek(*args) is None
