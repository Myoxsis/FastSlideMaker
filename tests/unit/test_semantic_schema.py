from app.models.schemas import (
    DiagramContent,
    DiagramEdge,
    DiagramNode,
    Integration,
    PresentationMetadata,
    RecommendationPriority,
    RoadmapContent,
    RoadmapPhase,
    SemanticPresentation,
    SemanticSlide,
    SlideType,
    TextBlock,
    TextRole,
)


def test_semantic_presentation_slide_order_validation() -> None:
    slide_1 = SemanticSlide(
        id="s1",
        order=1,
        type=SlideType.CONTENT,
        title="Overview",
        text_blocks=[TextBlock(id="t1", role=TextRole.BULLET, text="Point A")],
    )
    slide_2 = SemanticSlide(
        id="s2",
        order=2,
        type=SlideType.INTEGRATIONS,
        title="Integrations",
        integrations=[
            Integration(id="i1", system="CRM", purpose="Sync customer profiles"),
        ],
    )

    deck = SemanticPresentation(
        metadata=PresentationMetadata(title="Demo"),
        slides=[slide_1, slide_2],
        slide_order=["s1", "s2"],
    )

    assert len(deck.slides) == 2


def test_diagram_slide_requires_diagram_content() -> None:
    try:
        SemanticSlide(
            id="s1",
            order=1,
            type=SlideType.DIAGRAM,
            title="System Flow",
            text_blocks=[TextBlock(id="tx", text="Helper text")],
        )
        assert False, "Expected validation error"
    except ValueError:
        assert True


def test_diagram_edge_references_existing_nodes() -> None:
    diagram = DiagramContent(
        nodes=[DiagramNode(id="n1", label="Client"), DiagramNode(id="n2", label="API")],
        edges=[DiagramEdge(source_id="n1", target_id="n2", label="Calls")],
    )

    slide = SemanticSlide(
        id="s1",
        order=1,
        type=SlideType.DIAGRAM,
        title="Interaction Diagram",
        diagram=diagram,
    )

    assert slide.diagram is not None
    assert len(slide.diagram.nodes) == 2


def test_normalization_sorts_integrations_and_trims_text() -> None:
    slide = SemanticSlide(
        id="s1",
        order=1,
        type=SlideType.INTEGRATIONS,
        title=" Integrations ",
        text_blocks=[TextBlock(id="t1", role=TextRole.BODY, label=" Label ", text="A   B   C")],
        integrations=[
            Integration(id="i2", system="Zeta", purpose="Z sync"),
            Integration(id="i1", system="Alpha", purpose="A sync"),
        ],
    )

    normalized = slide.normalized()

    assert normalized.title == "Integrations"
    assert normalized.text_blocks[0].label == "Label"
    assert normalized.text_blocks[0].text == "A B C"
    assert [i.system for i in normalized.integrations] == ["Alpha", "Zeta"]


def test_issue_priority_enum_value() -> None:
    assert RecommendationPriority.CRITICAL.value == "critical"


def test_roadmap_slide_supports_phases_and_milestones() -> None:
    roadmap = RoadmapContent(
        phases=[
            RoadmapPhase(
                id="p1",
                name="Foundation",
                objective="Establish base platform",
                milestones=[],
            )
        ]
    )

    slide = SemanticSlide(
        id="s1",
        order=1,
        type=SlideType.ROADMAP,
        title="Roadmap",
        roadmap=roadmap,
    )

    assert slide.roadmap is not None
    assert slide.roadmap.phases[0].name == "Foundation"
