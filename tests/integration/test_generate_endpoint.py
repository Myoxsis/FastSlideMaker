from fastapi.testclient import TestClient

from app.main import app


def test_generate_endpoint_returns_deck() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/generate",
        json={"topic": "Platform strategy", "audience": "Board", "tone": "Professional", "slide_count": 4},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "deck" in payload
    assert len(payload["deck"]["slides"]) == 4
