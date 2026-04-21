from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# The `_load_attr` function, `_Fallback*` classes, and `_make_input` helper below
# are compatibility scaffolding for standalone local tests or mixed Langflow
# versions. In the actual lfx-based Langflow environment, this block is not
# required and can be replaced with direct imports such as:
#   from lfx.custom import Component
#   from lfx.io import DataInput, MultilineInput, Output
#   from lfx.schema import Data
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


# In the actual lfx Langflow runtime, these resolve to real Langflow classes.
# The fallback argument is only used outside Langflow or when import paths differ.
Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


DEFAULT_INTENT: Dict[str, Any] = {
    "request_type": "unknown",
    "query_summary": "",
    "dataset_hints": [],
    "metric_hints": [],
    "required_params": {},
    "filters": {},
    "group_by": [],
    "sort": None,
    "top_n": None,
    "calculation_hints": [],
    "followup_cues": [],
    "confidence": 0.0,
}


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
        return {"text": text}
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return {"text": content}
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return {"text": "\n".join(parts)}
    return {}


def _read_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("llm_text", "text", "content"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return text.strip()
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(text or "").strip()


def _extract_json_object(text: str) -> str:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _normalize_intent_shape(value: Any, errors: list[str]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("Parsed intent is not an object.")
        return dict(DEFAULT_INTENT)
    intent = dict(DEFAULT_INTENT)
    intent.update(value)

    if intent.get("request_type") not in {"data_question", "process_execution", "unknown"}:
        errors.append("Invalid request_type; using unknown.")
        intent["request_type"] = "unknown"

    for key in ("dataset_hints", "metric_hints", "group_by", "calculation_hints", "followup_cues"):
        intent[key] = [str(item) for item in _as_list(intent.get(key)) if str(item).strip()]

    if not isinstance(intent.get("required_params"), dict):
        intent["required_params"] = {}
    if not isinstance(intent.get("filters"), dict):
        intent["filters"] = {}
    if intent.get("sort") is not None and not isinstance(intent.get("sort"), dict):
        intent["sort"] = None
    try:
        intent["confidence"] = float(intent.get("confidence") or 0.0)
    except Exception:
        intent["confidence"] = 0.0
    return intent


def parse_intent_json(llm_text: Any) -> Dict[str, Any]:
    text = _read_text(llm_text)
    errors: list[str] = []
    if not text:
        errors.append("llm_text is empty.")
        intent = dict(DEFAULT_INTENT)
    else:
        try:
            parsed = json.loads(_extract_json_object(text))
            intent = _normalize_intent_shape(parsed, errors)
        except Exception as exc:
            errors.append(f"Intent JSON parse failed: {exc}")
            intent = dict(DEFAULT_INTENT)
    return {"intent_raw": intent, "parse_errors": errors}


class ParseIntentJson(Component):
    display_name = "Parse Intent JSON"
    description = "Parse the LLM response into a normalized intent JSON object."
    icon = "Braces"
    name = "ParseIntentJson"

    inputs = [
        DataInput(
            name="llm_result",
            display_name="LLM Result",
            info="Output from a built-in LLM node or optional LLM JSON Caller.",
            input_types=["Data", "Message", "Text", "JSON"],
        ),
        MultilineInput(name="llm_text", display_name="LLM Text", value="", advanced=True),
    ]

    outputs = [
        Output(name="intent_raw", display_name="Intent Raw", method="build_intent_raw", types=["Data"]),
    ]

    def build_intent_raw(self) -> Data:
        value = getattr(self, "llm_result", None) or getattr(self, "llm_text", "")
        payload = parse_intent_json(value)
        return _make_data(payload)
