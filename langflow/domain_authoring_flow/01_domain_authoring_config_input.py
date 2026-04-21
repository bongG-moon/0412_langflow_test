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


def _normalize_choice(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in allowed else default


class DomainAuthoringConfigInput(Component):
    display_name = "Domain Authoring Config Input"
    description = "Build configuration for creating or updating a manufacturing Domain JSON document."
    icon = "Settings"
    name = "DomainAuthoringConfigInput"

    inputs = [
        MessageTextInput(name="domain_id", display_name="Domain ID", value="manufacturing_default", advanced=True),
        MessageTextInput(
            name="authoring_mode",
            display_name="Authoring Mode",
            info="create, append, update, or validate_only",
            value="append",
            advanced=True,
        ),
        MessageTextInput(
            name="target_status",
            display_name="Target Status",
            info="draft or active",
            value="active",
            advanced=True,
        ),
        MessageTextInput(
            name="display_name",
            display_name="Display Name",
            value="제조 분석 도메인",
            advanced=True,
        ),
        MessageTextInput(
            name="description",
            display_name="Description",
            value="Domain Authoring Flow에서 생성한 제조 분석 도메인",
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="authoring_config", display_name="Authoring Config", method="build_config", types=["Data"]),
    ]

    def build_config(self) -> Data:
        payload = {
            "domain_id": str(getattr(self, "domain_id", "") or "manufacturing_default").strip(),
            "authoring_mode": _normalize_choice(
                getattr(self, "authoring_mode", "append"),
                {"create", "append", "update", "validate_only"},
                "append",
            ),
            "target_status": _normalize_choice(getattr(self, "target_status", "active"), {"draft", "active"}, "active"),
            "metadata": {
                "display_name": str(getattr(self, "display_name", "") or "").strip(),
                "description": str(getattr(self, "description", "") or "").strip(),
            },
        }
        if not payload["domain_id"]:
            payload["domain_id"] = "manufacturing_default"
        return _make_data({"authoring_config": payload})
