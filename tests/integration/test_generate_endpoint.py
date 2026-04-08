from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_endpoint_returns_deck() -> None:
    response = client.post(
        "/api/generate",
        json={
            "topic": "Order-to-cash process and architecture",
            "audience": "Board",
            "tone": "Professional",
            "slide_count": 4,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "deck" in payload
    assert len(payload["deck"]["slides"]) == 4
    assert payload["deck"]["metadata"]["mode"] == "mock"
    assert payload["deck"]["metadata"]["mock_scenario"] == "order-to-cash-architecture"


def test_mock_examples_endpoint_exposes_prompts_and_outputs() -> None:
    response = client.get("/api/mock-mode/examples")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["prompts"]) >= 3
    assert "order-to-cash-architecture" in payload["sample_outputs"]
    assert "customer-onboarding-target-design" in payload["sample_outputs"]
    assert "claims-transformation-roadmap" in payload["sample_outputs"]
