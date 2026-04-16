from __future__ import annotations

# VISIBLE_STANDALONE_RUNTIME: visible per-node standalone code with no hidden source bundle.

# ---- visible runtime: component_base ----
"""Helpers shared by standalone Langflow custom components.

This package is meant to be copied into a Langflow custom-component folder, so
the wrappers below keep the nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""
from dataclasses import dataclass as __lf_component_base__dataclass
from typing import Any as __lf_component_base__Any, Dict as __lf_component_base__Dict

def __lf_component_base___build_simple_data(payload: __lf_component_base__Dict[str, __lf_component_base__Any], text: str | None=None):

    @__lf_component_base__dataclass
    class SimpleData:
        data: __lf_component_base__Dict[str, __lf_component_base__Any]
        text: str | None = None
    return SimpleData(data=payload, text=text)
try:
    from lfx.custom.custom_component.component import Component as __lf_component_base__Component
    from lfx.io import DataInput as __lf_component_base__DataInput, MessageInput as __lf_component_base__MessageInput, MessageTextInput as __lf_component_base__MessageTextInput, MultilineInput as __lf_component_base__MultilineInput, Output as __lf_component_base__Output
    from lfx.schema import Data as __lf_component_base__Data
except Exception:
    try:
        from langflow.custom import Component as __lf_component_base__Component
        from langflow.io import DataInput as __lf_component_base__DataInput, MessageInput as __lf_component_base__MessageInput, MessageTextInput as __lf_component_base__MessageTextInput, MultilineInput as __lf_component_base__MultilineInput, Output as __lf_component_base__Output
        from langflow.schema import Data as __lf_component_base__Data
    except Exception:

        class __lf_component_base__Component:
            display_name = ''
            description = ''
            documentation = ''
            icon = ''
            name = ''
            inputs = []
            outputs = []
            status = ''

        @__lf_component_base__dataclass
        class __lf_component_base___Input:
            name: str
            display_name: str
            info: str = ''
            value: __lf_component_base__Any = None
            tool_mode: bool = False
            advanced: bool = False

        @__lf_component_base__dataclass
        class __lf_component_base__Output:
            name: str
            display_name: str
            method: str
            group_outputs: bool = False
            types: list[str] | None = None
            selected: str | None = None

        def __lf_component_base__MessageTextInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        def __lf_component_base__MultilineInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        def __lf_component_base__DataInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        def __lf_component_base__MessageInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        class __lf_component_base__Data:

            def __init__(self, data: __lf_component_base__Dict[str, __lf_component_base__Any] | None=None, text: str | None=None):
                self.data = data or {}
                self.text = text

def __lf_component_base__make_data(payload: __lf_component_base__Dict[str, __lf_component_base__Any], text: str | None=None):
    """Return a Data-like object in both Langflow and local test environments."""
    try:
        return __lf_component_base__Data(data=payload, text=text)
    except TypeError:
        try:
            return __lf_component_base__Data(payload)
        except Exception:
            return __lf_component_base___build_simple_data(payload, text=text)

def __lf_component_base__make_branch_data(active: bool, payload: __lf_component_base__Dict[str, __lf_component_base__Any], text: str | None=None):
    """Emit data only for the active branch output."""
    if not active:
        return None
    return __lf_component_base__make_data(payload, text=text)

def __lf_component_base__read_data_payload(value: __lf_component_base__Any) -> __lf_component_base__Dict[str, __lf_component_base__Any]:
    """Normalize Langflow Data, plain dict, or None into a regular dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, 'data', None)
    if isinstance(data, dict):
        return data
    if hasattr(value, 'dict'):
        try:
            result = value.dict()
            if isinstance(result, dict):
                return result
        except Exception:
            return {}
    return {}

def __lf_component_base__read_state_payload(value: __lf_component_base__Any) -> __lf_component_base__Dict[str, __lf_component_base__Any]:
    """Read a Langflow payload and unwrap the nested ``state`` field when present."""
    payload = __lf_component_base__read_data_payload(value)
    state = payload.get('state')
    if isinstance(state, dict):
        return state
    return payload if isinstance(payload, dict) else {}

# ---- node component ----
import sys
from pathlib import Path

Component = __lf_component_base__Component
MultilineInput = __lf_component_base__MultilineInput
Output = __lf_component_base__Output
make_data = __lf_component_base__make_data


class DomainRulesComponent(Component):
    display_name = "Domain Rules"
    description = "Provide free-text manufacturing domain notes used during planning and extraction."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "ScrollText"
    name = "domain_rules"

    inputs = [
        MultilineInput(
            name="domain_rules_text",
            display_name="Rules Text",
            info="Optional free-text domain notes. This is appended to the runtime prompt as-is.",
            value="",
        )
    ]
    outputs = [Output(name="rules", display_name="Rules", method="build_rules", types=["Data"], selected="Data")]

    def build_rules(self):
        text = str(getattr(self, "domain_rules_text", "") or "").strip()
        self.status = "Domain rules loaded" if text else "No domain rules text"
        return make_data({"domain_rules_text": text}, text=text)
