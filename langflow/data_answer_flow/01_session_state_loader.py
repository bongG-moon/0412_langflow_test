from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# The `_load_attr` function, `_Fallback*` classes, and `_make_input` helper below
# are compatibility scaffolding for standalone local tests or mixed Langflow
# versions. In the actual lfx-based Langflow environment, this block is not
# required and can be replaced with direct imports such as:
#   from lfx.custom import Component
#   from lfx.io import DataInput, MessageTextInput, MultilineInput, Output
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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
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
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _parse_state_text(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    payload = _payload_from_value(value)
    if payload:
        state = payload.get("state")
        if isinstance(state, dict):
            return state
        if isinstance(payload.get("state_json"), str):
            return _parse_state_text(payload["state_json"])
        return payload
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    if isinstance(parsed, dict):
        if isinstance(parsed.get("state"), dict):
            return parsed["state"]
        if isinstance(parsed.get("state_json"), str):
            return _parse_state_text(parsed["state_json"])
        return parsed
    return {}


def _default_state(session_id: str) -> Dict[str, Any]:
    return {
        "session_id": session_id or "default",
        "turn_id": 0,
        "chat_history": [],
        "context": {},
        "source_snapshots": {},
        "current_data": None,
    }


def load_session_state(previous_state_json: Any, session_id: str, user_question: str) -> Dict[str, Any]:
    state = _parse_state_text(previous_state_json)
    if not state:
        state = _default_state(session_id)

    state = dict(state)
    state["session_id"] = str(session_id or state.get("session_id") or "default")
    try:
        state["turn_id"] = int(state.get("turn_id") or 0) + 1
    except Exception:
        state["turn_id"] = 1

    chat_history = state.get("chat_history")
    state["chat_history"] = chat_history if isinstance(chat_history, list) else []
    state["context"] = state.get("context") if isinstance(state.get("context"), dict) else {}
    source_snapshots = state.get("source_snapshots")
    state["source_snapshots"] = source_snapshots if isinstance(source_snapshots, dict) else {}
    if "current_data" not in state:
        state["current_data"] = None

    state["pending_user_question"] = str(user_question or "")
    state["state_errors"] = []
    return state


class SessionStateLoader(Component):
    display_name = "Session State Loader"
    description = "Parse previous state JSON and prepare the state for this turn."
    icon = "Database"
    name = "SessionStateLoader"

    inputs = [
        DataInput(
            name="previous_state_payload",
            display_name="Previous State Payload",
            info="Optional output from Previous State JSON Input.",
            input_types=["Data", "JSON"],
        ),
        MultilineInput(
            name="previous_state_json",
            display_name="Previous State JSON",
            info="State JSON returned from the previous turn. Leave empty on the first turn.",
            value="",
        ),
        MessageTextInput(
            name="session_id",
            display_name="Session ID",
            value="default",
            info="Session identifier used in the returned state payload.",
        ),
        MessageTextInput(
            name="user_question",
            display_name="User Question",
            info="Current user question from Chat Input.",
        ),
    ]

    outputs = [
        Output(name="agent_state", display_name="Agent State", method="build_agent_state", types=["Data"]),
    ]

    def build_agent_state(self) -> Data:
        previous_state_source = getattr(self, "previous_state_payload", None) or getattr(self, "previous_state_json", "")
        state = load_session_state(
            previous_state_source,
            getattr(self, "session_id", "default"),
            getattr(self, "user_question", ""),
        )
        return _make_data({"agent_state": state, "state": state})
