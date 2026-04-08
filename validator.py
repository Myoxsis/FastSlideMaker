from __future__ import annotations

from typing import List

from pydantic import ValidationError

from schema import Deck, Slide, ValidationResult


DEFAULT_BY_TYPE = {
    "executive_summary": "narrative",
    "process_flow": "flow_steps",
    "swimlane": "lanes",
    "current_vs_target": "comparison",
    "layered_architecture": "layers",
    "integration_map": "links",
    "roadmap": "roadmap_phases",
    "issue_implication_recommendation": "iir",
}


def _normalize_slide(slide: Slide) -> Slide:
    required = DEFAULT_BY_TYPE.get(slide.slide_type)
    if required == "narrative" and not slide.narrative:
        slide.narrative = ["Add summary insight."]
    elif required == "flow_steps" and not slide.flow_steps:
        slide.flow_steps = [
            {"id": "step_1", "title": "Discover", "detail": "Capture current process."}
        ]
    elif required == "lanes" and not slide.lanes:
        slide.lanes = [{"name": "Business", "items": ["Define ownership"]}]
    elif required == "comparison" and not slide.comparison:
        slide.comparison = [
            {"topic": "Operations", "current": "Manual", "target": "Automated"}
        ]
    elif required == "layers" and not slide.layers:
        slide.layers = [{"name": "Experience", "components": ["Portal"]}]
    elif required == "links" and not slide.links:
        slide.systems = slide.systems or ["CRM", "ERP"]
        slide.links = [{"source": "CRM", "target": "ERP", "protocol": "REST"}]
    elif required == "roadmap_phases" and not slide.roadmap_phases:
        slide.roadmap_phases = [
            {"name": "Phase 1", "timeframe": "Q1", "outcomes": ["Foundation"]}
        ]
    elif required == "iir" and not slide.iir:
        slide.iir = [
            {
                "issue": "Fragmented tooling",
                "implication": "Slow cycle time",
                "recommendation": "Standardize platform",
            }
        ]

    return slide


def validate_and_normalize(raw: dict) -> ValidationResult:
    errors: List[str] = []
    try:
        deck = Deck.model_validate(raw)
    except ValidationError as exc:
        for err in exc.errors():
            location = ".".join(str(x) for x in err["loc"])
            errors.append(f"{location}: {err['msg']}")
        return ValidationResult(valid=False, errors=errors)

    normalized_slides = [_normalize_slide(s) for s in deck.slides]
    normalized_deck = deck.model_copy(update={"slides": normalized_slides})
    return ValidationResult(valid=True, normalized_deck=normalized_deck)
