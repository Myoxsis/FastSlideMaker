"""HTTP routes for UI, generation, and semantic preview endpoints."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.models.schemas import DeckRequest, DeckResponse, MilestoneStatus, SemanticPresentation, SlideType, TextBlock, TextRole
from app.services.designer import DesignerService
from app.services.export import ExportService
from app.services.generation import GenerationService
from app.services.mock_mode import CANNED_SAMPLE_PROMPTS, DECK_TEMPLATES
from app.services.rendering import RenderingService
from app.services.validation import ValidationService
from project_store import ProjectStore

router = APIRouter()


class SaveProjectRequest(BaseModel):
    name: str = Field(default="Untitled Project", max_length=120)
    deck: SemanticPresentation


class PromptUpdateRequest(BaseModel):
    user_prompt: str = Field(default="", max_length=8000)


class RegenerateDeckRequest(BaseModel):
    user_prompt: str | None = Field(default=None, max_length=8000)


class RegenerateSlideRequest(BaseModel):
    slide_id: str = Field(..., min_length=1, max_length=64)
    user_prompt: str | None = Field(default=None, max_length=8000)


def _project_store(request: Request) -> ProjectStore:
    if not hasattr(request.app.state, "project_store"):
        request.app.state.project_store = ProjectStore()
    return request.app.state.project_store


def _build_default_semantic_deck() -> SemanticPresentation:
    now = datetime.now(timezone.utc).isoformat()
    default_prompt = "Build an executive-ready enterprise delivery plan with process, architecture, and roadmap slides."
    return SemanticPresentation.model_validate(
        {
            "metadata": {
                "title": "Enterprise Delivery Plan",
                "subtitle": "Operational readiness and execution blueprint",
                "audience": "Executive Leadership",
                "purpose": "Align teams on delivery design and milestones",
            },
            "user_prompt": default_prompt,
            "prompt_last_updated_at": now,
            "slide_order": ["process-flow", "layered-architecture", "roadmap"],
            "slides": [
                {
                    "id": "process-flow",
                    "order": 1,
                    "type": SlideType.PROCESS,
                    "title": "Process Flow",
                    "objective": "Clarify the deterministic delivery lifecycle from intake through release.",
                    "text_blocks": [
                        {
                            "id": "process-context",
                            "role": TextRole.CALLOUT,
                            "label": "Operating Model",
                            "text": "Each phase has an explicit owner and a measurable handoff.",
                        }
                    ],
                    "process": {
                        "steps": [
                            {
                                "id": "discover",
                                "label": "Discover",
                                "description": "Capture requirements and constraints.",
                                "owner": "Product",
                                "outputs": ["Scope", "Prioritized backlog"],
                            },
                            {
                                "id": "design",
                                "label": "Design",
                                "description": "Define architecture and implementation plan.",
                                "owner": "Architecture",
                                "outputs": ["Design spec", "Delivery plan"],
                            },
                            {
                                "id": "build",
                                "label": "Build",
                                "description": "Implement features and validate quality.",
                                "owner": "Engineering",
                                "outputs": ["Validated build", "Test evidence"],
                            },
                            {
                                "id": "release",
                                "label": "Release",
                                "description": "Deploy in controlled waves and monitor outcomes.",
                                "owner": "Operations",
                                "outputs": ["Production release", "Post-launch report"],
                            },
                        ]
                    },
                },
                {
                    "id": "layered-architecture",
                    "order": 2,
                    "type": SlideType.ARCHITECTURE,
                    "title": "Layered Architecture",
                    "objective": "Show clear separation of concerns across platform layers.",
                    "text_blocks": [
                        {
                            "id": "arch-principle",
                            "role": TextRole.CALLOUT,
                            "label": "Design Principle",
                            "text": "Interfaces are stable, implementations can evolve independently.",
                        }
                    ],
                    "architecture": {
                        "layers": [
                            {
                                "id": "experience",
                                "name": "Experience Layer",
                                "responsibility": "Handles user interactions and accessibility.",
                                "components": ["Web UI", "Template Renderer", "Editor Controls"],
                            },
                            {
                                "id": "application",
                                "name": "Application Layer",
                                "responsibility": "Coordinates workflows and business rules.",
                                "components": ["Slide Controller", "Validation Service", "Export Orchestrator"],
                            },
                            {
                                "id": "data",
                                "name": "Data Layer",
                                "responsibility": "Stores semantic models and artifacts.",
                                "components": ["Semantic JSON Store", "Versioned Snapshots", "Asset Catalog"],
                            },
                        ],
                        "integrations": [
                            {
                                "id": "llm",
                                "system": "LLM Provider",
                                "purpose": "Generate draft narrative suggestions.",
                                "direction": "outbound",
                                "protocol": "HTTPS",
                            },
                            {
                                "id": "storage",
                                "system": "Object Storage",
                                "purpose": "Persist exports and metadata.",
                                "direction": "bidirectional",
                                "protocol": "S3 API",
                            },
                        ],
                    },
                },
                {
                    "id": "roadmap",
                    "order": 3,
                    "type": SlideType.ROADMAP,
                    "title": "Roadmap",
                    "objective": "Sequence rollout outcomes by quarter.",
                    "text_blocks": [
                        {
                            "id": "roadmap-note",
                            "role": TextRole.CALLOUT,
                            "label": "Success Metric",
                            "text": "Achieve predictable release cadence and reduce cycle time by 30%.",
                        }
                    ],
                    "roadmap": {
                        "phases": [
                            {
                                "id": "q2",
                                "name": "Q2 Foundations",
                                "objective": "Establish reliable data and publishing pipelines.",
                                "milestones": [
                                    {
                                        "id": "schema",
                                        "label": "Semantic schema finalized",
                                        "status": MilestoneStatus.COMPLETE,
                                        "target_period": "Apr 2026",
                                    },
                                    {
                                        "id": "preview",
                                        "label": "Preview renderer delivered",
                                        "status": MilestoneStatus.IN_PROGRESS,
                                        "target_period": "May 2026",
                                    },
                                ],
                            },
                            {
                                "id": "q3",
                                "name": "Q3 Scale",
                                "objective": "Expand templates and harden collaboration workflows.",
                                "milestones": [
                                    {
                                        "id": "templates",
                                        "label": "Add 8 deterministic slide templates",
                                        "status": MilestoneStatus.PLANNED,
                                        "target_period": "Jul 2026",
                                    },
                                    {
                                        "id": "review",
                                        "label": "Stakeholder review workflow",
                                        "status": MilestoneStatus.PLANNED,
                                        "target_period": "Aug 2026",
                                    },
                                ],
                            },
                        ]
                    },
                },
            ],
        }
    )

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_regenerated_text(prompt: str, slide_title: str, index: int) -> str:
    return (
        f"{prompt} — {slide_title} focus: "
        f"deterministic update #{index} aligned to the active project context."
    )


def _regenerate_semantic_deck(deck: SemanticPresentation, prompt: str) -> SemanticPresentation:
    normalized_prompt = prompt.strip()
    updated = deck.model_copy(deep=True)
    updated.user_prompt = normalized_prompt
    updated.prompt_last_updated_at = _now_iso()
    if normalized_prompt:
        updated.metadata.purpose = normalized_prompt[:280]

    for index, slide in enumerate(updated.slides, start=1):
        slide.objective = f"Generated from current prompt for {slide.title}."
        if slide.text_blocks:
            slide.text_blocks[0].text = _build_regenerated_text(normalized_prompt, slide.title, index)[:2000]
        else:
            slide.text_blocks = [
                TextBlock(
                    id=f"prompt-context-{index}",
                    role=TextRole.CALLOUT,
                    label="Prompt Context",
                    text=_build_regenerated_text(normalized_prompt, slide.title, index)[:2000],
                )
            ]
    return DesignerService().design_presentation(updated.normalized())


def _regenerate_single_slide(deck: SemanticPresentation, prompt: str, slide_id: str) -> SemanticPresentation:
    normalized_prompt = prompt.strip()
    updated = deck.model_copy(deep=True)
    updated.user_prompt = normalized_prompt
    updated.prompt_last_updated_at = _now_iso()

    for slide in updated.slides:
        if slide.id != slide_id:
            continue
        slide.objective = f"Generated from current prompt for {slide.title}."
        if slide.text_blocks:
            slide.text_blocks[0].text = _build_regenerated_text(normalized_prompt, slide.title, slide.order)[:2000]
        else:
            slide.text_blocks = [
                TextBlock(
                    id=f"prompt-context-{slide.order}",
                    role=TextRole.CALLOUT,
                    label="Prompt Context",
                    text=_build_regenerated_text(normalized_prompt, slide.title, slide.order)[:2000],
                )
            ]
        break
    else:
        raise HTTPException(status_code=404, detail=f"Slide '{slide_id}' not found in current deck.")

    return DesignerService().design_presentation(updated.normalized())


@router.get("/health")
async def health_check(request: Request) -> dict:
    return {
        "status": "ok",
        "ollama_available": getattr(request.app.state, "ollama_available", False),
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/api/semantic-deck", response_model=SemanticPresentation)
async def get_semantic_deck(request: Request) -> SemanticPresentation:
    designer = DesignerService()
    if not hasattr(request.app.state, "semantic_preview_deck"):
        request.app.state.semantic_preview_deck = designer.design_presentation(_build_default_semantic_deck())
    return designer.design_presentation(request.app.state.semantic_preview_deck)


@router.put("/api/semantic-deck", response_model=SemanticPresentation)
async def update_semantic_deck(payload: SemanticPresentation, request: Request) -> SemanticPresentation:
    designed = DesignerService().design_presentation(payload.normalized())
    request.app.state.semantic_preview_deck = designed
    return designed


@router.put("/api/semantic-deck/prompt", response_model=SemanticPresentation)
async def update_semantic_deck_prompt(payload: PromptUpdateRequest, request: Request) -> SemanticPresentation:
    if not hasattr(request.app.state, "semantic_preview_deck"):
        request.app.state.semantic_preview_deck = DesignerService().design_presentation(_build_default_semantic_deck())
    deck: SemanticPresentation = request.app.state.semantic_preview_deck
    updated = deck.model_copy(
        deep=True,
        update={"user_prompt": payload.user_prompt.strip(), "prompt_last_updated_at": _now_iso()},
    )
    designed = DesignerService().design_presentation(updated.normalized())
    request.app.state.semantic_preview_deck = designed
    return designed


@router.post("/api/semantic-deck/regenerate", response_model=SemanticPresentation)
async def regenerate_semantic_deck(payload: RegenerateDeckRequest, request: Request) -> SemanticPresentation:
    if not hasattr(request.app.state, "semantic_preview_deck"):
        request.app.state.semantic_preview_deck = DesignerService().design_presentation(_build_default_semantic_deck())
    deck: SemanticPresentation = request.app.state.semantic_preview_deck
    prompt = payload.user_prompt if payload.user_prompt is not None else deck.user_prompt
    regenerated = _regenerate_semantic_deck(deck, prompt)
    request.app.state.semantic_preview_deck = regenerated
    return regenerated


@router.post("/api/semantic-deck/regenerate-slide", response_model=SemanticPresentation)
async def regenerate_semantic_slide(payload: RegenerateSlideRequest, request: Request) -> SemanticPresentation:
    if not hasattr(request.app.state, "semantic_preview_deck"):
        request.app.state.semantic_preview_deck = DesignerService().design_presentation(_build_default_semantic_deck())
    deck: SemanticPresentation = request.app.state.semantic_preview_deck
    prompt = payload.user_prompt if payload.user_prompt is not None else deck.user_prompt
    regenerated = _regenerate_single_slide(deck, prompt, payload.slide_id)
    request.app.state.semantic_preview_deck = regenerated
    return regenerated


@router.get("/api/projects")
async def list_projects(request: Request) -> dict:
    project_store = _project_store(request)
    projects = [item.__dict__ for item in project_store.list_projects()]
    return {"projects": projects}


@router.get("/api/projects/{project_id}")
async def load_project(project_id: str, request: Request) -> dict:
    project_store = _project_store(request)
    try:
        payload = project_store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    request.app.state.semantic_preview_deck = SemanticPresentation.model_validate(payload["deck"])
    return payload


@router.post("/api/projects")
async def save_project(payload: SaveProjectRequest, request: Request) -> dict:
    project_store = _project_store(request)
    designed = DesignerService().design_presentation(payload.deck)
    return project_store.save_project(payload.name, designed)


@router.get("/api/projects/{project_id}/export/json")
async def export_project_json(project_id: str, request: Request) -> FileResponse:
    project_store = _project_store(request)
    try:
        output = project_store.export_project_json(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(path=output, filename=output.name, media_type="application/json")


@router.get("/api/projects/{project_id}/export/pptx")
async def export_project_pptx(project_id: str, request: Request) -> FileResponse:
    project_store = _project_store(request)
    try:
        output = project_store.export_project_pptx(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path=output,
        filename=Path(output).name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.post("/api/generate", response_model=DeckResponse)
async def generate_slides(payload: DeckRequest, request: Request) -> DeckResponse:
    generation_service: GenerationService = getattr(request.app.state, "generation_service", GenerationService())
    try:
        generated_deck = await generation_service.generate(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    validated_deck = ValidationService().validate(generated_deck)
    rendered_deck = RenderingService().render(validated_deck)
    export_artifacts = ExportService().export(rendered_deck)

    return DeckResponse(deck=rendered_deck, export=export_artifacts)


@router.get("/api/mock-mode/examples")
async def get_mock_examples() -> dict:
    return {
        "prompts": CANNED_SAMPLE_PROMPTS,
        "sample_outputs": DECK_TEMPLATES,
    }
