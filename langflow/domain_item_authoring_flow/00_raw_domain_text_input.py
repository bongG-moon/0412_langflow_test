from __future__ import annotations

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


def build_raw_domain_payload(raw_text: Any) -> Dict[str, Any]:
    text = str(raw_text or "").strip()
    return {
        "raw_text": text,
        "source": "domain_item_authoring_flow",
        "is_empty": not bool(text),
    }


class RawDomainTextInput(Component):
    display_name = "Raw Domain Text Input"
    description = "Single text entry for product, process, term, dataset, metric, or join-rule domain notes."
    icon = "TextCursorInput"
    name = "RawDomainTextInput"

    inputs = [
        MultilineInput(
            name="raw_text",
            display_name="Raw Domain Text",
            info="Paste one or more domain notes. Multiple lines are split by Domain Text Splitter.",
            value="",
        ),
    ]

    outputs = [
        Output(name="raw_domain_payload", display_name="Raw Domain Payload", method="build_payload", types=["Data"]),
    ]

    def build_payload(self) -> Data:
        return _make_data(build_raw_domain_payload(getattr(self, "raw_text", "")))
