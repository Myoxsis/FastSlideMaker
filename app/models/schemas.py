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




class FontWeight(str, Enum):
    REGULAR = "regular"
    BOLD = "bold"


class TextAlign(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlign(str, Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class BulletStyle(str, Enum):
    DISC = "disc"
    DASH = "dash"
    NUMBER = "number"


class ElementRole(str, Enum):
    TEXT = "text"
    SHAPE = "shape"
    ICON = "icon"
    DIVIDER = "divider"
    CALLOUT = "callout"
    LEGEND = "legend"
    SECTION_HEADER = "section_header"


class TextStyle(BaseModel):
    font_size: int = Field(default=16, ge=8, le=72)
    font_weight: FontWeight = FontWeight.REGULAR
    italic: bool = False
    text_color: str = Field(default="#111827", max_length=16)
    text_align: TextAlign = TextAlign.LEFT
    vertical_align: VerticalAlign = VerticalAlign.TOP
    line_spacing: float = Field(default=1.2, ge=1.0, le=2.5)
    bullet_style: BulletStyle = BulletStyle.DISC
    padding: int = Field(default=8, ge=0, le=64)
    text_case: str = Field(default="sentence", max_length=16)
    font_family: str = Field(default="Inter", max_length=64)


class ShapeStyle(BaseModel):
    fill_color: str = Field(default="#ffffff", max_length=16)
    border_color: str = Field(default="#94a3b8", max_length=16)
    border_width: float = Field(default=1.0, ge=0.0, le=12.0)
    corner_radius: int = Field(default=0, ge=0, le=999)
    opacity: float = Field(default=1.0, ge=0.1, le=1.0)


class VisualElement(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    type: str = Field(..., min_length=1, max_length=32)
    label: Label | None = None
    x: float = 0.0
    y: float = 0.0
    w: float = 120.0
    h: float = 60.0
    z_index: int = Field(default=1, ge=1, le=500)
    element_role: ElementRole = ElementRole.SHAPE
    style: ShapeStyle = Field(default_factory=ShapeStyle)
    is_user_modified: bool = False
    user_locked: bool = False
    user_modified: bool = False

class TextBlock(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    role: TextRole = TextRole.BODY
    label: Label | None = None
    text: LongText
    style: TextStyle = Field(default_factory=TextStyle)
    user_locked: bool = False
    user_modified: bool = False
    is_user_modified: bool = False


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
    margin_x: int = Field(default=36, ge=0, le=180)
    margin_y: int = Field(default=24, ge=0, le=120)
    spacing_density: str = Field(default="standard", max_length=32)
    template_variant: str = Field(default="default", max_length=64)
    grid_visible: bool = True
    safe_bounds_visible: bool = True
    snap_to_grid: bool = True
    show_guides: bool = True


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
    visual_elements: list[VisualElement] = Field(default_factory=list, max_length=120)
    diagram_data: dict[str, Any] = Field(default_factory=dict)
    user_locked: bool = False
    user_modified: bool = False

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


class PresentationTheme(BaseModel):
    font_family: str = Field(default="Inter", max_length=64)
    palette: list[str] = Field(default_factory=lambda: ["#1f3a8a", "#2563eb", "#0f766e", "#7c3aed", "#111827", "#dc2626"], max_length=16)
    title_preset: str = Field(default="executive", max_length=64)
    diagram_preset: str = Field(default="enterprise", max_length=64)


class SemanticPresentation(BaseModel):
    """Internal source-of-truth representation for renderer/exporter pipelines."""

    metadata: PresentationMetadata
    slides: list[SemanticSlide] = Field(..., min_length=1, max_length=500)
    slide_order: list[str] = Field(..., min_length=1, max_length=500)
    user_prompt: str = Field(default="", max_length=8000)
    prompt_last_updated_at: str | None = None
    theme: PresentationTheme = Field(default_factory=PresentationTheme)

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
        return self.model_copy(
            deep=True,
            update={
                "slides": normalized_slides,
                "user_prompt": self.user_prompt.strip(),
            },
        )


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
