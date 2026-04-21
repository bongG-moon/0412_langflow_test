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
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


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


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        for key in ("llm_text", "text", "output", "content", "result"):
            if isinstance(data.get(key), str):
                return data[key].strip()
        if isinstance(data.get("message"), dict) and isinstance(data["message"].get("text"), str):
            return data["message"]["text"].strip()
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
    return str(value or "").strip()


def _parse_json_block(text: str) -> tuple[Dict[str, Any], list[str]]:
    errors: list[str] = []
    cleaned = str(text or "").strip()
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
        errors.append(f"LLM JSON parse failed: {exc}")
        return {}, errors
    if not isinstance(parsed, dict):
        errors.append("LLM JSON root must be an object.")
        return {}, errors
    return parsed, errors


def parse_domain_item_json(llm_output: Any) -> Dict[str, Any]:
    text = _extract_text(llm_output)
    parsed, errors = _parse_json_block(text)
    items = parsed.get("items") if isinstance(parsed.get("items"), list) else []
    if not items and all(key in parsed for key in ("gbn", "key", "payload")):
        items = [parsed]
    return {
        "domain_items_raw": items,
        "unmapped_text": str(parsed.get("unmapped_text") or "").strip() if isinstance(parsed, dict) else "",
        "parse_errors": errors,
        "llm_text_chars": len(text),
    }


class ParseDomainItemJSON(Component):
    display_name = "Parse Domain Item JSON"
    description = "Parse JSON text from a built-in LLM node into raw domain item candidates."
    icon = "Braces"
    name = "ParseDomainItemJSON"

    inputs = [
        DataInput(
            name="llm_output",
            display_name="LLM Output",
            info="Output from a built-in LLM node, custom LLM node, Message, or Data payload.",
            input_types=["Data", "Message", "Text", "JSON"],
        ),
    ]

    outputs = [
        Output(name="domain_items_raw", display_name="Domain Items Raw", method="build_items", types=["Data"]),
    ]

    def build_items(self) -> Data:
        return _make_data(parse_domain_item_json(getattr(self, "llm_output", None)))
