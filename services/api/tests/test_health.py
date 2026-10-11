from fastapi.testclient import TestClient

from services.api.app.main import create_app


def test_health_endpoint_is_minimal(database_url: str) -> None:
    response = TestClient(create_app(database_url)).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
