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
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("user_question", "question", "text", "content", "message", "state_json"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None) or getattr(value, "content", None)
    return str(text or "").strip()


def _as_dict_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("state") or payload.get("agent_state")
    if isinstance(state, dict):
        return deepcopy(state)
    if isinstance(payload.get("state_json"), str):
        try:
            parsed = json.loads(payload["state_json"])
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return deepcopy(payload) if payload else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def load_state(user_question_value: Any, previous_state_value: Any = None, session_id_value: Any = "") -> Dict[str, Any]:
    previous_state = _as_dict_state(previous_state_value)
    user_question = _text_from_value(user_question_value) or str(previous_state.get("pending_user_question") or "").strip()
    session_id = str(session_id_value or previous_state.get("session_id") or "default").strip()

    state = {
        "session_id": session_id,
        "chat_history": [item for item in _as_list(previous_state.get("chat_history")) if isinstance(item, dict)],
        "context": deepcopy(previous_state.get("context")) if isinstance(previous_state.get("context"), dict) else {},
        "current_data": deepcopy(previous_state.get("current_data")) if isinstance(previous_state.get("current_data"), dict) else None,
        "source_snapshots": deepcopy(previous_state.get("source_snapshots")) if previous_state.get("source_snapshots") else [],
        "last_intent": deepcopy(previous_state.get("last_intent")) if isinstance(previous_state.get("last_intent"), dict) else {},
        "last_retrieval_plan": deepcopy(previous_state.get("last_retrieval_plan")) if isinstance(previous_state.get("last_retrieval_plan"), dict) else {},
        "pending_user_question": user_question,
    }
    return {"user_question": user_question, "state": state}


class StateLoader(Component):
    display_name = "V2 State Loader"
    description = "Standalone state loader for the simplified manufacturing Langflow v2 flow."
    icon = "ArchiveRestore"
    name = "V2StateLoader"

    inputs = [
        MessageTextInput(name="user_question", display_name="User Question", info="Current chat input."),
        DataInput(name="previous_state", display_name="Previous State", info="Optional output from V2 Final Answer Builder.next_state.", input_types=["Data", "JSON"], advanced=True),
        MessageTextInput(name="session_id", display_name="Session ID", value="default", advanced=True),
    ]

    outputs = [Output(name="state_payload", display_name="State Payload", method="build_state", types=["Data"])]

    def build_state(self):
        payload = load_state(getattr(self, "user_question", ""), getattr(self, "previous_state", None), getattr(self, "session_id", "default"))
        state = payload["state"]
        self.status = {
            "session_id": state.get("session_id"),
            "chat_turns": len(state.get("chat_history", [])),
            "has_current_data": bool(state.get("current_data")),
        }
        return _make_data(payload)
