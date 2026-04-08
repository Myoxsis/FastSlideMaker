from fastapi.testclient import TestClient
import pytest

from app.main import app


def _payload() -> dict:
    return {
        "name": "Integration Project",
        "deck": {
            "metadata": {"title": "Integration Deck", "audience": "Team", "purpose": "Validate"},
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

    json_export = client.get(f"/api/projects/{project_id}/export/json")
    assert json_export.status_code == 200
    assert "application/json" in json_export.headers["content-type"]


def test_project_export_pptx() -> None:
    pytest.importorskip("pptx")

    client = TestClient(app)
    project_id = client.post("/api/projects", json=_payload()).json()["project_id"]

    pptx_export = client.get(f"/api/projects/{project_id}/export/pptx")
    assert pptx_export.status_code == 200
    assert "presentation" in pptx_export.headers["content-type"]
    assert len(pptx_export.content) > 0
