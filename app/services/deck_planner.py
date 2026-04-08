"""Build concise deck plans from interpreted request metadata."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.request_interpreter import RequestInterpretation, RequestInterpreter


@dataclass(frozen=True, slots=True)
class SlidePlanItem:
    order: int
    title: str
    objective: str
    visual_type: str


@dataclass(frozen=True, slots=True)
class DeckPlan:
    deck_title: str
    deck_summary: str
    ordered_slide_plan: list[SlidePlanItem]


class DeckPlanner:
    """Deterministic planner designed for structured, concise deck outputs."""

    def __init__(self, interpreter: RequestInterpreter | None = None) -> None:
        self._interpreter = interpreter or RequestInterpreter()

    def plan_from_request(self, request: str) -> DeckPlan:
        interpretation = self._interpreter.interpret(request)
        return self.plan_from_interpretation(interpretation)

    def plan_from_interpretation(self, interpretation: RequestInterpretation) -> DeckPlan:
        title = self._build_title(interpretation)
        summary = self._build_summary(interpretation)
        slide_types = self._expand_slide_types(
            interpretation.recommended_slide_types,
            interpretation.likely_slide_count,
        )

        slides = [
            SlidePlanItem(
                order=index,
                title=self._slide_title(slide_type, interpretation, index),
                objective=self._slide_objective(slide_type, interpretation),
                visual_type=self._visual_for_slide(slide_type),
            )
            for index, slide_type in enumerate(slide_types, start=1)
        ]

        return DeckPlan(deck_title=title, deck_summary=summary, ordered_slide_plan=slides)

    def _build_title(self, data: RequestInterpretation) -> str:
        if data.request_kind == "comparison":
            return f"{data.topic}: Options and Recommendation"
        if data.request_kind == "roadmap":
            return f"{data.topic}: Delivery Roadmap"
        if data.request_kind in {"architecture", "mixed"}:
            return f"{data.topic}: Target Process and Architecture"
        return f"{data.topic}: Execution Plan"

    def _build_summary(self, data: RequestInterpretation) -> str:
        return (
            f"Objective: {data.deck_objective} "
            f"Tone: {data.tone}. "
            f"Plan: {data.likely_slide_count} slides for {data.audience}."
        )

    def _expand_slide_types(self, recommended: list[str], target_count: int) -> list[str]:
        if not recommended:
            recommended = ["title", "agenda", "content", "summary"]

        slides = list(recommended)
        while len(slides) < target_count:
            insert_at = max(2, len(slides) - 1)
            slides.insert(insert_at, "content")

        return slides[:target_count]

    def _slide_title(self, slide_type: str, data: RequestInterpretation, order: int) -> str:
        mapping = {
            "title": data.deck_objective.split(".")[0],
            "agenda": "Agenda",
            "content": f"Key Decision Area {order}",
            "process": "Current vs Target Process",
            "swimlane": "Roles and Handoffs",
            "architecture": "Target Architecture",
            "integrations": "Integration Design",
            "roadmap": "Phased Roadmap",
            "diagram": "Decision Framework",
            "issue_implication_recommendation": "Issues, Implications, Recommendations",
            "summary": "Summary and Next Steps",
        }
        return mapping.get(slide_type, f"Slide {order}")

    def _slide_objective(self, slide_type: str, data: RequestInterpretation) -> str:
        objective_map = {
            "title": f"Frame decision context for {data.audience}.",
            "agenda": "Set flow and expected outcomes.",
            "content": "Highlight core facts and constraints.",
            "process": "Show sequence, ownership, and outputs.",
            "swimlane": "Clarify cross-team accountability.",
            "architecture": "Explain layers, responsibilities, and components.",
            "integrations": "Specify interfaces, purpose, and direction.",
            "roadmap": "Sequence phases, milestones, and risks.",
            "diagram": "Visualize option structure and dependencies.",
            "issue_implication_recommendation": "Drive decision with issue-impact-action logic.",
            "summary": "Confirm recommendation and immediate actions.",
        }
        return objective_map.get(slide_type, "Support the deck objective.")

    def _visual_for_slide(self, slide_type: str) -> str:
        visual_map = {
            "title": "hero title",
            "agenda": "numbered list",
            "content": "bulleted content",
            "process": "process flow",
            "swimlane": "swimlane chart",
            "architecture": "layered architecture diagram",
            "integrations": "system context diagram",
            "roadmap": "timeline roadmap",
            "diagram": "matrix or node-link diagram",
            "issue_implication_recommendation": "3-column issue-impact-action",
            "summary": "key takeaways panel",
        }
        return visual_map.get(slide_type, "bulleted content")
