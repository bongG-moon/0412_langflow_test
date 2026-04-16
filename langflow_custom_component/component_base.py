"""Helpers shared by standalone Langflow custom components.

This package is meant to be copied into a Langflow custom-component folder, so
the wrappers below keep the nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    """Load a Langflow class while keeping direct-paste validation friendly."""

    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback


class _FallbackComponent:
    display_name = ""
    description = ""
    documentation = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""


@dataclass
class _Input:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    tool_mode: bool = False
    advanced: bool = False


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:  # pragma: no cover - only used without Langflow
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text


def _make_input(**kwargs):
    return _Input(**kwargs)


def _build_simple_data(payload: Dict[str, Any], text: str | None = None):
    @dataclass
    class SimpleData:
        data: Dict[str, Any]
        text: str | None = None

    return SimpleData(data=payload, text=text)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageInput = _load_attr(["lfx.io", "langflow.io"], "MessageInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def make_data(payload: Dict[str, Any], text: str | None = None):
    """Return a Data-like object in both Langflow and local test environments."""

    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _build_simple_data(payload, text=text)


def make_branch_data(active: bool, payload: Dict[str, Any], text: str | None = None):
    """Emit data only for the active branch output."""

    if not active:
        return None
    return make_data(payload, text=text)


def read_data_payload(value: Any) -> Dict[str, Any]:
    """Normalize Langflow Data, plain dict, or None into a regular dict."""

    if value is None:
        return {}
    if isinstance(value, dict):
        return value

    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data

    if hasattr(value, "dict"):
        try:
            result = value.dict()
            if isinstance(result, dict):
                return result
        except Exception:
            return {}
    return {}


def read_state_payload(value: Any) -> Dict[str, Any]:
    """Read a Langflow payload and unwrap the nested ``state`` field when present."""

    payload = read_data_payload(value)
    state = payload.get("state")
    if isinstance(state, dict):
        return state
    return payload if isinstance(payload, dict) else {}
