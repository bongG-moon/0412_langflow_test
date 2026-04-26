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


def merge_retrieval_payloads(single_retrieval_value: Any = None, multi_retrieval_value: Any = None, followup_retrieval_value: Any = None) -> Dict[str, Any]:
    candidates = [
        ("single_retrieval", _retrieval_payload(single_retrieval_value)),
        ("multi_retrieval", _retrieval_payload(multi_retrieval_value)),
        ("followup_transform", _retrieval_payload(followup_retrieval_value)),
    ]
    skipped = []
    for source, retrieval in candidates:
        if not isinstance(retrieval, dict) or not retrieval:
            continue
        if retrieval.get("skipped"):
            skipped.append({"source": source, "skip_reason": retrieval.get("skip_reason", "")})
            continue
        merged = deepcopy(retrieval)
        merged["merged_from"] = source
        if skipped:
            merged["skipped_retrieval_branches"] = skipped
        return {"retrieval_payload": merged}
    return {
        "retrieval_payload": {
            "skipped": True,
            "skip_reason": "No active retrieval branch produced a retrieval payload.",
            "source_results": [],
            "skipped_retrieval_branches": skipped,
        }
    }


class RetrievalPayloadMerger(Component):
    display_name = "Retrieval Payload Merger"
    description = "Merge single, multi, and follow-up retrieval branches before postprocess routing."
    icon = "Merge"
    name = "RetrievalPayloadMerger"

    inputs = [
        DataInput(name="single_retrieval", display_name="Single Retrieval", info="Output from single retrieval node.", input_types=["Data", "JSON"]),
        DataInput(name="multi_retrieval", display_name="Multi Retrieval", info="Output from multi retrieval node.", input_types=["Data", "JSON"]),
        DataInput(name="followup_retrieval", display_name="Follow-up Retrieval", info="Output from Current Data Retriever.", input_types=["Data", "JSON"]),
    ]
    outputs = [Output(name="retrieval_payload", display_name="Retrieval Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = merge_retrieval_payloads(getattr(self, "single_retrieval", None), getattr(self, "multi_retrieval", None), getattr(self, "followup_retrieval", None))
        retrieval = payload.get("retrieval_payload", {})
        self.status = {"merged_from": retrieval.get("merged_from"), "route": retrieval.get("route"), "skipped": retrieval.get("skipped", False)}
        return _make_data(payload)

