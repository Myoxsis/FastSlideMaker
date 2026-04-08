import asyncio

from app.models.schemas import SlideType
from app.services.deck_planner import SlidePlanItem
from app.services.slide_generator import SlideGenerator


class StubLLM:
    def __init__(self, response: str, repaired: str | None = None) -> None:
        self.response = response
        self.repaired = repaired or "{}"

    async def generate_slide_json(self, *, plan_json: str, slide_count: int) -> str:
        return self.response

    async def repair_json(self, *, malformed_json: str, expected_shape_hint: str = "") -> str:
        return self.repaired


def test_generate_single_semantic_slide_normalizes_and_validates() -> None:
    raw = """
    {
      "slide": {
        "id": "s1",
        "order": 1,
        "type": "integrations",
        "title": "  Integration Landscape for Program Execution  ",
        "objective": "  Show integration priorities and dependencies across the program. ",
        "text_blocks": [
          {"id":"tb1","role":"bullet","label":"  Priority Stream  ","text":"  ERP to CRM sync for customer status updates with a lot of extra wording that should still be cleaned up.  "}
        ],
        "integrations": [
          {"id":"i2","system":"Zeta","purpose":"z sync","direction":"outbound"},
          {"id":"i1","system":"Alpha","purpose":"a sync","direction":"inbound"}
        ]
      }
    }
    """

    generator = SlideGenerator(llm_client=StubLLM(raw))
    slide = asyncio.run(generator.generate_semantic_slide(
        deck_context="Use term Program Control Tower throughout the deck.",
        current_slide_objective="Summarize core integrations.",
        selected_slide_type=SlideType.INTEGRATIONS,
        slide_id="s1",
        order=1,
        title="Integrations",
    ))

    assert slide.type == SlideType.INTEGRATIONS
    assert slide.title == "Integration Landscape for Program Execution"
    assert slide.text_blocks[0].label == "Priority Stream"
    assert [item.system for item in slide.integrations] == ["Alpha", "Zeta"]


def test_generate_single_slide_uses_repair_path_for_malformed_output() -> None:
    malformed = "not-json"
    repaired = '{"id":"s2","order":2,"type":"diagram","title":"Decision Flow","objective":"Map dependencies."}'

    generator = SlideGenerator(llm_client=StubLLM(malformed, repaired=repaired))
    slide = asyncio.run(generator.generate_semantic_slide(
        deck_context="",
        current_slide_objective="Map dependencies",
        selected_slide_type=SlideType.DIAGRAM,
        slide_id="s2",
        order=2,
    ))

    assert slide.type == SlideType.DIAGRAM
    assert slide.diagram is not None
    assert len(slide.diagram.nodes) >= 2


def test_regenerate_single_slide_workflow() -> None:
    response = '{"id":"s3","order":3,"type":"summary","title":"Next Steps","text_blocks":[{"id":"t1","role":"bullet","text":"Approve phase 1"}]}'
    generator = SlideGenerator(llm_client=StubLLM(response))

    plan_item = SlidePlanItem(order=3, title="Summary", objective="Confirm actions", visual_type="key takeaways panel")
    slide = asyncio.run(generator.regenerate_semantic_slide(deck_context="same deck terms", slide_plan_item=plan_item))

    assert slide.id == "s3"
    assert slide.order == 3
    assert slide.type == SlideType.SUMMARY
