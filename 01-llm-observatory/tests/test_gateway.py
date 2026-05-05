from fastapi.testclient import TestClient

from gateway.gateway import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_logs_mock_response() -> None:
    client = TestClient(app)
    response = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "endpoint": "test-suite",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["tokens"]["prompt"] > 0
    assert data["response"]
