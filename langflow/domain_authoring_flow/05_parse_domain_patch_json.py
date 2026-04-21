from __future__ import annotations

import json
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


ROOT_KEYS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
LEGACY_KEYS = ("dataset_keywords", "value_groups", "analysis_rules")


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


def _extract_json_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("llm_text", "domain_patch_text", "text"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    if payload:
        return json.dumps(payload, ensure_ascii=False)
    return ""


def _parse_json_block(text: str) -> tuple[Dict[str, Any], list[str]]:
    errors: list[str] = []
    cleaned = str(text or "").strip()
    if not cleaned:
        return {}, ["LLM result is empty."]
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
        return {}, [f"Domain patch JSON parse failed: {exc}"]
    if not isinstance(parsed, dict):
        return {}, ["Domain patch JSON root must be an object."]
    return parsed, errors


def parse_domain_patch_json(value: Any) -> Dict[str, Any]:
    text = _extract_json_text(value)
    parsed, errors = _parse_json_block(text)
    patch: Dict[str, Any] = {}
    if isinstance(parsed.get("domain_patch"), dict):
        patch = parsed["domain_patch"]
    elif isinstance(parsed.get("domain"), dict):
        patch = parsed["domain"]
    elif any(key in parsed for key in (*ROOT_KEYS, *LEGACY_KEYS)):
        patch = {key: parsed.get(key) for key in (*ROOT_KEYS, *LEGACY_KEYS) if key in parsed}
    else:
        patch = {}
        if parsed:
            errors.append("No domain_patch or domain object found in LLM result.")

    return {
        "domain_patch": patch,
        "warnings": parsed.get("warnings", []) if isinstance(parsed.get("warnings"), list) else [],
        "parse_errors": errors,
    }


class ParseDomainPatchJson(Component):
    display_name = "Parse Domain Patch JSON"
    description = "Parse the LLM domain structuring result into a domain_patch payload."
    icon = "Braces"
    name = "ParseDomainPatchJson"

    inputs = [
        DataInput(name="llm_result", display_name="LLM Result", info="Output from Domain Authoring LLM JSON Caller.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="domain_patch", display_name="Domain Patch", method="build_domain_patch", types=["Data"]),
    ]

    def build_domain_patch(self) -> Data:
        return _make_data(parse_domain_patch_json(getattr(self, "llm_result", None)))
