"""Deterministic slide layout calculations independent from LLM output."""

from __future__ import annotations

from typing import Any


def layout_for_slide(slide: dict[str, Any]) -> dict[str, Any]:
    slide_type = slide.get("slide_type", "generic")
    if slide_type == "process flow":
        return _layout_process_flow(slide)
    if slide_type == "layered architecture":
        return _layout_layered_architecture(slide)
    if slide_type == "roadmap":
        return _layout_roadmap(slide)
    return _layout_generic(slide)


def _layout_process_flow(slide: dict[str, Any]) -> dict[str, Any]:
    nodes = slide.get("diagram_data", {}).get("nodes", [])
    spacing = 1 / max(len(nodes), 1)
    positions = []
    for idx, node in enumerate(nodes):
        positions.append({"id": node["id"], "x": round(0.08 + idx * spacing, 3), "y": 0.52, "w": 0.14, "h": 0.12})
    return {"template": "process_flow", "node_positions": positions}


def _layout_layered_architecture(slide: dict[str, Any]) -> dict[str, Any]:
    layers = slide.get("diagram_data", {}).get("layers", [])
    h = 0.62 / max(len(layers), 1)
    out = []
    for idx, layer in enumerate(layers):
        out.append({"id": layer["id"], "x": 0.1, "y": round(0.22 + idx * h, 3), "w": 0.8, "h": round(h - 0.02, 3)})
    return {"template": "layered_architecture", "layer_positions": out}


def _layout_roadmap(slide: dict[str, Any]) -> dict[str, Any]:
    milestones = slide.get("diagram_data", {}).get("milestones", [])
    spacing = 1 / max(len(milestones), 1)
    out = []
    for idx, ms in enumerate(milestones):
        out.append({"id": ms["id"], "x": round(0.08 + idx * spacing, 3), "y": 0.5})
    return {"template": "roadmap", "milestone_positions": out}


def _layout_generic(slide: dict[str, Any]) -> dict[str, Any]:
    return {"template": "generic", "body_box": {"x": 0.07, "y": 0.24, "w": 0.86, "h": 0.64}}
