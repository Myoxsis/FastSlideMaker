"""Schema, validation, and deck planning logic."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str
    label: str
    type: str = "process"


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    label: str = ""


class Lane(BaseModel):
    id: str
    label: str
    nodes: list[str] = Field(default_factory=list)


class Layer(BaseModel):
    id: str
    label: str
    items: list[str] = Field(default_factory=list)


class Milestone(BaseModel):
    id: str
    label: str
    period: str


class Annotation(BaseModel):
    id: str
    text: str
    target: str


class ContentBlock(BaseModel):
    type: str
    text: str


class DiagramData(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    lanes: list[Lane] = Field(default_factory=list)
    layers: list[Layer] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)


class LayoutHints(BaseModel):
    density: Literal["low", "medium", "high"] = "medium"
    emphasis: str = "headline"


class Slide(BaseModel):
    id: str
    title: str
    objective: str
    slide_type: str
    audience: str
    summary: str
    audience_takeaway: str
    key_entities: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    priority_of_information: list[str] = Field(default_factory=list)
    content_blocks: list[ContentBlock] = Field(default_factory=list)
    diagram_data: DiagramData = Field(default_factory=DiagramData)
    layout_hints: LayoutHints = Field(default_factory=LayoutHints)


class PresentationMeta(BaseModel):
    title: str
    theme: str = "consulting"
    description: str = ""


class Presentation(BaseModel):
    presentation: PresentationMeta
    slides: list[Slide]


def normalize_deck(candidate: dict[str, Any]) -> Presentation:
    """Validate and normalize JSON payload from LLM/mock."""
    deck = Presentation.model_validate(candidate)
    for i, slide in enumerate(deck.slides, start=1):
        if not slide.id:
            slide.id = f"s{i}"
        if len(slide.content_blocks) > 6:
            slide.content_blocks = slide.content_blocks[:6]
    return deck


def select_template_for_slide(slide_type: str) -> str:
    mapping = {
        "process flow": "process_flow",
        "layered architecture": "layered_architecture",
        "roadmap": "roadmap",
    }
    return mapping.get(slide_type, "generic")
