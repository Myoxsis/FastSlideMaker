"""Startup hooks for health checks and service wiring."""

from fastapi import FastAPI

from app.services.generation import GenerationService
from project_store import ProjectStore


def register_startup_events(app: FastAPI) -> None:
    """Attach startup handlers to prewarm service dependencies."""

    @app.on_event("startup")
    async def warm_generation_service() -> None:
        service = GenerationService()
        app.state.generation_service = service
        app.state.ollama_available = await service.check_ollama()
        app.state.project_store = ProjectStore()
