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


def _select_postprocess_route(retrieval: Dict[str, Any]) -> str:
    if retrieval.get("skipped"):
        return "skipped"
    plan = retrieval.get("intent_plan") if isinstance(retrieval.get("intent_plan"), dict) else {}
    source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
    if retrieval.get("early_result"):
        return "direct_response"
    if plan.get("needs_pandas") or plan.get("query_mode") == "followup_transform" or len(source_results) > 1:
        return "post_analysis"
    return "direct_response"


def route_retrieval_postprocess(retrieval_payload_value: Any, branch: str) -> Dict[str, Any]:
    retrieval = _retrieval_payload(retrieval_payload_value)
    selected = _select_postprocess_route(retrieval)
    if selected != branch:
        return {
            "retrieval_payload": {
                "skipped": True,
                "skip_reason": f"selected postprocess route is {selected}",
                "selected_postprocess_route": selected,
                "branch": branch,
                "intent_plan": retrieval.get("intent_plan", {}),
                "state": retrieval.get("state", {}),
                "source_results": [],
            }
        }
    routed = deepcopy(retrieval)
    routed["selected_postprocess_route"] = selected
    routed["branch"] = branch
    return {"retrieval_payload": routed}


class RetrievalPostprocessRouter(Component):
    display_name = "Retrieval Postprocess Router"
    description = "Expose direct-response vs pandas-analysis branches after retrieval."
    icon = "GitBranch"
    name = "RetrievalPostprocessRouter"

    inputs = [
        DataInput(name="retrieval_payload", display_name="Retrieval Payload", info="Output from retriever branch.", input_types=["Data", "JSON"])
    ]
    outputs = [
        Output(name="direct_response", display_name="Direct Response", method="build_direct_response", group_outputs=True, types=["Data"]),
        Output(name="post_analysis", display_name="Post Analysis", method="build_post_analysis", group_outputs=True, types=["Data"]),
    ]

    def _payload(self, branch: str) -> Dict[str, Any]:
        payload = route_retrieval_postprocess(getattr(self, "retrieval_payload", None), branch)
        retrieval = payload.get("retrieval_payload", {})
        self.status = {"selected_postprocess_route": retrieval.get("selected_postprocess_route"), "branch": branch, "skipped": retrieval.get("skipped", False)}
        return payload

    def build_direct_response(self):
        return _make_data(self._payload("direct_response"))

    def build_post_analysis(self):
        return _make_data(self._payload("post_analysis"))

