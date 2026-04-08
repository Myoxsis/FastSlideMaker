from app.services.deck_planner import DeckPlanner
from app.services.request_interpreter import RequestInterpreter


def test_interpreter_infers_mixed_for_enterprise_solution_design() -> None:
    interpreter = RequestInterpreter()
    result = interpreter.interpret(
        "Need an enterprise solution design deck for exec leadership with architecture and roadmap"
    )

    assert result.request_kind == "mixed"
    assert result.audience == "Executive stakeholders"
    assert "process" in result.recommended_slide_types
    assert "architecture" in result.recommended_slide_types


def test_planner_generates_ordered_slides_with_visuals() -> None:
    planner = DeckPlanner()
    plan = planner.plan_from_request(
        "Compare options for data platform migration vs modernization for technical architects"
    )

    assert plan.deck_title
    assert len(plan.ordered_slide_plan) >= 6
    assert plan.ordered_slide_plan[0].order == 1
    assert all(item.visual_type for item in plan.ordered_slide_plan)
