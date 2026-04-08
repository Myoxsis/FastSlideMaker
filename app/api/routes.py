"""HTTP routes for UI, generation, and semantic preview endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.models.schemas import DeckRequest, DeckResponse, MilestoneStatus, SemanticPresentation, SlideType, TextRole
from app.services.export import ExportService
from app.services.generation import GenerationService
from app.services.rendering import RenderingService
from app.services.validation import ValidationService

router = APIRouter()


def _build_default_semantic_deck() -> SemanticPresentation:
    return SemanticPresentation.model_validate(
        {
            "metadata": {
                "title": "Enterprise Delivery Plan",
                "subtitle": "Operational readiness and execution blueprint",
                "audience": "Executive Leadership",
                "purpose": "Align teams on delivery design and milestones",
            },
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


@router.get("/api/semantic-deck", response_model=SemanticPresentation)
async def get_semantic_deck(request: Request) -> SemanticPresentation:
    if not hasattr(request.app.state, "semantic_preview_deck"):
        request.app.state.semantic_preview_deck = _build_default_semantic_deck()
    return request.app.state.semantic_preview_deck


@router.put("/api/semantic-deck", response_model=SemanticPresentation)
async def update_semantic_deck(payload: SemanticPresentation, request: Request) -> SemanticPresentation:
    normalized = payload.normalized()
    request.app.state.semantic_preview_deck = normalized
    return normalized


@router.post("/api/generate", response_model=DeckResponse)
async def generate_slides(payload: DeckRequest, request: Request) -> DeckResponse:
    generation_service: GenerationService = getattr(request.app.state, "generation_service", GenerationService())

    generated_deck = await generation_service.generate(payload)
    validated_deck = ValidationService().validate(generated_deck)
    rendered_deck = RenderingService().render(validated_deck)
    export_artifacts = ExportService().export(rendered_deck)

    return DeckResponse(deck=rendered_deck, export=export_artifacts)
