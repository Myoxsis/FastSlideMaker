from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SlideType = Literal[
    "executive_summary",
    "process_flow",
    "swimlane",
    "current_vs_target",
    "layered_architecture",
    "integration_map",
    "roadmap",
    "issue_implication_recommendation",
]


class FlowStep(BaseModel):
    id: str
    title: str
    detail: str = ""


class Lane(BaseModel):
    name: str
    items: List[str] = Field(default_factory=list)


class ComparisonItem(BaseModel):
    topic: str
    current: str
    target: str


class ArchitectureLayer(BaseModel):
    name: str
    components: List[str] = Field(default_factory=list)


class IntegrationLink(BaseModel):
    source: str
    target: str
    protocol: str = "API"


class RoadmapPhase(BaseModel):
    name: str
    timeframe: str
    outcomes: List[str] = Field(default_factory=list)


class IIRItem(BaseModel):
    issue: str
    implication: str
    recommendation: str


class Slide(BaseModel):
    id: str
    slide_type: SlideType
    title: str
    subtitle: str = ""
    narrative: List[str] = Field(default_factory=list)
    flow_steps: List[FlowStep] = Field(default_factory=list)
    lanes: List[Lane] = Field(default_factory=list)
    comparison: List[ComparisonItem] = Field(default_factory=list)
    layers: List[ArchitectureLayer] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)
    links: List[IntegrationLink] = Field(default_factory=list)
    roadmap_phases: List[RoadmapPhase] = Field(default_factory=list)
    iir: List[IIRItem] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class DeckPlan(BaseModel):
    objective: str
    audience: str = "Business and IT stakeholders"
    slide_count: int
    slide_types: List[SlideType]


class Deck(BaseModel):
    request: str
    model: str
    plan: DeckPlan
    slides: List[Slide]
    warnings: List[str] = Field(default_factory=list)


class GenerationRequest(BaseModel):
    prompt: str
    model: str = "llama3"


class GenerationResponse(BaseModel):
    project_id: str
    deck: Deck


class ProjectRecord(BaseModel):
    project_id: str
    created_at: str
    deck: Deck


class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    normalized_deck: Optional[Deck] = None
