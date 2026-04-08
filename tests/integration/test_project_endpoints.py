from fastapi.testclient import TestClient
import pytest

from app.main import app


def _payload() -> dict:
    return {
        "name": "Integration Project",
        "deck": {
            "metadata": {"title": "Integration Deck", "audience": "Team", "purpose": "Validate"},
            "user_prompt": "Original integration prompt",
            "prompt_last_updated_at": "2026-01-01T00:00:00+00:00",
            "slide_order": ["s1"],
            "slides": [
                {
                    "id": "s1",
                    "order": 1,
                    "type": "content",
                    "title": "Overview",
                    "text_blocks": [{"id": "t1", "role": "body", "text": "Integration test payload."}],
                }
            ],
        },
    }


def test_project_save_list_load_and_export_json() -> None:
    client = TestClient(app)

    save_response = client.post("/api/projects", json=_payload())
    assert save_response.status_code == 200
    project_id = save_response.json()["project_id"]

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert any(item["project_id"] == project_id for item in list_response.json()["projects"])

    load_response = client.get(f"/api/projects/{project_id}")
    assert load_response.status_code == 200
    assert load_response.json()["deck"]["metadata"]["title"] == "Integration Deck"
    assert load_response.json()["deck"]["user_prompt"] == "Original integration prompt"

    json_export = client.get(f"/api/projects/{project_id}/export/json")
    assert json_export.status_code == 200
    assert "application/json" in json_export.headers["content-type"]


def test_prompt_update_and_regeneration_endpoints() -> None:
    client = TestClient(app)

    base = client.get("/api/semantic-deck")
    assert base.status_code == 200
    assert "user_prompt" in base.json()

    updated = client.put("/api/semantic-deck/prompt", json={"user_prompt": "Updated from integration test"})
    assert updated.status_code == 200
    assert updated.json()["user_prompt"] == "Updated from integration test"
    assert updated.json()["prompt_last_updated_at"]

    regenerated = client.post("/api/semantic-deck/regenerate", json={"user_prompt": "Deck regeneration prompt"})
    assert regenerated.status_code == 200
    assert regenerated.json()["user_prompt"] == "Deck regeneration prompt"

    slide_id = regenerated.json()["slide_order"][0]
    regenerated_slide = client.post(
        "/api/semantic-deck/regenerate-slide",
        json={"slide_id": slide_id, "user_prompt": "Single slide regeneration prompt"},
    )
    assert regenerated_slide.status_code == 200
    assert regenerated_slide.json()["user_prompt"] == "Single slide regeneration prompt"


def test_project_export_pptx() -> None:
    pytest.importorskip("pptx")

    client = TestClient(app)
    project_id = client.post("/api/projects", json=_payload()).json()["project_id"]

    pptx_export = client.get(f"/api/projects/{project_id}/export/pptx")
    assert pptx_export.status_code == 200
    assert "presentation" in pptx_export.headers["content-type"]
    assert len(pptx_export.content) > 0
