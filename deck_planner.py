from __future__ import annotations

from schema import DeckPlan

DEFAULT_SEQUENCE = [
    "executive_summary",
    "process_flow",
    "swimlane",
    "current_vs_target",
    "layered_architecture",
    "integration_map",
    "roadmap",
    "issue_implication_recommendation",
]


def build_deck_plan(objective: str, slide_count: int) -> DeckPlan:
    slide_types = DEFAULT_SEQUENCE[: slide_count - 1]
    if len(slide_types) < slide_count:
        slide_types.append("roadmap")

    return DeckPlan(
        objective=objective,
        slide_count=slide_count,
        slide_types=slide_types[:slide_count],
    )
