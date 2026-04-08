"""Deterministic designer phase that converts semantic slides into render-safe layouts."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from textwrap import shorten
from typing import Any

from app.models.schemas import (
    ArchitectureLayer,
    LayoutHints,
    ProcessStep,
    RoadmapPhase,
    SemanticPresentation,
    SemanticSlide,
    SlideType,
    Swimlane,
    TextBlock,
)

SLIDE_WIDTH = 13.333
SLIDE_HEIGHT = 7.5


class DesignerService:
    """Applies deterministic spacing and overflow constraints before render/export."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._rules = self._load_rules(config_path)

    @property
    def rules(self) -> dict[str, Any]:
        return deepcopy(self._rules)

    def design_presentation(self, presentation: SemanticPresentation | dict[str, Any]) -> SemanticPresentation:
        model = (
            presentation
            if isinstance(presentation, SemanticPresentation)
            else SemanticPresentation.model_validate(presentation)
        )
        designed_slides = [self.design_slide(slide) for slide in model.slides]
        return model.model_copy(update={"slides": designed_slides}).normalized()

    def design_slide(self, slide: SemanticSlide) -> SemanticSlide:
        updated = slide.normalized().model_copy(deep=True)
        hints = LayoutHints(
            grid="single_column",
            spacing=f"{self._rules['min_spacing']}in",
            overflow_strategy="wrap",
            grouping="none",
            element_positions={},
        )

        if updated.type == SlideType.PROCESS and updated.process:
            self._design_process_flow(updated, hints)
        elif updated.type == SlideType.ARCHITECTURE and updated.architecture:
            self._design_layered_architecture(updated, hints)
        elif updated.type == SlideType.ROADMAP and updated.roadmap:
            self._design_roadmap(updated, hints)
        elif updated.type == SlideType.SWIMLANE and updated.swimlanes:
            self._design_swimlane(updated, hints)
        else:
            self._design_generic_content(updated, hints)

        updated.layout_hints = hints
        return updated

    @staticmethod
    def estimate_text_width(text: str, font_size: float) -> float:
        """Approximate text width in inches (PPT-friendly estimate, not pixels)."""

        return max(0.15, len(" ".join(text.split())) * font_size * 0.0072)

    @classmethod
    def estimate_box_size(cls, content: str, *, font_size: float = 12, max_width: float = 3.0) -> tuple[float, float]:
        width = min(max_width, cls.estimate_text_width(content, font_size) + 0.3)
        chars_per_line = max(16, int(max_width / max(font_size * 0.0072, 0.001)))
        lines = max(1, (len(content) // chars_per_line) + 1)
        height = max(0.4, lines * (font_size / 72) * 1.35 + 0.18)
        return (round(width, 3), round(height, 3))

    @staticmethod
    def detect_overlap(box_a: dict[str, float], box_b: dict[str, float]) -> bool:
        return not (
            box_a["x"] + box_a["w"] <= box_b["x"]
            or box_b["x"] + box_b["w"] <= box_a["x"]
            or box_a["y"] + box_a["h"] <= box_b["y"]
            or box_b["y"] + box_b["h"] <= box_a["y"]
        )

    def resolve_overlap(
        self,
        boxes: list[dict[str, float]],
        *,
        strategy: str = "shift",
        bounds: tuple[float, float, float, float] | None = None,
    ) -> list[dict[str, float]]:
        """Resolve overlap in predictable order using shift/resize/wrap/split."""

        adjusted = [dict(box) for box in boxes]
        spacing = self._rules["min_spacing"]
        x_min, y_min, x_max, y_max = bounds or (0.0, 0.0, SLIDE_WIDTH, SLIDE_HEIGHT)

        for i in range(1, len(adjusted)):
            for j in range(i):
                if not self.detect_overlap(adjusted[i], adjusted[j]):
                    continue

                if strategy == "resize":
                    adjusted[i]["h"] = max(0.35, adjusted[i]["h"] - 0.15)
                    adjusted[i]["w"] = max(0.8, adjusted[i]["w"] - 0.1)
                elif strategy == "wrap":
                    adjusted[i]["h"] += 0.18
                    adjusted[i]["w"] = max(0.9, adjusted[i]["w"] - 0.08)
                elif strategy == "split":
                    adjusted[i]["y"] = min(y_max - adjusted[i]["h"], adjusted[j]["y"] + adjusted[j]["h"] + spacing)
                else:  # shift
                    adjusted[i]["y"] = adjusted[j]["y"] + adjusted[j]["h"] + spacing

                adjusted[i]["x"] = min(max(adjusted[i]["x"], x_min), x_max - adjusted[i]["w"])
                adjusted[i]["y"] = min(max(adjusted[i]["y"], y_min), y_max - adjusted[i]["h"])

        return adjusted

    def normalize_spacing(self, elements: list[dict[str, float]]) -> list[dict[str, float]]:
        if not elements:
            return []
        ordered = sorted((dict(item) for item in elements), key=lambda item: (item["y"], item["x"]))
        spacing = self._rules["min_spacing"]
        for idx in range(1, len(ordered)):
            prior = ordered[idx - 1]
            current = ordered[idx]
            min_y = prior["y"] + prior["h"] + spacing
            if current["y"] < min_y:
                current["y"] = min_y
        return ordered

    def _load_rules(self, config_path: Path | None) -> dict[str, Any]:
        path = config_path or Path(__file__).with_name("design_rules.json")
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw

    def _margin_bounds(self) -> tuple[float, float, float, float]:
        margin = self._rules["slide_margin"]
        return (margin, margin, SLIDE_WIDTH - margin, SLIDE_HEIGHT - margin)

    def _truncate(self, text: str, limit: int) -> str:
        return shorten(" ".join(text.split()), width=limit, placeholder="…")

    def _design_process_flow(self, slide: SemanticSlide, hints: LayoutHints) -> None:
        assert slide.process is not None
        max_per_row = self._rules["max_process_steps_per_row"]
        steps: list[ProcessStep] = list(slide.process.steps)
        if len(steps) > self._rules["max_process_steps_total"]:
            steps = steps[: self._rules["max_process_steps_total"]]
        rows = [steps[i : i + max_per_row] for i in range(0, len(steps), max_per_row)]

        box_w = 1.85
        box_h = 0.95
        bounds = self._margin_bounds()
        content_w = bounds[2] - bounds[0]
        row_gap = max(self._rules["min_spacing"], 0.24)

        positions: dict[str, dict[str, float | str | int]] = {}
        normalized_steps: list[ProcessStep] = []
        for row_idx, row_steps in enumerate(rows):
            span = len(row_steps) * box_w + max(0, len(row_steps) - 1) * self._rules["min_spacing"]
            start_x = bounds[0] + max(0.0, (content_w - span) / 2)
            y = 1.8 + row_idx * (box_h + row_gap)
            for col_idx, step in enumerate(row_steps):
                label = self._truncate(step.label, self._rules["max_label_chars"]) 
                desc = self._truncate(step.description or "", self._rules["max_body_chars"]) if step.description else None
                normalized_steps.append(step.model_copy(update={"label": label, "description": desc}))
                x = start_x + col_idx * (box_w + self._rules["min_spacing"])
                positions[step.id] = {"x": round(x, 3), "y": round(y, 3), "w": box_w, "h": box_h, "row": row_idx}

        slide.process = slide.process.model_copy(update={"steps": normalized_steps})
        slide.diagram_data = {
            "type": "process_flow",
            "rows": len(rows),
            "arrows": "horizontal_then_down",
            "step_ids": [step.id for step in normalized_steps],
        }
        hints.grid = "process_rows"
        hints.grouping = f"rows:{len(rows)}"
        hints.overflow_strategy = "split" if len(rows) > 1 else "wrap"
        hints.element_positions = positions

    def _design_layered_architecture(self, slide: SemanticSlide, hints: LayoutHints) -> None:
        assert slide.architecture is not None
        max_components = self._rules["max_items_per_layer"]
        layers: list[ArchitectureLayer] = []
        for layer in slide.architecture.layers:
            layers.append(
                layer.model_copy(
                    update={
                        "name": self._truncate(layer.name, self._rules["max_label_chars"]),
                        "responsibility": self._truncate(layer.responsibility, self._rules["max_body_chars"]),
                        "components": [self._truncate(c, 30) for c in layer.components[:max_components]],
                    }
                )
            )

        bounds = self._margin_bounds()
        available_h = bounds[3] - 1.9
        layer_h = max(0.72, (available_h - (len(layers) - 1) * self._rules["min_spacing"]) / max(1, len(layers)))
        positions = {}
        y = 1.8
        for layer in layers:
            positions[layer.id] = {"x": bounds[0], "y": round(y, 3), "w": round(bounds[2] - bounds[0], 3), "h": round(layer_h, 3)}
            y += layer_h + self._rules["min_spacing"]

        slide.architecture = slide.architecture.model_copy(update={"layers": layers})
        slide.diagram_data = {"type": "layered_architecture", "layer_count": len(layers), "equal_height": round(layer_h, 3)}
        hints.grid = "vertical_stack"
        hints.grouping = f"layers:{len(layers)}"
        hints.overflow_strategy = "group"
        hints.element_positions = positions

    def _design_roadmap(self, slide: SemanticSlide, hints: LayoutHints) -> None:
        assert slide.roadmap is not None
        max_phases = self._rules["max_roadmap_phases"]
        max_milestones = self._rules["max_milestones_per_phase"]
        phases: list[RoadmapPhase] = []
        for phase in slide.roadmap.phases[:max_phases]:
            milestones = [
                milestone.model_copy(update={"label": self._truncate(milestone.label, self._rules["max_label_chars"])})
                for milestone in phase.milestones[:max_milestones]
            ]
            phases.append(
                phase.model_copy(
                    update={
                        "name": self._truncate(phase.name, self._rules["max_label_chars"]),
                        "objective": self._truncate(phase.objective, self._rules["max_body_chars"]),
                        "milestones": milestones,
                    }
                )
            )

        count = max(1, len(phases))
        bounds = self._margin_bounds()
        lane_w = (bounds[2] - bounds[0] - (count - 1) * self._rules["min_spacing"]) / count
        positions = {}
        for idx, phase in enumerate(phases):
            x = bounds[0] + idx * (lane_w + self._rules["min_spacing"])
            y = 2.05 if idx % 2 == 0 else 3.4
            positions[phase.id] = {"x": round(x, 3), "y": y, "w": round(lane_w, 3), "h": 1.35}

        slide.roadmap = slide.roadmap.model_copy(update={"phases": phases})
        slide.diagram_data = {"type": "roadmap", "phase_count": len(phases), "alternating_cards": True}
        hints.grid = "timeline"
        hints.grouping = f"phases:{len(phases)}"
        hints.overflow_strategy = "split" if len(slide.roadmap.phases) > max_phases else "wrap"
        hints.element_positions = positions

    def _design_swimlane(self, slide: SemanticSlide, hints: LayoutHints) -> None:
        assert slide.swimlanes is not None
        lanes: list[Swimlane] = []
        for lane in slide.swimlanes.lanes:
            limited_items = lane.items[: self._rules["max_swimlane_items"]]
            lanes.append(
                lane.model_copy(
                    update={
                        "lane_label": self._truncate(lane.lane_label, self._rules["max_label_chars"]),
                        "items": [
                            item.model_copy(update={"label": self._truncate(item.label, self._rules["max_body_chars"])})
                            for item in limited_items
                        ],
                    }
                )
            )

        lane_count = max(1, len(lanes))
        bounds = self._margin_bounds()
        gap = self._rules["min_spacing"]
        lane_h = (bounds[3] - 2.0 - (lane_count - 1) * gap) / lane_count
        positions = {}
        for idx, lane in enumerate(lanes):
            y = 1.95 + idx * (lane_h + gap)
            positions[lane.id] = {"x": bounds[0], "y": round(y, 3), "w": round(bounds[2] - bounds[0], 3), "h": round(lane_h, 3)}

        slide.swimlanes = slide.swimlanes.model_copy(update={"lanes": lanes})
        slide.diagram_data = {"type": "swimlane", "lane_count": lane_count, "equal_lane_height": round(lane_h, 3)}
        hints.grid = "swimlane_rows"
        hints.grouping = f"lanes:{lane_count}"
        hints.overflow_strategy = "group"
        hints.element_positions = positions

    def _design_generic_content(self, slide: SemanticSlide, hints: LayoutHints) -> None:
        max_bullets = self._rules["max_generic_bullets"]
        max_chars = self._rules["max_chars_per_line"]
        blocks: list[TextBlock] = []
        for block in slide.text_blocks[:max_bullets]:
            blocks.append(
                block.model_copy(
                    update={
                        "label": self._truncate(block.label, 30) if block.label else None,
                        "text": self._truncate(block.text, max_chars),
                    }
                )
            )

        boxes = []
        bounds = self._margin_bounds()
        x = bounds[0]
        y = 1.9
        w = bounds[2] - bounds[0]
        for block in blocks:
            _, h = self.estimate_box_size(block.text, font_size=12, max_width=w)
            boxes.append({"id": block.id, "x": x, "y": y, "w": w, "h": h})
            y += h + self._rules["min_spacing"]

        resolved = self.resolve_overlap(boxes, strategy="shift", bounds=bounds)
        spaced = self.normalize_spacing(resolved)
        hints.element_positions = {
            box["id"]: {"x": round(box["x"], 3), "y": round(box["y"], 3), "w": round(box["w"], 3), "h": round(box["h"], 3)}
            for box in spaced
        }

        slide.text_blocks = blocks
        slide.diagram_data = {"type": "generic", "columns": 1 if len(blocks) <= 4 else 2, "block_count": len(blocks)}
        hints.grid = "single_column" if len(blocks) <= 4 else "two_column"
        hints.grouping = "bullets"
        hints.overflow_strategy = "truncate"


def design_semantic_presentation(presentation: SemanticPresentation | dict[str, Any]) -> SemanticPresentation:
    """Convenience helper for deterministic design pass."""

    return DesignerService().design_presentation(presentation)
