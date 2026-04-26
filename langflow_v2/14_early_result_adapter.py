from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return deepcopy(data)
    text = getattr(value, "text", None) or getattr(value, "content", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def build_early_analysis_result(intent_plan_value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(intent_plan_value)
    plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    if payload.get("skipped"):
        return {
            "analysis_result": {
                "skipped": True,
                "skip_reason": payload.get("skip_reason", "route skipped"),
                "analysis_logic": "early_result_skipped",
                "intent_plan": plan,
                "state": state,
            }
        }

    response = str(plan.get("response") or "질문을 처리하려면 추가 조건이 필요합니다.")
    result = {
        "success": False,
        "tool_name": "early_result",
        "data": [],
        "summary": response,
        "error_message": "",
        "analysis_logic": "early_result",
        "source_results": [],
        "retrieval_applied_params": plan.get("required_params", {}) if isinstance(plan, dict) else {},
        "followup_applied_params": {},
        "intent_plan": plan if isinstance(plan, dict) else {},
        "state": state,
        "user_question": state.get("pending_user_question", ""),
        "awaiting_analysis_choice": False,
    }
    return {"analysis_result": result}


class EarlyResultAdapter(Component):
    display_name = "Early Result Adapter"
    description = "Convert finish/clarification intent branches into analysis_result shape."
    icon = "CornerDownRight"
    name = "EarlyResultAdapter"

    inputs = [
        DataInput(name="intent_plan", display_name="Finish Intent Plan", info="Output from Intent Route Router.finish.", input_types=["Data", "JSON"])
    ]
    outputs = [Output(name="analysis_result", display_name="Analysis Result", method="build_result", types=["Data"])]

    def build_result(self):
        payload = build_early_analysis_result(getattr(self, "intent_plan", None))
        result = payload.get("analysis_result", {})
        self.status = {"logic": result.get("analysis_logic"), "skipped": result.get("skipped", False)}
        return _make_data(payload)

