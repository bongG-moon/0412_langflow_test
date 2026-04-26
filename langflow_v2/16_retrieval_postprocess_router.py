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

