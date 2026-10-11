from fastapi.testclient import TestClient

from services.api.app.main import app


def test_health_endpoint_is_minimal() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
