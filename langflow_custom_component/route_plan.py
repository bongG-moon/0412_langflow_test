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

# ---- visible runtime: _runtime ----
"""Standalone runtime copied for Langflow custom components."""

# ---- visible runtime: _runtime.graph ----
"""Graph-state helpers used by standalone Langflow nodes."""

# ---- visible runtime: _runtime.graph.state ----
"""Shared state typing for standalone Langflow runtime."""
import typing as lf_runtime_graph_state_import_typing
lf_runtime_graph_state_Any = lf_runtime_graph_state_import_typing.Any
lf_runtime_graph_state_Dict = lf_runtime_graph_state_import_typing.Dict
lf_runtime_graph_state_List = lf_runtime_graph_state_import_typing.List
lf_runtime_graph_state_Literal = lf_runtime_graph_state_import_typing.Literal
lf_runtime_graph_state_TypedDict = lf_runtime_graph_state_import_typing.TypedDict
lf_runtime_graph_state_QueryMode = lf_runtime_graph_state_Literal['retrieval', 'followup_transform']

class lf_runtime_graph_state_AgentGraphState(lf_runtime_graph_state_TypedDict, total=False):
    user_input: str
    chat_history: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, str]]
    context: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    current_data: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any] | None
    domain_rules_text: str
    domain_registry_payload: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any] | lf_runtime_graph_state_List[lf_runtime_graph_state_Any]
    raw_extracted_params: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    extracted_params: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    query_mode: lf_runtime_graph_state_QueryMode
    retrieval_plan: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    retrieval_keys: lf_runtime_graph_state_List[str]
    retrieval_jobs: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]]
    source_results: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]]
    current_datasets: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    source_snapshots: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]]
    result: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]

# ---- visible runtime: _runtime.graph.builder ----
"""Small routing helpers that mirror the LangGraph branch contract."""
lf_runtime_graph_builder_AgentGraphState = lf_runtime_graph_state_AgentGraphState

def lf_runtime_graph_builder_route_after_resolve(state: lf_runtime_graph_builder_AgentGraphState) -> str:
    """Return the first visible branch after request resolution."""
    if state.get('query_mode') == 'followup_transform' and isinstance(state.get('current_data'), dict):
        return 'followup_analysis'
    return 'plan_retrieval'

def lf_runtime_graph_builder_route_after_retrieval_plan(state: lf_runtime_graph_builder_AgentGraphState) -> str:
    """Return finish / single / multi after retrieval planning."""
    if state.get('result'):
        return 'finish'
    jobs = state.get('retrieval_jobs', [])
    if len(jobs) > 1:
        return 'multi_retrieval'
    return 'single_retrieval'

# ---- node component ----
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

Component = lf_component_base_Component
DataInput = lf_component_base_DataInput
Output = lf_component_base_Output
make_branch_data = lf_component_base_make_branch_data
read_state_payload = lf_component_base_read_state_payload
route_after_retrieval_plan = lf_runtime_graph_builder_route_after_retrieval_plan


class RoutePlanComponent(Component):
    display_name = "Route Plan"
    description = "Expose finish / single / multi retrieval branches after planning."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitFork"
    name = "route_plan"

    inputs = [DataInput(name="state", display_name="State", info="State after dataset planning and job build")]
    outputs = [
        Output(name="finish_out", display_name="Finish", method="finish_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="single_out", display_name="Single", method="single_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="multi_out", display_name="Multi", method="multi_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _cached: Tuple[Dict[str, Any], str] | None = None

    def _resolve(self) -> Tuple[Dict[str, Any], str]:
        if self._cached is not None:
            return self._cached
        state = read_state_payload(getattr(self, "state", None))
        route = route_after_retrieval_plan(state) if state else ""
        self.status = f"Retrieval route: {route or 'inactive'}"
        self._cached = (state, route)
        return self._cached

    def finish_state(self):
        state, route = self._resolve()
        return make_branch_data(route == "finish", {"state": state})

    def single_state(self):
        state, route = self._resolve()
        return make_branch_data(route == "single_retrieval", {"state": state})

    def multi_state(self):
        state, route = self._resolve()
        return make_branch_data(route == "multi_retrieval", {"state": state})
