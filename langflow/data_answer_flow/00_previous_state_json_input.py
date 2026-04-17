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
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any], text: str | None = None) -> Any:
    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload, text=text)


class PreviousStateJsonInput(Component):
    display_name = "Previous State JSON Input"
    description = "Manual state_json input for multi-turn Langflow runs. Leave empty on the first turn."
    icon = "History"
    name = "PreviousStateJsonInput"

    inputs = [
        MultilineInput(
            name="previous_state_json",
            display_name="Previous State JSON",
            info="Paste the state_json returned by the previous turn. Leave empty on the first turn.",
            value="",
        ),
    ]

    outputs = [
        Output(name="previous_state_payload", display_name="Previous State Payload", method="build_payload", types=["Data"]),
    ]

    def build_payload(self) -> Any:
        text = str(getattr(self, "previous_state_json", "") or "").strip()
        valid_json = False
        if text:
            try:
                json.loads(text)
                valid_json = True
            except Exception:
                valid_json = False
        payload = {
            "previous_state_json": text,
            "state_json": text,
            "is_empty": not bool(text),
            "valid_json": valid_json,
        }
        return _make_data(payload, text=text)
