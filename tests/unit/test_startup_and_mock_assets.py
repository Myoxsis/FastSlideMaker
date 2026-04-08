from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.startup import register_startup_events


def test_startup_boot_sequence_wires_core_state() -> None:
    app = FastAPI()
    register_startup_events(app)

    @app.get("/state")
    async def state() -> dict:
        return {
            "has_generation_service": hasattr(app.state, "generation_service"),
            "has_project_store": hasattr(app.state, "project_store"),
            "ollama_available_is_bool": isinstance(getattr(app.state, "ollama_available", None), bool),
        }

    with TestClient(app) as client:
        response = client.get("/state")
        assert response.status_code == 200
        payload = response.json()
        assert payload["has_generation_service"] is True
        assert payload["has_project_store"] is True
        assert payload["ollama_available_is_bool"] is True
