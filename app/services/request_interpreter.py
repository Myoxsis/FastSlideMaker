"""Interpret a free-form deck request into structured planning signals."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

RequestCategory = Literal["process", "architecture", "roadmap", "comparison", "mixed"]


@dataclass(frozen=True, slots=True)
class RequestInterpretation:
    topic: str
    audience: str
    deck_objective: str
    likely_slide_count: int
    recommended_slide_types: list[str]
    tone: str
    request_kind: RequestCategory


class RequestInterpreter:
    """Rule-based request interpreter with pragmatic enterprise defaults."""

    _AUDIENCE_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"\b(exec|executive|leadership|board|c-?suite)\b", "Executive stakeholders"),
        (r"\b(customer|client|buyer|prospect)\b", "Customer stakeholders"),
        (r"\b(engineer|developer|architect|technical|it team)\b", "Technical team"),
        (r"\b(product|operations|ops|pm|program)\b", "Cross-functional delivery team"),
    )
    _TONE_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"\b(formal|board|executive)\b", "Executive concise"),
        (r"\b(technical|deep dive|detailed)\b", "Technical precise"),
        (r"\b(persuade|pitch|sell|convince)\b", "Persuasive"),
    )

    def interpret(self, request: str) -> RequestInterpretation:
        cleaned = " ".join(request.strip().split())
        lowered = cleaned.lower()

        request_kind = self._infer_kind(lowered)
        topic = self._infer_topic(cleaned)
        audience = self._infer_audience(lowered)
        tone = self._infer_tone(lowered, audience=audience)
        deck_objective = self._infer_objective(topic=topic, kind=request_kind, audience=audience)
        likely_slide_count = self._infer_slide_count(lowered, request_kind)
        recommended_slide_types = self._recommended_slide_types(request_kind, lowered)

        return RequestInterpretation(
            topic=topic,
            audience=audience,
            deck_objective=deck_objective,
            likely_slide_count=likely_slide_count,
            recommended_slide_types=recommended_slide_types,
            tone=tone,
            request_kind=request_kind,
        )

    def _infer_kind(self, lowered: str) -> RequestCategory:
        signals = {
            "process": bool(re.search(r"\b(process|workflow|operating model|sop|handoff)\b", lowered)),
            "architecture": bool(
                re.search(r"\b(architecture|system design|platform|integration|data flow|solution design)\b", lowered)
            ),
            "roadmap": bool(re.search(r"\b(roadmap|timeline|milestone|phase|quarter|rollout)\b", lowered)),
            "comparison": bool(re.search(r"\b(compare|comparison|vs\.?|versus|option|trade-?off)\b", lowered)),
        }
        picked = [name for name, present in signals.items() if present]

        if len(picked) >= 2:
            return "mixed"

        if picked:
            return picked[0]  # type: ignore[return-value]

        # Enterprise default: vague solution-design requests usually need process + architecture.
        if re.search(r"\b(enterprise|solution|modernization|transformation|implementation)\b", lowered):
            return "mixed"

        return "process"

    def _infer_topic(self, cleaned: str) -> str:
        match = re.search(r"(?:about|for|on)\s+(.+?)(?:\.|$)", cleaned, flags=re.IGNORECASE)
        if match and len(match.group(1)) >= 4:
            return match.group(1).strip(" .")
        if len(cleaned) > 8:
            return cleaned[:120]
        return "Enterprise solution proposal"

    def _infer_audience(self, lowered: str) -> str:
        for pattern, audience in self._AUDIENCE_PATTERNS:
            if re.search(pattern, lowered):
                return audience
        return "Business and technology stakeholders"

    def _infer_tone(self, lowered: str, *, audience: str) -> str:
        for pattern, tone in self._TONE_PATTERNS:
            if re.search(pattern, lowered):
                return tone
        if "Executive" in audience:
            return "Executive concise"
        if "Technical" in audience:
            return "Technical precise"
        return "Consultative clear"

    def _infer_objective(self, *, topic: str, kind: RequestCategory, audience: str) -> str:
        objective_map = {
            "process": "Clarify the target process, ownership, and measurable outcomes.",
            "architecture": "Explain the proposed architecture and integration rationale.",
            "roadmap": "Align on phased delivery, milestones, and decision checkpoints.",
            "comparison": "Compare options, trade-offs, and recommendation criteria.",
            "mixed": "Present process and architecture options with a practical rollout path.",
        }
        return f"{objective_map[kind]} Audience: {audience}. Topic: {topic}."

    def _infer_slide_count(self, lowered: str, kind: RequestCategory) -> int:
        count_match = re.search(r"\b(\d{1,2})\s*(?:slides?|pages?)\b", lowered)
        if count_match:
            return max(4, min(20, int(count_match.group(1))))

        defaults = {
            "process": 7,
            "architecture": 8,
            "roadmap": 7,
            "comparison": 6,
            "mixed": 9,
        }
        return defaults[kind]

    def _recommended_slide_types(self, kind: RequestCategory, lowered: str) -> list[str]:
        base = ["title", "agenda"]

        by_kind = {
            "process": ["content", "process", "swimlane", "summary"],
            "architecture": ["content", "architecture", "integrations", "summary"],
            "roadmap": ["content", "roadmap", "issue_implication_recommendation", "summary"],
            "comparison": ["content", "diagram", "issue_implication_recommendation", "summary"],
            "mixed": [
                "content",
                "process",
                "architecture",
                "integrations",
                "roadmap",
                "summary",
            ],
        }
        rec = base + by_kind[kind]

        # Enterprise solution-design preference.
        if re.search(r"\b(enterprise|solution design|target operating model|implementation)\b", lowered):
            for preferred in ("process", "architecture"):
                if preferred not in rec:
                    rec.insert(2, preferred)
        return rec
