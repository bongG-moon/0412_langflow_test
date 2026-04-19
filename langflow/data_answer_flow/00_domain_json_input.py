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


class DomainJsonInput(Component):
    display_name = "Domain JSON Input"
    description = "Manual Domain JSON text input used before MongoDB domain loading is available."
    icon = "Braces"
    name = "DomainJsonInput"

    inputs = [
        MultilineInput(
            name="domain_json_text",
            display_name="Domain JSON Text",
            info="Paste the standard Domain JSON document or a bare domain object.",
            value="",
        ),
    ]

    outputs = [
        Output(name="domain_json_payload", display_name="Domain JSON Payload", method="build_payload", types=["Data"]),
    ]

    def build_payload(self) -> Data:
        text = str(getattr(self, "domain_json_text", "") or "").strip()
        valid_json = False
        if text:
            try:
                json.loads(text)
                valid_json = True
            except Exception:
                valid_json = False
        payload = {
            "domain_json_text": text,
            "domain_json": text,
            "is_empty": not bool(text),
            "valid_json": valid_json,
        }
        return _make_data(payload, text=text)
