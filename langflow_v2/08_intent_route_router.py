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


def _intent_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("intent_plan"), dict):
        return payload
    return {"intent_plan": payload, "retrieval_jobs": payload.get("retrieval_jobs", []) if isinstance(payload, dict) else []}


def _select_route(plan: Dict[str, Any]) -> str:
    route = str(plan.get("route") or "").strip()
    query_mode = str(plan.get("query_mode") or "").strip()
    if route == "finish" or query_mode in {"finish", "clarification"}:
        return "finish"
    if route == "followup_transform" or query_mode == "followup_transform":
        return "followup_transform"
    if route == "multi_retrieval" or len(plan.get("retrieval_jobs", []) if isinstance(plan.get("retrieval_jobs"), list) else []) > 1:
        return "multi_retrieval"
    return "single_retrieval"


def route_intent(intent_plan_value: Any, branch: str) -> Dict[str, Any]:
    payload = _intent_payload(intent_plan_value)
    plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else {}
    selected = _select_route(plan)
    if selected != branch:
        return {
            "skipped": True,
            "skip_reason": f"selected route is {selected}",
            "selected_route": selected,
            "branch": branch,
            "intent_plan": plan,
            "state": payload.get("state", {}),
        }
    routed = deepcopy(payload)
    routed["selected_route"] = selected
    routed["branch"] = branch
    return routed


class IntentRouteRouter(Component):
    display_name = "Intent Route Router"
    description = "Expose intent_plan.route as visible Langflow branches."
    icon = "GitBranch"
    name = "IntentRouteRouter"

    inputs = [
        DataInput(name="intent_plan", display_name="Intent Plan", info="Output from Normalize Intent Plan.", input_types=["Data", "JSON"])
    ]
    outputs = [
        Output(name="single_retrieval", display_name="Single Retrieval", method="build_single_retrieval", group_outputs=True, types=["Data"]),
        Output(name="multi_retrieval", display_name="Multi Retrieval", method="build_multi_retrieval", group_outputs=True, types=["Data"]),
        Output(name="followup_transform", display_name="Follow-up Transform", method="build_followup_transform", group_outputs=True, types=["Data"]),
        Output(name="finish", display_name="Finish / Clarification", method="build_finish", group_outputs=True, types=["Data"]),
    ]

    def _payload(self, branch: str) -> Dict[str, Any]:
        payload = route_intent(getattr(self, "intent_plan", None), branch)
        self.status = {"selected_route": payload.get("selected_route"), "branch": branch, "skipped": payload.get("skipped", False)}
        return payload

    def build_single_retrieval(self):
        return _make_data(self._payload("single_retrieval"))

    def build_multi_retrieval(self):
        return _make_data(self._payload("multi_retrieval"))

    def build_followup_transform(self):
        return _make_data(self._payload("followup_transform"))

    def build_finish(self):
        return _make_data(self._payload("finish"))

