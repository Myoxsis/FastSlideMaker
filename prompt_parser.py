"""Prompt parsing and system prompt templates for structured deck generation."""

from __future__ import annotations

from textwrap import dedent


def build_system_prompt() -> str:
    return dedent(
        """
        You are a strategy consulting slide planner specialized in process and IT solution design.
        Return ONLY JSON that matches the requested schema.
        Focus on structure, audience takeaway, relationships, and visual clarity.
        Keep each slide concise and decision-oriented.
        Supported slide_type values:
        executive summary, process flow, swimlane, current vs target, layered architecture,
        integration map, roadmap, issue / implication / recommendation.
        """
    ).strip()


def build_user_prompt(user_prompt: str, slide_count: int = 6) -> str:
    schema_hint = dedent(
        """
        Generate a JSON object with:
        {
          "presentation": {"title": str, "theme": str, "description": str},
          "slides": [
            {
              "id": str,
              "title": str,
              "objective": str,
              "slide_type": str,
              "audience": str,
              "summary": str,
              "audience_takeaway": str,
              "key_entities": [str],
              "relationships": [str],
              "priority_of_information": [str],
              "content_blocks": [{"type": str, "text": str}],
              "diagram_data": {
                "nodes": [{"id": str, "label": str, "type": str}],
                "edges": [{"from": str, "to": str, "label": str}],
                "lanes": [{"id": str, "label": str, "nodes": [str]}],
                "layers": [{"id": str, "label": str, "items": [str]}],
                "milestones": [{"id": str, "label": str, "period": str}],
                "annotations": [{"id": str, "text": str, "target": str}]
              },
              "layout_hints": {"density": str, "emphasis": str}
            }
          ]
        }
        """
    ).strip()

    return dedent(
        f"""
        User request:
        {user_prompt}

        Constraints:
        - Produce exactly {slide_count} slides.
        - Keep language concise and business-friendly.
        - Infer a coherent narrative arc: context -> process -> target design -> roadmap.
        - Ensure each slide has meaningful diagram_data for its type.

        {schema_hint}
        """
    ).strip()
