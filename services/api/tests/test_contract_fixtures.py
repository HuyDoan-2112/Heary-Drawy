import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from services.api.app.contracts.schemas import ErrorEnvelope, RoleFilteredSnapshot, SocketEnvelope

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "contracts" / "fixtures"
SECRET_KEYS = {
    "object_id",
    "display_name",
    "image_url",
    "model_url",
    "rubric",
    "asset_url",
    "model_bytes",
}


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.parametrize(
    "fixture_name",
    [
        "speaker-collaborating.snapshot.json",
        "drawer-collaborating.snapshot.json",
        "reveal-feedback.snapshot.json",
    ],
)
def test_snapshot_fixtures_validate(fixture_name: str) -> None:
    RoleFilteredSnapshot.model_validate(load_fixture(fixture_name))


def test_socket_fixture_validates() -> None:
    SocketEnvelope.model_validate(load_fixture("drawing-updated.socket.json"))


def test_error_fixture_validates() -> None:
    ErrorEnvelope.model_validate(load_fixture("command-error.json"))


def test_drawer_before_reveal_fixture_contains_no_secret_object_fields() -> None:
    fixture = load_fixture("drawer-collaborating.snapshot.json")
    serialized = json.dumps(fixture)

    assert "object_access" not in fixture
    for key in SECRET_KEYS:
        assert key not in serialized


@pytest.mark.parametrize(
    "object_access",
    [
        None,
        {
            "object_id": "secret-object",
            "display_name": "secret label",
            "image_url": "fixture://secret-image",
        },
    ],
)
def test_schema_rejects_drawer_before_reveal_object_access(object_access: object) -> None:
    fixture = load_fixture("drawer-collaborating.snapshot.json")
    fixture["object_access"] = object_access

    with pytest.raises(ValidationError, match="drawer snapshots before reveal"):
        RoleFilteredSnapshot.model_validate(fixture)
