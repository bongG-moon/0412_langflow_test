"""Helpers shared by Langflow custom components.

These wrappers keep the custom nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


def _build_simple_data(payload: Dict[str, Any], text: str | None = None):
    @dataclass
    class SimpleData:
        data: Dict[str, Any]
        text: str | None = None

    return SimpleData(data=payload, text=text)


try:  # Langflow 1.7+ style
    from lfx.custom.custom_component.component import Component
    from lfx.io import DataInput, MessageTextInput, MultilineInput, Output
    from lfx.schema import Data
except Exception:  # pragma: no cover - fallback branch depends on environment
    try:  # Older compatible import path
        from langflow.custom import Component
        from langflow.io import DataInput, MessageTextInput, MultilineInput, Output
        from langflow.schema import Data
    except Exception:  # Local test fallback
        class Component:
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

        @dataclass
        class Output:
            name: str
            display_name: str
            method: str
            group_outputs: bool = False

        def MessageTextInput(**kwargs):
            return _Input(**kwargs)

        def MultilineInput(**kwargs):
            return _Input(**kwargs)

        def DataInput(**kwargs):
            return _Input(**kwargs)

        class Data:  # pragma: no cover - only used without Langflow
            def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
                self.data = data or {}
                self.text = text


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
