from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback


class _FallbackComponent:
    display_name = ""
    description = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""


@dataclass
class _FallbackInput:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    advanced: bool = False
    tool_mode: bool = False
    input_types: list[str] | None = None


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


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


def _retrieval_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("retrieval_payload") if isinstance(payload.get("retrieval_payload"), dict) else payload


def adapt_direct_result(retrieval_payload_value: Any) -> Dict[str, Any]:
    retrieval = _retrieval_payload(retrieval_payload_value)
    plan = retrieval.get("intent_plan") if isinstance(retrieval.get("intent_plan"), dict) else {}
    state = retrieval.get("state") if isinstance(retrieval.get("state"), dict) else {}
    if retrieval.get("skipped"):
        return {
            "analysis_result": {
                "skipped": True,
                "skip_reason": retrieval.get("skip_reason", "route skipped"),
                "analysis_logic": "direct_response_skipped",
                "source_results": [],
                "intent_plan": plan,
                "state": state,
            }
        }

    source_results = [item for item in retrieval.get("source_results", []) if isinstance(item, dict)] if isinstance(retrieval.get("source_results"), list) else []
    failed = [item for item in source_results if not item.get("success")]
    valid = [item for item in source_results if item.get("success")]
    first = valid[0] if valid else (failed[0] if failed else {})
    rows = deepcopy(first.get("data", [])) if isinstance(first.get("data"), list) else []
    success = bool(valid) and not failed
    summary = first.get("summary") or (f"retrieved rows: {len(rows)}" if rows else "No source data is available.")
    result = {
        "success": success,
        "tool_name": first.get("tool_name", "direct_response"),
        "data": rows,
        "summary": summary if success else first.get("error_message", summary),
        "error_message": "" if success else first.get("error_message", summary),
        "analysis_logic": "direct_response",
        "source_results": source_results,
        "source_dataset_keys": [str(item.get("dataset_key")) for item in source_results if item.get("dataset_key")],
        "current_datasets": retrieval.get("current_datasets", {}),
        "source_snapshots": retrieval.get("source_snapshots", []),
        "retrieval_applied_params": plan.get("required_params", {}) if isinstance(plan, dict) else {},
        "followup_applied_params": plan if isinstance(plan, dict) and plan.get("query_mode") == "followup_transform" else {},
        "intent_plan": plan if isinstance(plan, dict) else {},
        "state": state,
        "user_question": state.get("pending_user_question", ""),
        "merge_notes": [],
        "awaiting_analysis_choice": bool(success),
    }
    return {"analysis_result": result}


class DirectResultAdapter(Component):
    display_name = "Direct Result Adapter"
    description = "Convert retrieval_payload into analysis_result when pandas post-analysis is not needed."
    icon = "CornerDownRight"
    name = "DirectResultAdapter"

    inputs = [
        DataInput(name="retrieval_payload", display_name="Direct Retrieval Payload", info="Output from Retrieval Postprocess Router.direct_response.", input_types=["Data", "JSON"])
    ]
    outputs = [Output(name="analysis_result", display_name="Analysis Result", method="build_result", types=["Data"])]

    def build_result(self):
        payload = adapt_direct_result(getattr(self, "retrieval_payload", None))
        result = payload.get("analysis_result", {})
        self.status = {"logic": result.get("analysis_logic"), "success": result.get("success"), "skipped": result.get("skipped", False)}
        return _make_data(payload)

