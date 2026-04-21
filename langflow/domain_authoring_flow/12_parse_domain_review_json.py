from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# Compatibility scaffolding for local tests. In lfx Langflow this can be
# replaced with direct imports from lfx.custom, lfx.io, and lfx.schema.
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
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


VALID_STATUSES = {"active", "review_required", "rejected"}


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
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return {"llm_text": text}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _extract_json_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("llm_text", "review_text", "text"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    if payload:
        return json.dumps(payload, ensure_ascii=False)
    return ""


def _parse_json_block(text: str) -> tuple[Dict[str, Any], list[str]]:
    cleaned = str(text or "").strip()
    if not cleaned:
        return {}, ["Semantic review LLM result is empty."]
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    try:
        parsed = json.loads(cleaned)
    except Exception as exc:
        return {}, [f"Semantic review JSON parse failed: {exc}"]
    if not isinstance(parsed, dict):
        return {}, ["Semantic review JSON root must be an object."]
    return parsed, []


def parse_domain_review_json(value: Any) -> Dict[str, Any]:
    parsed, parse_errors = _parse_json_block(_extract_json_text(value))
    review = parsed.get("semantic_review") if isinstance(parsed.get("semantic_review"), dict) else parsed
    if not isinstance(review, dict):
        review = {}
    status = str(review.get("recommended_status") or "active").strip().lower()
    if status not in VALID_STATUSES:
        parse_errors.append(f"Unknown semantic recommended_status '{status}'; using review_required.")
        status = "review_required"
    if parse_errors:
        status = "review_required"
    try:
        confidence = float(review.get("confidence", 0.0))
    except Exception:
        confidence = 0.0
    semantic_review = {
        "semantic_conflicts": [item for item in _as_list(review.get("semantic_conflicts")) if item],
        "semantic_warnings": [str(item) for item in _as_list(review.get("semantic_warnings")) if str(item).strip()],
        "recommended_status": status,
        "confidence": max(0.0, min(1.0, confidence)),
        "parse_errors": parse_errors,
    }
    return {"semantic_review": semantic_review}


class ParseDomainReviewJson(Component):
    display_name = "Parse Domain Review JSON"
    description = "Parse semantic review LLM output into a compact semantic_review payload."
    icon = "Braces"
    name = "ParseDomainReviewJson"

    inputs = [
        DataInput(name="llm_result", display_name="LLM Result", info="Output from Domain Review LLM Caller.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="semantic_review", display_name="Semantic Review", method="build_semantic_review", types=["Data"]),
    ]

    def build_semantic_review(self) -> Data:
        return _make_data(parse_domain_review_json(getattr(self, "llm_result", None)))
