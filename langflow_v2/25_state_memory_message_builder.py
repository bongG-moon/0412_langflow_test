from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
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


class _FallbackMessage:
    def __init__(self, text: str | None = None, **kwargs: Any):
        self.text = text or str(kwargs.get("content") or "")
        self.content = self.text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)

DEFAULT_MEMORY_MARKER = "__LANGFLOW_V2_AGENT_STATE__"


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _make_message(text: str) -> Any:
    try:
        return Message(text=text)
    except TypeError:
        try:
            return Message(content=text)
        except TypeError:
            try:
                return Message(text)
            except Exception:
                return _FallbackMessage(text=text)


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


def _state_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("state") or payload.get("next_state") or payload.get("agent_state")
    if isinstance(state, dict):
        return deepcopy(state)
    state_json = payload.get("state_json")
    if isinstance(state_json, str):
        try:
            parsed = json.loads(state_json)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return deepcopy(payload) if payload.get("chat_history") or payload.get("current_data") else {}


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return str(value)


def build_state_memory_message(next_state_value: Any, marker_value: Any = DEFAULT_MEMORY_MARKER) -> Dict[str, Any]:
    marker = str(marker_value or DEFAULT_MEMORY_MARKER).strip() or DEFAULT_MEMORY_MARKER
    state = _json_safe(_state_from_value(next_state_value))
    if not isinstance(state, dict):
        state = {}
    record = {
        "marker": marker,
        "type": "langflow_v2_agent_state",
        "version": 1,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "session_id": state.get("session_id", "default"),
        "chat_turns": len(state.get("chat_history", [])) if isinstance(state.get("chat_history"), list) else 0,
        "has_current_data": isinstance(state.get("current_data"), dict) and bool(state.get("current_data")),
        "state": state,
    }
    text = json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str)
    return {
        "memory_payload": record,
        "memory_text": text,
        "state": state,
        "state_json": json.dumps(state, ensure_ascii=False, default=str),
    }


class StateMemoryMessageBuilder(Component):
    display_name = "State Memory Message Builder"
    description = "Build a Message History-compatible state snapshot message from Final Answer Builder.next_state."
    icon = "Save"
    name = "StateMemoryMessageBuilder"

    inputs = [
        DataInput(name="next_state", display_name="Next State", info="Output from Final Answer Builder.next_state.", input_types=["Data", "JSON"]),
        MessageTextInput(name="memory_marker", display_name="Memory Marker", value=DEFAULT_MEMORY_MARKER, advanced=True),
    ]
    outputs = [
        Output(name="memory_message", display_name="Memory Message", method="build_memory_message", group_outputs=True, types=["Message"]),
        Output(name="memory_payload", display_name="Memory Payload", method="build_memory_payload", group_outputs=True, types=["Data"]),
    ]

    def _payload(self) -> Dict[str, Any]:
        cached = getattr(self, "_cached_payload", None)
        if isinstance(cached, dict):
            return cached
        payload = build_state_memory_message(getattr(self, "next_state", None), getattr(self, "memory_marker", DEFAULT_MEMORY_MARKER))
        self._cached_payload = payload
        return payload

    def build_memory_message(self):
        payload = self._payload()
        self.status = {
            "session_id": payload.get("memory_payload", {}).get("session_id"),
            "chars": len(payload.get("memory_text", "")),
        }
        return _make_message(str(payload.get("memory_text", "")))

    def build_memory_payload(self):
        return _make_data(self._payload())

