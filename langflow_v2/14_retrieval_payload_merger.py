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

