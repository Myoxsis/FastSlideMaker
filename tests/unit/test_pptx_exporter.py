from pathlib import Path

import pytest

pytest.importorskip("pptx")

from app.models.schemas import SemanticPresentation
from app.services.pptx_exporter import export_semantic_deck_to_pptx


def _semantic_fixture() -> SemanticPresentation:
    return SemanticPresentation.model_validate(
        {
            "metadata": {"title": "Delivery Plan", "audience": "Leadership", "purpose": "Execution alignment"},
            "slide_order": ["process-flow", "team-handoffs", "layered-architecture", "roadmap"],
            "slides": [
                {
                    "id": "process-flow",
                    "order": 1,
                    "type": "process",
                    "title": "Process Flow",
                    "objective": "Sequence core execution phases.",
                    "process": {
                        "steps": [
                            {"id": "s1", "label": "Discover", "description": "Gather requirements", "owner": "Product"},
                            {"id": "s2", "label": "Design", "description": "Define architecture", "owner": "Architecture"},
                            {"id": "s3", "label": "Build", "description": "Implement and validate", "owner": "Engineering"},
                        ]
                    },
                },
                {
                    "id": "team-handoffs",
                    "order": 2,
                    "type": "swimlane",
                    "title": "Cross-Team Handoffs",
                    "objective": "Clarify responsibilities across delivery lanes.",
                    "swimlanes": {
                        "lanes": [
                            {
                                "id": "lane-1",
                                "lane_label": "Product",
                                "items": [
                                    {"id": "item-1", "label": "Define scope", "detail": "Backlog and acceptance criteria"},
                                    {"id": "item-2", "label": "Approve priorities"},
                                ],
                            },
                            {
                                "id": "lane-2",
                                "lane_label": "Engineering",
                                "items": [
                                    {"id": "item-3", "label": "Implement sprint plan"},
                                    {"id": "item-4", "label": "Ship release candidate", "detail": "Validate quality gates"},
                                ],
                            },
                        ]
                    },
                },
                {
                    "id": "layered-architecture",
                    "order": 3,
                    "type": "architecture",
                    "title": "Layered Architecture",
                    "objective": "Separate concerns cleanly.",
                    "architecture": {
                        "layers": [
                            {
                                "id": "l1",
                                "name": "Experience",
                                "responsibility": "UI and interactions",
                                "components": ["Web UI", "Editor"],
                            },
                            {
                                "id": "l2",
                                "name": "Application",
                                "responsibility": "Business logic and orchestration",
                                "components": ["Planner", "Validation"],
                            },
                        ]
                    },
                },
                {
                    "id": "roadmap",
                    "order": 4,
                    "type": "roadmap",
                    "title": "Roadmap",
                    "objective": "Track phased delivery milestones.",
                    "roadmap": {
                        "phases": [
                            {
                                "id": "p1",
                                "name": "Q2",
                                "objective": "Foundation",
                                "milestones": [
                                    {
                                        "id": "m1",
                                        "label": "Schema finalized",
                                        "target_period": "Apr 2026",
                                        "status": "complete",
                                    }
                                ],
                            },
                            {
                                "id": "p2",
                                "name": "Q3",
                                "objective": "Scale",
                                "milestones": [
                                    {
                                        "id": "m2",
                                        "label": "Template expansion",
                                        "target_period": "Jul 2026",
                                        "status": "planned",
                                    }
                                ],
                            },
                        ]
                    },
                },
            ],
        }
    )


def test_export_semantic_deck_to_pptx_creates_file(tmp_path: Path) -> None:
    semantic = _semantic_fixture()
    output = tmp_path / "semantic_export.pptx"

    exported = export_semantic_deck_to_pptx(semantic, output)

    assert exported == output
    assert output.exists()
    assert output.stat().st_size > 0
