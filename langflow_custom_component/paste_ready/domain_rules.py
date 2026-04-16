from __future__ import annotations

# VISIBLE_STANDALONE_RUNTIME: visible per-node standalone code with no hidden source bundle.

# ---- visible runtime: component_base ----
"""Helpers shared by standalone Langflow custom components.

This package is meant to be copied into a Langflow custom-component folder, so
the wrappers below keep the nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""
import dataclasses as lf_component_base_import_dataclasses
lf_component_base_dataclass = lf_component_base_import_dataclasses.dataclass
import importlib as lf_component_base_import_importlib
lf_component_base_import_module = lf_component_base_import_importlib.import_module
import typing as lf_component_base_import_typing
lf_component_base_Any = lf_component_base_import_typing.Any
lf_component_base_Dict = lf_component_base_import_typing.Dict

def lf_component_base__load_attr(module_names: list[str], attr_name: str, fallback: lf_component_base_Any) -> lf_component_base_Any:
    """Load a Langflow class while keeping direct-paste validation friendly."""
    for module_name in module_names:
        try:
            return getattr(lf_component_base_import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback

class lf_component_base__FallbackComponent:
    display_name = ''
    description = ''
    documentation = ''
    icon = ''
    name = ''
    inputs = []
    outputs = []
    status = ''

@lf_component_base_dataclass
class lf_component_base__Input:
    name: str
    display_name: str
    info: str = ''
    value: lf_component_base_Any = None
    tool_mode: bool = False
    advanced: bool = False

@lf_component_base_dataclass
class lf_component_base__FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None

class lf_component_base__FallbackData:

    def __init__(self, data: lf_component_base_Dict[str, lf_component_base_Any] | None=None, text: str | None=None):
        self.data = data or {}
        self.text = text

def lf_component_base__make_input(**kwargs):
    return lf_component_base__Input(**kwargs)

def lf_component_base__build_simple_data(payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):

    @lf_component_base_dataclass
    class SimpleData:
        data: lf_component_base_Dict[str, lf_component_base_Any]
        text: str | None = None
    return SimpleData(data=payload, text=text)
lf_component_base_Component = lf_component_base__load_attr(['lfx.custom.custom_component.component', 'lfx.custom', 'langflow.custom'], 'Component', lf_component_base__FallbackComponent)
lf_component_base_DataInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'DataInput', lf_component_base__make_input)
lf_component_base_MessageInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MessageInput', lf_component_base__make_input)
lf_component_base_MessageTextInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MessageTextInput', lf_component_base__make_input)
lf_component_base_MultilineInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MultilineInput', lf_component_base__make_input)
lf_component_base_SecretStrInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'SecretStrInput', lf_component_base__make_input)
lf_component_base_Output = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'Output', lf_component_base__FallbackOutput)
lf_component_base_Data = lf_component_base__load_attr(['lfx.schema.data', 'lfx.schema', 'langflow.schema'], 'Data', lf_component_base__FallbackData)

def lf_component_base_make_data(payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):
    """Return a Data-like object in both Langflow and local test environments."""
    try:
        return lf_component_base_Data(data=payload, text=text)
    except TypeError:
        try:
            return lf_component_base_Data(payload)
        except Exception:
            return lf_component_base__build_simple_data(payload, text=text)

def lf_component_base_make_branch_data(active: bool, payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):
    """Emit data only for the active branch output."""
    if not active:
        return None
    return lf_component_base_make_data(payload, text=text)

def lf_component_base_read_data_payload(value: lf_component_base_Any) -> lf_component_base_Dict[str, lf_component_base_Any]:
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

def lf_component_base_read_state_payload(value: lf_component_base_Any) -> lf_component_base_Dict[str, lf_component_base_Any]:
    """Read a Langflow payload and unwrap the nested ``state`` field when present."""
    payload = lf_component_base_read_data_payload(value)
    state = payload.get('state')
    if isinstance(state, dict):
        return state
    return payload if isinstance(payload, dict) else {}

# ---- node component ----
import sys
from pathlib import Path

Component = lf_component_base_Component
MultilineInput = lf_component_base_MultilineInput
Output = lf_component_base_Output
make_data = lf_component_base_make_data


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
