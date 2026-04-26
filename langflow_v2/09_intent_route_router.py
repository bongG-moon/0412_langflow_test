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

