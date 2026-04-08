from app.models.schemas import SemanticPresentation
from app.services.designer import DesignerService, design_semantic_presentation


def _deck_fixture() -> SemanticPresentation:
    return SemanticPresentation.model_validate(
        {
            "metadata": {"title": "Demo"},
            "slide_order": ["s1", "s2"],
            "slides": [
                {
                    "id": "s1",
                    "order": 1,
                    "type": "process",
                    "title": "Process",
                    "process": {
                        "steps": [
                            {"id": "p1", "label": "Discover"},
                            {"id": "p2", "label": "Design"},
                            {"id": "p3", "label": "Build"},
                            {"id": "p4", "label": "Release"},
                            {"id": "p5", "label": "Measure"},
                            {"id": "p6", "label": "Improve"},
                            {"id": "p7", "label": "Optimize"},
                        ]
                    },
                },
                {
                    "id": "s2",
                    "order": 2,
                    "type": "content",
                    "title": "Summary",
                    "text_blocks": [
                        {"id": "t1", "text": "A" * 200},
                        {"id": "t2", "text": "B" * 200},
                    ],
                },
            ],
        }
    )


def test_detect_overlap() -> None:
    service = DesignerService()
    assert service.detect_overlap({"x": 1, "y": 1, "w": 2, "h": 1}, {"x": 2, "y": 1.5, "w": 2, "h": 1})
    assert not service.detect_overlap({"x": 1, "y": 1, "w": 1, "h": 1}, {"x": 3, "y": 3, "w": 1, "h": 1})


def test_resolve_overlap_shift() -> None:
    service = DesignerService()
    resolved = service.resolve_overlap(
        [
            {"x": 1.0, "y": 1.0, "w": 2.0, "h": 1.0},
            {"x": 1.3, "y": 1.2, "w": 2.0, "h": 1.0},
        ],
        strategy="shift",
    )
    assert not service.detect_overlap(resolved[0], resolved[1])


def test_designer_adds_layout_hints_and_diagram_data() -> None:
    designed = design_semantic_presentation(_deck_fixture())

    process = designed.slides[0]
    assert process.layout_hints.grid == "process_rows"
    assert process.layout_hints.overflow_strategy == "split"
    assert process.diagram_data["rows"] == 2

    content = designed.slides[1]
    assert content.layout_hints.grid in {"single_column", "two_column"}
    assert content.layout_hints.element_positions
