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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)

DEFAULT_MEMORY_MARKER = "__LANGFLOW_V2_AGENT_STATE__"


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


def _text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("text", "content", "message", "msg", "messages_text"):
            if isinstance(value.get(key), str):
                return value[key]
        data = value.get("data") if isinstance(value.get("data"), dict) else {}
        for key in ("text", "content", "message", "msg", "messages_text"):
            if isinstance(data.get(key), str):
                return data[key]
    text = getattr(value, "text", None) or getattr(value, "content", None) or getattr(value, "messages_text", None)
    return str(text or "")


def _collect_texts(value: Any, depth: int = 0) -> list[str]:
    if depth > 8 or value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        texts: list[str] = []
        for item in value:
            texts.extend(_collect_texts(item, depth + 1))
        return texts

    payload = _payload_from_value(value)
    texts: list[str] = []
    for key in ("messages", "data", "rows", "records", "items", "result", "value"):
        nested = payload.get(key) if isinstance(payload, dict) else None
        if nested is not None and nested is not payload:
            texts.extend(_collect_texts(nested, depth + 1))
    text = _text_from_value(value)
    if text:
        texts.append(text)
    return texts


def _json_objects_from_text(text: str) -> list[Dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[Dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except Exception:
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
    return objects


def _state_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    state = record.get("state") or record.get("agent_state")
    if isinstance(state, dict):
        return deepcopy(state)
    state_json = record.get("state_json")
    if isinstance(state_json, str):
        try:
            parsed = json.loads(state_json)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def extract_previous_state(memory_messages_value: Any, marker_value: Any = DEFAULT_MEMORY_MARKER) -> Dict[str, Any]:
    marker = str(marker_value or DEFAULT_MEMORY_MARKER).strip() or DEFAULT_MEMORY_MARKER
    texts = _collect_texts(memory_messages_value)
    errors: list[str] = []
    selected: Dict[str, Any] = {}
    scanned_records = 0

    for text in reversed(texts):
        if marker not in text:
            continue
        records = [record for record in _json_objects_from_text(text) if record.get("marker") == marker]
        scanned_records += len(records)
        for record in reversed(records):
            state = _state_from_record(record)
            if state:
                selected = {
                    "state": state,
                    "state_json": json.dumps(state, ensure_ascii=False),
                    "memory_record": record,
                }
                break
        if selected:
            break
        errors.append("State marker was found, but no parseable state JSON was present.")

    if not selected:
        selected = {"state": {}, "state_json": "", "memory_record": {}}

    state = selected.get("state") if isinstance(selected.get("state"), dict) else {}
    return {
        "previous_state": {"state": state, "state_json": selected.get("state_json", "")},
        "state": state,
        "state_json": selected.get("state_json", ""),
        "memory_loaded": bool(state),
        "memory_message_count": len(texts),
        "memory_record_count": scanned_records,
        "memory_errors": errors,
    }


class StateMemoryExtractor(Component):
    display_name = "State Memory Extractor"
    description = "Extract the latest agent state from Langflow Message History output."
    icon = "ArchiveRestore"
    name = "StateMemoryExtractor"

    inputs = [
        DataInput(name="memory_messages", display_name="Memory Messages", info="Output from Langflow Message History in Retrieve mode.", input_types=["Data", "Message", "Text", "JSON"]),
        MessageTextInput(name="memory_marker", display_name="Memory Marker", value=DEFAULT_MEMORY_MARKER, advanced=True),
    ]
    outputs = [Output(name="previous_state", display_name="Previous State", method="build_previous_state", types=["Data"])]

    def build_previous_state(self):
        payload = extract_previous_state(getattr(self, "memory_messages", None), getattr(self, "memory_marker", DEFAULT_MEMORY_MARKER))
        self.status = {
            "memory_loaded": payload.get("memory_loaded", False),
            "messages": payload.get("memory_message_count", 0),
            "records": payload.get("memory_record_count", 0),
        }
        return _make_data(payload)

