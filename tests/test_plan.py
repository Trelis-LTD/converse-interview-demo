from interview_demo.plan import build_instructions, build_tool, load_plan, required_fields


def test_plan_has_four_required_fields_and_one_optional_field() -> None:
    plan = load_plan()

    assert len(required_fields(plan)) == 4
    assert [field["key"] for field in plan["fields"] if not field.get("required", True)] == [
        "follow_up_permission"
    ]


def test_instructions_make_the_application_completion_contract_explicit() -> None:
    instructions = build_instructions(load_plan())

    assert "record_plan_field" in instructions
    assert "missing_required" in instructions
    assert "every required field has been recorded" in instructions
    assert "do not ask a follow-up" in instructions
    assert "about three minutes" in instructions


def test_instructions_end_immediately_when_the_participant_asks_to_stop() -> None:
    instructions = build_instructions(load_plan())

    assert "asks to stop" in instructions
    assert "end_call" in instructions
    assert "required fields are still missing" in instructions


def test_tool_accepts_only_configured_fields() -> None:
    plan = load_plan()
    tool = build_tool(plan)

    assert tool["name"] == "record_plan_field"
    assert tool["expected_duration"] == "instant"
    assert tool["read_only"] is False
    assert tool["status_label"] == "interview notes"
    assert tool["parameters"]["properties"]["field"]["enum"] == [
        field["key"] for field in plan["fields"]
    ]
