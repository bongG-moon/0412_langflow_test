from __future__ import annotations

import json
import re
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
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"raw_text": text}
        except Exception:
            return {"raw_text": text}
    return {}


def _clean_note(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned)
    cleaned = re.sub(r"^\s*\d+[\).\-\s]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _split_raw_text(raw_text: str) -> list[str]:
    normalized = str(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [_clean_note(line) for line in normalized.split("\n")]
    notes = [line for line in lines if line]
    if len(notes) <= 1:
        parts = [_clean_note(part) for part in re.split(r"(?<=[.!?。])\s+", normalized)]
        notes = [part for part in parts if part]
    return notes or ([_clean_note(normalized)] if _clean_note(normalized) else [])


def split_domain_text(raw_payload: Any) -> Dict[str, Any]:
    payload = _payload_from_value(raw_payload)
    raw_text = str(payload.get("raw_text") or payload.get("text") or "").strip()
    notes = []
    for idx, note in enumerate(_split_raw_text(raw_text), start=1):
        notes.append({"note_id": f"note_{idx}", "raw_text": note})
    return {
        "raw_text": raw_text,
        "combined_raw_text": "\n".join(note["raw_text"] for note in notes),
        "raw_notes": notes,
        "note_count": len(notes),
        "source": payload.get("source") or "domain_item_authoring_flow",
        "is_empty": not bool(raw_text),
    }


class DomainTextSplitter(Component):
    display_name = "Domain Text Splitter"
    description = "Split multi-line domain input into raw_notes so one LLM call can extract multiple items."
    icon = "ListTree"
    name = "DomainTextSplitter"

    inputs = [
        DataInput(name="raw_domain_payload", display_name="Raw Domain Payload", info="Output from Raw Domain Text Input.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="split_domain_payload", display_name="Split Domain Payload", method="build_split_payload", types=["Data"]),
    ]

    def build_split_payload(self) -> Data:
        return _make_data(split_domain_text(getattr(self, "raw_domain_payload", None)))
