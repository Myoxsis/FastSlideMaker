"""Single-slide semantic generator with validation, repair, and normalization."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.models.schemas import (
    ArchitectureContent,
    ArchitectureLayer,
    DiagramContent,
    DiagramEdge,
    DiagramNode,
    Integration,
    IssueBlock,
    IssueImplicationRecommendationContent,
    Milestone,
    ProcessContent,
    ProcessStep,
    RecommendationPriority,
    RoadmapContent,
    RoadmapPhase,
    SemanticSlide,
    SlideType,
    Swimlane,
    SwimlaneContent,
    SwimlaneItem,
    TextBlock,
    TextRole,
)
from app.services.deck_planner import SlidePlanItem
from app.services.llm_client import OllamaLLMClient
from app.utils.json_utils import extract_json_object


class SlideGenerator:
    """Generates exactly one validated semantic slide for plan/regeneration workflows."""

    def __init__(self, llm_client: OllamaLLMClient | None = None) -> None:
        self._llm = llm_client or OllamaLLMClient()

    async def generate_semantic_slide(
        self,
        *,
        deck_context: str,
        current_slide_objective: str,
        selected_slide_type: SlideType | str,
        slide_id: str,
        order: int,
        title: str | None = None,
    ) -> SemanticSlide:
        """Generate and validate a single semantic slide."""
        slide_type = self._coerce_type(selected_slide_type)
        raw = await self._llm.generate_slide_json(
            plan_json=self._build_prompt_payload(deck_context, current_slide_objective, slide_type, slide_id, order, title),
            slide_count=1,
        )

        parsed = self._parse_json(raw)
        if parsed is None:
            parsed = await self._repair_and_parse(raw, slide_type)

        semantic_json = self._extract_slide_payload(
            parsed,
            slide_id=slide_id,
            order=order,
            title=title,
            objective=current_slide_objective,
            slide_type=slide_type,
        )

        normalized_json = self._normalize_slide_json(semantic_json, slide_type)
        return self._validate_or_fallback(normalized_json, slide_id, order, title or "Slide", current_slide_objective, slide_type)

    async def regenerate_semantic_slide(
        self,
        *,
        deck_context: str,
        slide_plan_item: SlidePlanItem,
    ) -> SemanticSlide:
        """Regenerate exactly one slide using existing plan metadata."""
        return await self.generate_semantic_slide(
            deck_context=deck_context,
            current_slide_objective=slide_plan_item.objective,
            selected_slide_type=slide_plan_item.visual_type.replace(" ", "_").replace("-", "_"),
            slide_id=f"s{slide_plan_item.order}",
            order=slide_plan_item.order,
            title=slide_plan_item.title,
        )

    def _build_prompt_payload(
        self,
        deck_context: str,
        objective: str,
        slide_type: SlideType,
        slide_id: str,
        order: int,
        title: str | None,
    ) -> str:
        prompt = {
            "task": "generate_single_semantic_slide",
            "must_return": "valid json for exactly one slide object",
            "deck_context": deck_context,
            "current_slide_objective": objective,
            "selected_slide_type": slide_type.value,
            "constraints": {
                "exactly_one_slide": True,
                "keep_terminology_consistent_with_deck": True,
                "text_concise_for_presentations": True,
                "diagram_data_must_be_meaningful_and_exportable": True,
            },
            "target_slide": {
                "id": slide_id,
                "order": order,
                "title": title or "",
                "type": slide_type.value,
            },
        }
        return json.dumps(prompt)

    async def _repair_and_parse(self, raw: str, slide_type: SlideType) -> dict[str, Any]:
        repaired = await self._llm.repair_json(
            malformed_json=raw,
            expected_shape_hint=(
                '{"id":"s1","order":1,"type":"%s","title":"...","objective":"..."}' % slide_type.value
            ),
        )
        repaired_parsed = self._parse_json(repaired)
        if repaired_parsed is None:
            raise ValueError("LLM output could not be parsed, even after repair.")
        return repaired_parsed

    def _parse_json(self, payload: str) -> dict[str, Any] | None:
        return extract_json_object(payload)

    def _extract_slide_payload(
        self,
        parsed: dict[str, Any],
        *,
        slide_id: str,
        order: int,
        title: str | None,
        objective: str,
        slide_type: SlideType,
    ) -> dict[str, Any]:
        if isinstance(parsed.get("slide"), dict):
            candidate = dict(parsed["slide"])
        elif isinstance(parsed.get("slides"), list) and parsed["slides"]:
            candidate = dict(parsed["slides"][0])
        else:
            candidate = dict(parsed)

        candidate.setdefault("id", slide_id)
        candidate.setdefault("order", order)
        candidate.setdefault("title", title or "Slide")
        candidate.setdefault("objective", objective)
        candidate["type"] = self._coerce_type(candidate.get("type", slide_type.value)).value
        return candidate

    def _normalize_slide_json(self, slide_json: dict[str, Any], slide_type: SlideType) -> dict[str, Any]:
        slide = dict(slide_json)
        slide["title"] = self._trim_text(str(slide.get("title", "Slide")), 80)
        slide["objective"] = self._trim_text(str(slide.get("objective", "")), 280)

        text_blocks = slide.get("text_blocks") or []
        if isinstance(text_blocks, list):
            normalized_blocks: list[dict[str, Any]] = []
            for index, block in enumerate(text_blocks[:8], start=1):
                if not isinstance(block, dict):
                    continue
                text = self._trim_text(str(block.get("text", "")), 240)
                if not text:
                    continue
                normalized_blocks.append(
                    {
                        "id": block.get("id") or f"tb{index}",
                        "role": block.get("role") or TextRole.BULLET.value,
                        "label": self._trim_text(str(block.get("label", "")), 40) or None,
                        "text": text,
                    }
                )
            slide["text_blocks"] = normalized_blocks

        slide = self._ensure_type_specific_content(slide, slide_type)
        return slide

    def _ensure_type_specific_content(self, slide: dict[str, Any], slide_type: SlideType) -> dict[str, Any]:
        objective = str(slide.get("objective") or "")
        title = str(slide.get("title") or "")

        if slide_type == SlideType.DIAGRAM and not slide.get("diagram"):
            slide["diagram"] = {
                "nodes": [
                    {"id": "n1", "label": self._trim_text(title or "Context", 40)},
                    {"id": "n2", "label": self._trim_text(objective or "Outcome", 40)},
                ],
                "edges": [{"source_id": "n1", "target_id": "n2", "label": "drives", "style": "solid"}],
            }
        elif slide_type == SlideType.PROCESS and not slide.get("process"):
            slide["process"] = {
                "steps": [
                    {"id": "p1", "label": "Input", "description": self._trim_text(objective, 120), "outputs": ["Brief"]},
                    {"id": "p2", "label": "Decision", "description": "Select path", "outputs": ["Next step"]},
                ]
            }
        elif slide_type == SlideType.SWIMLANE and not slide.get("swimlanes"):
            slide["swimlanes"] = {
                "lanes": [
                    {"id": "l1", "lane_label": "Business", "items": [{"id": "i1", "label": "Define need"}]},
                    {"id": "l2", "lane_label": "Technology", "items": [{"id": "i2", "label": "Implement"}]},
                ]
            }
        elif slide_type == SlideType.ARCHITECTURE and not slide.get("architecture"):
            slide["architecture"] = {
                "layers": [
                    {"id": "a1", "name": "Experience", "responsibility": "User entry point", "components": ["UI"]},
                    {"id": "a2", "name": "Core Services", "responsibility": "Business logic", "components": ["API"]},
                ],
                "integrations": [],
            }
        elif slide_type == SlideType.INTEGRATIONS and not slide.get("integrations"):
            slide["integrations"] = [
                {"id": "int1", "system": "Source System", "purpose": "Provide input data", "direction": "inbound"}
            ]
        elif slide_type == SlideType.ROADMAP and not slide.get("roadmap"):
            slide["roadmap"] = {
                "phases": [
                    {
                        "id": "r1",
                        "name": "Phase 1",
                        "objective": self._trim_text(objective or "Establish baseline", 120),
                        "milestones": [{"id": "m1", "label": "Kickoff", "target_period": "Q1", "status": "planned"}],
                    }
                ]
            }
        elif slide_type == SlideType.ISSUE_IMPLICATION_RECOMMENDATION and not slide.get("issue_implication_recommendation"):
            slide["issue_implication_recommendation"] = {
                "blocks": [
                    {
                        "issue": self._trim_text(objective or "Issue not specified", 200),
                        "implication": "Delivery risk increases.",
                        "recommendation": "Approve a focused mitigation plan.",
                        "priority": "high",
                    }
                ]
            }

        return slide

    def _validate_or_fallback(
        self,
        slide_json: dict[str, Any],
        slide_id: str,
        order: int,
        title: str,
        objective: str,
        slide_type: SlideType,
    ) -> SemanticSlide:
        try:
            return SemanticSlide.model_validate(slide_json).normalized()
        except ValidationError:
            return self._fallback_slide(slide_id, order, title, objective, slide_type).normalized()

    def _fallback_slide(
        self,
        slide_id: str,
        order: int,
        title: str,
        objective: str,
        slide_type: SlideType,
    ) -> SemanticSlide:
        base = {
            "id": slide_id,
            "order": order,
            "type": slide_type,
            "title": self._trim_text(title or "Slide", 80),
            "objective": self._trim_text(objective, 280),
            "text_blocks": [
                TextBlock(
                    id="tb1",
                    role=TextRole.BULLET,
                    text=self._trim_text(objective or "Key message", 200),
                )
            ],
        }

        if slide_type == SlideType.DIAGRAM:
            base["diagram"] = DiagramContent(
                nodes=[DiagramNode(id="n1", label="Start"), DiagramNode(id="n2", label="Outcome")],
                edges=[DiagramEdge(source_id="n1", target_id="n2", label="flow")],
            )
        elif slide_type == SlideType.PROCESS:
            base["process"] = ProcessContent(
                steps=[
                    ProcessStep(id="p1", label="Assess", outputs=["Findings"]),
                    ProcessStep(id="p2", label="Execute", outputs=["Result"]),
                ]
            )
        elif slide_type == SlideType.SWIMLANE:
            base["swimlanes"] = SwimlaneContent(
                lanes=[
                    Swimlane(id="l1", lane_label="Business", items=[SwimlaneItem(id="i1", label="Define")]),
                    Swimlane(id="l2", lane_label="IT", items=[SwimlaneItem(id="i2", label="Deliver")]),
                ]
            )
        elif slide_type == SlideType.ARCHITECTURE:
            base["architecture"] = ArchitectureContent(
                layers=[
                    ArchitectureLayer(id="a1", name="Channel", responsibility="User interaction", components=["Web"]),
                    ArchitectureLayer(id="a2", name="Services", responsibility="Core logic", components=["API"]),
                ],
                integrations=[],
            )
        elif slide_type == SlideType.INTEGRATIONS:
            base["integrations"] = [
                Integration(id="int1", system="System A", purpose="Data sync", direction="bidirectional")
            ]
        elif slide_type == SlideType.ROADMAP:
            base["roadmap"] = RoadmapContent(
                phases=[
                    RoadmapPhase(
                        id="r1",
                        name="Foundation",
                        objective="Stabilize prerequisites",
                        milestones=[Milestone(id="m1", label="Kickoff", target_period="Q1")],
                    )
                ]
            )
        elif slide_type == SlideType.ISSUE_IMPLICATION_RECOMMENDATION:
            base["issue_implication_recommendation"] = IssueImplicationRecommendationContent(
                blocks=[
                    IssueBlock(
                        issue=self._trim_text(objective or "Issue", 200),
                        implication="Impacts delivery confidence.",
                        recommendation="Approve mitigation workstream.",
                        priority=RecommendationPriority.HIGH,
                    )
                ]
            )

        return SemanticSlide.model_validate(base)

    def _coerce_type(self, slide_type: SlideType | str) -> SlideType:
        if isinstance(slide_type, SlideType):
            return slide_type
        cleaned = str(slide_type).strip().lower().replace(" ", "_").replace("-", "_")
        visual_map = {
            "hero_title": SlideType.TITLE,
            "numbered_list": SlideType.AGENDA,
            "bulleted_content": SlideType.CONTENT,
            "process_flow": SlideType.PROCESS,
            "swimlane_chart": SlideType.SWIMLANE,
            "layered_architecture_diagram": SlideType.ARCHITECTURE,
            "system_context_diagram": SlideType.INTEGRATIONS,
            "timeline_roadmap": SlideType.ROADMAP,
            "matrix_or_node_link_diagram": SlideType.DIAGRAM,
            "3_column_issue_impact_action": SlideType.ISSUE_IMPLICATION_RECOMMENDATION,
            "key_takeaways_panel": SlideType.SUMMARY,
        }
        return visual_map.get(cleaned, SlideType(cleaned) if cleaned in SlideType._value2member_map_ else SlideType.CONTENT)

    def _trim_text(self, value: str, max_len: int) -> str:
        compact = " ".join(value.split())
        if len(compact) <= max_len:
            return compact
        return compact[: max_len - 1].rstrip() + "…"
