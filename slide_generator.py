from __future__ import annotations

import json

from llm_client import OllamaClient, mock_slide_payload
from schema import DeckPlan

SYSTEM_PROMPT = """
You are a slide semantics generator.
Return strict JSON only with fields:
request, model, plan, slides, warnings.
Each slide must include id, slide_type, title, subtitle, metadata.
Allowed slide_type values:
executive_summary, process_flow, swimlane, current_vs_target,
layered_architecture, integration_map, roadmap, issue_implication_recommendation.
Never include x/y coordinates. Never include styling details beyond metadata tags.
""".strip()


def generate_semantic_deck(prompt: str, model: str, plan: DeckPlan) -> dict:
    client = OllamaClient(model=model)
    plan_dict = json.loads(plan.model_dump_json())
    user_prompt = (
        f"Create a semantic slide deck JSON for this request: {prompt}\n"
        f"Use this plan exactly: {json.dumps(plan_dict)}"
    )

    try:
        generated = client.generate_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        generated.setdefault("warnings", [])
        return generated
    except Exception:
        return mock_slide_payload(plan=plan_dict, prompt=prompt, model=model)
