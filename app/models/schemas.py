"""Shared schema objects across generation pipeline stages.

This module keeps the existing API models used by the app while also defining a
semantic source-of-truth schema for richer slide generation/rendering/export.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator


Label = Annotated[str, Field(min_length=1, max_length=80)]
ShortText = Annotated[str, Field(min_length=1, max_length=280)]
LongText = Annotated[str, Field(min_length=1, max_length=2000)]


class SlideType(str, Enum):
    TITLE = "title"
    AGENDA = "agenda"
    SECTION_BREAK = "section_break"
    CONTENT = "content"
    DIAGRAM = "diagram"
    PROCESS = "process"
    SWIMLANE = "swimlane"
    ARCHITECTURE = "architecture"
    INTEGRATIONS = "integrations"
    ROADMAP = "roadmap"
    ISSUE_IMPLICATION_RECOMMENDATION = "issue_implication_recommendation"
    SUMMARY = "summary"


class TextRole(str, Enum):
    HEADLINE = "headline"
    BODY = "body"
    BULLET = "bullet"
    CALLOUT = "callout"
    METRIC = "metric"
    FOOTNOTE = "footnote"


class ConnectorStyle(str, Enum):
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


class MilestoneStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    AT_RISK = "at_risk"
    COMPLETE = "complete"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TextBlock(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    role: TextRole = TextRole.BODY
    label: Label | None = None
    text: LongText


class DiagramNode(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    label: Label
    description: ShortText | None = None
    category: Label | None = None


class DiagramEdge(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=64)
    target_id: str = Field(..., min_length=1, max_length=64)
    label: Label | None = None
    style: ConnectorStyle = ConnectorStyle.SOLID


class DiagramContent(BaseModel):
    nodes: list[DiagramNode] = Field(default_factory=list, max_length=30)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_references(self) -> "DiagramContent":
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                raise ValueError("Diagram edge references unknown node id.")
        return self


class ProcessStep(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    label: Label
    description: ShortText | None = None
    owner: Label | None = None
    outputs: list[Label] = Field(default_factory=list, max_length=8)


class ProcessContent(BaseModel):
    steps: list[ProcessStep] = Field(..., min_length=2, max_length=12)


class SwimlaneItem(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    label: Label
    detail: ShortText | None = None


class Swimlane(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    lane_label: Label
    items: list[SwimlaneItem] = Field(default_factory=list, max_length=12)


class SwimlaneContent(BaseModel):
    lanes: list[Swimlane] = Field(..., min_length=2, max_length=8)


class Integration(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    system: Label
    purpose: ShortText
    direction: Label = Field(default="bidirectional", max_length=24)
    protocol: Label | None = None


class ArchitectureLayer(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: Label
    responsibility: ShortText
    components: list[Label] = Field(default_factory=list, max_length=12)


class ArchitectureContent(BaseModel):
    layers: list[ArchitectureLayer] = Field(..., min_length=2, max_length=10)
    integrations: list[Integration] = Field(default_factory=list, max_length=20)


class Milestone(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    label: Label
    status: MilestoneStatus = MilestoneStatus.PLANNED
    target_period: Label = Field(..., max_length=32)


class RoadmapPhase(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: Label
    objective: ShortText
    milestones: list[Milestone] = Field(default_factory=list, max_length=10)


class RoadmapContent(BaseModel):
    phases: list[RoadmapPhase] = Field(..., min_length=1, max_length=8)


class IssueBlock(BaseModel):
    issue: LongText
    implication: LongText
    recommendation: LongText
    priority: RecommendationPriority = RecommendationPriority.MEDIUM


class IssueImplicationRecommendationContent(BaseModel):
    blocks: list[IssueBlock] = Field(..., min_length=1, max_length=6)




class LayoutHints(BaseModel):
    """Deterministic layout hints produced by the designer phase."""

    grid: str = Field(default="single_column", max_length=64)
    spacing: str = Field(default="normal", max_length=64)
    element_positions: dict[str, dict[str, float | int | str]] = Field(default_factory=dict)
    overflow_strategy: str = Field(default="wrap", max_length=64)
    grouping: str = Field(default="none", max_length=120)


class SemanticSlide(BaseModel):
    """Semantic slide definition with no coordinate/layout coupling."""

    id: str = Field(..., min_length=1, max_length=64)
    order: int = Field(..., ge=1, le=500)
    type: SlideType
    title: Label
    objective: ShortText | None = None

    text_blocks: list[TextBlock] = Field(default_factory=list, max_length=12)
    diagram: DiagramContent | None = None
    process: ProcessContent | None = None
    swimlanes: SwimlaneContent | None = None
    architecture: ArchitectureContent | None = None
    integrations: list[Integration] = Field(default_factory=list, max_length=20)
    roadmap: RoadmapContent | None = None
    issue_implication_recommendation: IssueImplicationRecommendationContent | None = None
    layout_hints: LayoutHints = Field(default_factory=LayoutHints)
    diagram_data: dict[str, Any] = Field(default_factory=dict)

    MAX_TEXT_CHARS: int = 1200
    MAX_DENSITY_ITEMS: int = 24

    @model_validator(mode="after")
    def validate_type_requirements(self) -> "SemanticSlide":
        requirements: dict[SlideType, tuple[str, ...]] = {
            SlideType.DIAGRAM: ("diagram",),
            SlideType.PROCESS: ("process",),
            SlideType.SWIMLANE: ("swimlanes",),
            SlideType.ARCHITECTURE: ("architecture",),
            SlideType.INTEGRATIONS: ("integrations",),
            SlideType.ROADMAP: ("roadmap",),
            SlideType.ISSUE_IMPLICATION_RECOMMENDATION: ("issue_implication_recommendation",),
        }

        for required_field in requirements.get(self.type, tuple()):
            value = getattr(self, required_field)
            if value in (None, [], {}):
                raise ValueError(f"Slide type '{self.type.value}' requires field '{required_field}'.")

        if not any(
            [
                self.text_blocks,
                self.diagram,
                self.process,
                self.swimlanes,
                self.architecture,
                self.integrations,
                self.roadmap,
                self.issue_implication_recommendation,
            ]
        ):
            raise ValueError("Slide must include at least one semantic content block.")

        text_chars = len(self.title) + sum(len(block.text) + len(block.label or "") for block in self.text_blocks)
        if text_chars > self.MAX_TEXT_CHARS:
            raise ValueError(f"Slide text density too high ({text_chars} chars > {self.MAX_TEXT_CHARS}).")

        density = len(self.text_blocks)
        density += len(self.process.steps) if self.process else 0
        density += len(self.swimlanes.lanes) if self.swimlanes else 0
        density += len(self.architecture.layers) if self.architecture else 0
        density += len(self.integrations)
        density += len(self.roadmap.phases) if self.roadmap else 0
        density += len(self.issue_implication_recommendation.blocks) if self.issue_implication_recommendation else 0
        density += len(self.diagram.nodes) if self.diagram else 0

        if density > self.MAX_DENSITY_ITEMS:
            raise ValueError(f"Slide content density too high ({density} items > {self.MAX_DENSITY_ITEMS}).")

        return self

    def normalized(self) -> "SemanticSlide":
        """Return a normalized copy with trimmed labels/text and sorted integrations."""

        return self.model_copy(
            deep=True,
            update={
                "title": self.title.strip(),
                "text_blocks": [
                    block.model_copy(
                        update={
                            "label": block.label.strip() if block.label else None,
                            "text": " ".join(block.text.split()),
                        }
                    )
                    for block in self.text_blocks
                ],
                "layout_hints": self.layout_hints.model_copy(deep=True),
                "diagram_data": dict(self.diagram_data),
                "integrations": sorted(self.integrations, key=lambda item: (item.system.lower(), item.id)),
            },
        )


class PresentationMetadata(BaseModel):
    title: Label
    subtitle: ShortText | None = None
    subject: Label | None = None
    audience: Label | None = None
    purpose: ShortText | None = None
    author: Label | None = None
    language: Label = Field(default="en-US", max_length=10)
    version: Label = Field(default="1.0", max_length=16)
    tags: list[Label] = Field(default_factory=list, max_length=20)


class SemanticPresentation(BaseModel):
    """Internal source-of-truth representation for renderer/exporter pipelines."""

    metadata: PresentationMetadata
    slides: list[SemanticSlide] = Field(..., min_length=1, max_length=500)
    slide_order: list[str] = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_slide_order(self) -> "SemanticPresentation":
        slide_ids = [slide.id for slide in self.slides]

        if len(set(slide_ids)) != len(slide_ids):
            raise ValueError("Slide ids must be unique.")
        if len(set(self.slide_order)) != len(self.slide_order):
            raise ValueError("slide_order contains duplicate ids.")

        if set(slide_ids) != set(self.slide_order):
            raise ValueError("slide_order must contain every slide id exactly once.")

        expected_orders = list(range(1, len(self.slides) + 1))
        actual_orders = sorted(slide.order for slide in self.slides)
        if actual_orders != expected_orders:
            raise ValueError("Slide.order must be contiguous and start at 1.")

        return self

    def normalized(self) -> "SemanticPresentation":
        normalized_slides = [slide.normalized() for slide in self.slides]
        normalized_slides.sort(key=lambda item: self.slide_order.index(item.id))
        return self.model_copy(deep=True, update={"slides": normalized_slides})


# -----------------------
# Existing app API models
# -----------------------


class DeckRequest(BaseModel):
    topic: str = Field(..., description="Topic for the generated presentation.")
    audience: str = Field(default="General", description="Target audience.")
    tone: str = Field(default="Professional", description="Narrative tone.")
    slide_count: int = Field(default=6, ge=3, le=30)


class Slide(BaseModel):
    title: str
    bullets: list[str]
    notes: str | None = None


class Deck(BaseModel):
    title: str
    theme: str = "clean-blue"
    slides: list[Slide]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeckResponse(BaseModel):
    deck: Deck
    export: dict[str, Any]
