import asyncio
import json

from app.services.llm_client import OllamaLLMClient


class StubbedOllamaClient(OllamaLLMClient):
    def __init__(self, responses: list[str]) -> None:
        super().__init__()
        self._responses = responses

    async def _complete(self, prompt: str, *, task_name: str) -> str:  # type: ignore[override]
        if not self._responses:
            raise RuntimeError("No more stub responses")
        return self._responses.pop(0)


def test_generate_deck_plan_uses_repair_on_invalid_json() -> None:
    client = StubbedOllamaClient([
        "not-json",
        '{"deck_title":"Order-to-Cash Deck","audience":"COO","deck_objective":"Improve cycle time","slides":[{"id":"s1","slide_type":"executive_summary","objective":"Frame value","key_message":"Cycle-time reduction unlocks cash."}]}'
    ])

    result = asyncio.run(client.generate_deck_plan({"user_request": "3 slides on order-to-cash process"}))

    assert result["deck_title"] == "Order-to-Cash Deck"
    assert result["slides"][0]["slide_type"] == "executive_summary"


def test_generate_slide_supports_architecture_prompt() -> None:
    payload = {
        "id": "s2",
        "order": 2,
        "type": "architecture",
        "title": "Target Claims Architecture",
        "objective": "Define layered capabilities",
        "architecture": {
            "layers": [
                {"id": "l1", "name": "Channels", "responsibility": "Intake", "components": ["Portal", "API Gateway"]},
                {"id": "l2", "name": "Core", "responsibility": "Claims orchestration", "components": ["Workflow", "Rules Engine"]},
                {"id": "l3", "name": "Data", "responsibility": "Storage and analytics", "components": ["ODS", "Warehouse"]},
            ],
            "integrations": [
                {"id": "i1", "system": "Policy Admin", "purpose": "Coverage validation", "direction": "bidirectional"}
            ],
        },
    }
    client = StubbedOllamaClient([json.dumps(payload)])

    result = asyncio.run(
        client.generate_slide(
            deck_context={"deck_title": "Claims Modernization", "audience": "IT leadership", "deck_objective": "Target architecture"},
            slide_plan_item={"id": "s2", "order": 2, "slide_type": "layered_architecture", "objective": "Define architecture", "key_message": "Layering reduces coupling."},
        )
    )

    assert result["type"] == "architecture"
    assert len(result["architecture"]["layers"]) == 3


def test_generate_slide_supports_roadmap_prompt() -> None:
    payload = {
        "id": "s3",
        "order": 3,
        "type": "roadmap",
        "title": "Digital Transformation Roadmap",
        "objective": "Sequence transformation delivery",
        "roadmap": {
            "phases": [
                {"id": "p1", "name": "Mobilize", "objective": "Set governance", "milestones": [{"id": "m1", "label": "Program charter", "status": "planned", "target_period": "Q1"}]},
                {"id": "p2", "name": "Modernize", "objective": "Upgrade platforms", "milestones": [{"id": "m2", "label": "Core release", "status": "planned", "target_period": "Q2"}]},
                {"id": "p3", "name": "Scale", "objective": "Expand automation", "milestones": [{"id": "m3", "label": "Enterprise rollout", "status": "planned", "target_period": "Q3"}]},
            ]
        },
    }
    client = StubbedOllamaClient([json.dumps(payload)])

    result = asyncio.run(
        client.generate_slide(
            deck_context={"deck_title": "Digital Transformation", "audience": "Executive committee", "deck_objective": "Roadmap alignment"},
            slide_plan_item={"id": "s3", "order": 3, "slide_type": "roadmap", "objective": "Show phases", "key_message": "Phase delivery lowers execution risk."},
        )
    )

    assert result["type"] == "roadmap"
    assert len(result["roadmap"]["phases"]) == 3
