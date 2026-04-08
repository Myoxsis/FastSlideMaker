"""HTTP routes for UI and slide-generation endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.models.schemas import DeckRequest, DeckResponse
from app.services.export import ExportService
from app.services.generation import GenerationService
from app.services.rendering import RenderingService
from app.services.validation import ValidationService

router = APIRouter()


@router.get("/health")
async def healthcheck(request: Request) -> dict:
    return {
        "status": "ok",
        "ollama_available": getattr(request.app.state, "ollama_available", False),
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/generate", response_model=DeckResponse)
async def generate_slides(payload: DeckRequest, request: Request) -> DeckResponse:
    generation_service: GenerationService = getattr(request.app.state, "generation_service", GenerationService())

    generated_deck = await generation_service.generate(payload)
    validated_deck = ValidationService().validate(generated_deck)
    rendered_deck = RenderingService().render(validated_deck)
    export_artifacts = ExportService().export(rendered_deck)

    return DeckResponse(deck=rendered_deck, export=export_artifacts)
