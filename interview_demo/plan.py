from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = PROJECT_ROOT / "interview_plan.json"


@lru_cache(maxsize=1)
def load_plan() -> dict[str, Any]:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def required_fields(plan: dict[str, Any]) -> list[str]:
    return [
        str(field["key"])
        for field in plan["fields"]
        if field.get("required", True)
    ]


def build_instructions(plan: dict[str, Any]) -> str:
    evidence = "\n".join(
        f"- {field['key']} ({'required' if field.get('required', True) else 'optional'}): "
        f"{field['description']}"
        for field in plan["fields"]
    )
    return (
        f"You are conducting {plan['name']}.\n"
        f"Objective: {plan['objective']}\n\n"
        "Collect the evidence below through a concise, natural conversation. Choose the order "
        "based on what the participant says. Ask only one question at a time. Clarify vague or "
        "very short answers, but do not ask a follow-up when the participant has already supplied "
        "the evidence. Do not read the field list aloud. Whenever an answer sufficiently supports "
        "one or more fields, make one record_plan_field call containing all supported fields in "
        "the updates array. Batch all supported fields from the participant's latest answer into "
        "that one call. Update a field if later evidence changes it. Treat a "
        "refusal to answer respectfully and do not pressure the participant. Do not claim the "
        "interview is complete until every required field has been recorded. Treat the tool's "
        "missing_required and complete result as the authoritative completion state. When complete "
        "is true, do not ask another evidence-gathering question; proceed to the completion flow. "
        "If the participant asks to stop or end the interview at any point, stop gathering evidence "
        "and immediately call end_call with a brief respectful farewell, even if required fields "
        "are still missing. Never say goodbye or imply that the session has ended without calling "
        "end_call. After the normal completion flow, also use end_call for the final farewell. "
        "Keep the interview to about three minutes.\n\n"
        f"Evidence:\n{evidence}\n\n"
        f"Once complete: {plan['completion']}"
    )


def build_tool(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "record_plan_field",
        "description": (
            "Record or correct every supported piece of evidence from the participant's latest "
            "answer in one call. Submit all field updates together. The result reports "
            "missing_required and complete; follow that state before asking another question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "updates": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": len(plan["fields"]),
                    "description": (
                        "All supported or corrected fields from the participant's latest answer."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "enum": [str(field["key"]) for field in plan["fields"]],
                            },
                            "value": {
                                "type": "string",
                                "description": "Concise evidence in the participant's own terms.",
                            },
                        },
                        "required": ["field", "value"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["updates"],
            "additionalProperties": False,
        },
        "read_only": False,
        "expected_duration": "instant",
        "status_label": "interview notes",
    }


def public_config() -> dict[str, Any]:
    plan = load_plan()
    return {
        "name": plan["name"],
        "greeting": plan["greeting"],
        "instructions": build_instructions(plan),
        "fields": plan["fields"],
        "required_fields": required_fields(plan),
        "tool": build_tool(plan),
    }
