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

# ---- visible runtime: _runtime.graph.state ----
"""Shared state typing for standalone Langflow runtime."""
from typing import Any as __lf_runtime_graph_state__Any, Dict as __lf_runtime_graph_state__Dict, List as __lf_runtime_graph_state__List, Literal as __lf_runtime_graph_state__Literal, TypedDict as __lf_runtime_graph_state__TypedDict
__lf_runtime_graph_state__QueryMode = __lf_runtime_graph_state__Literal['retrieval', 'followup_transform']

class __lf_runtime_graph_state__AgentGraphState(__lf_runtime_graph_state__TypedDict, total=False):
    user_input: str
    chat_history: __lf_runtime_graph_state__List[__lf_runtime_graph_state__Dict[str, str]]
    context: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]
    current_data: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any] | None
    domain_rules_text: str
    domain_registry_payload: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any] | __lf_runtime_graph_state__List[__lf_runtime_graph_state__Any]
    raw_extracted_params: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]
    extracted_params: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]
    query_mode: __lf_runtime_graph_state__QueryMode
    retrieval_plan: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]
    retrieval_keys: __lf_runtime_graph_state__List[str]
    retrieval_jobs: __lf_runtime_graph_state__List[__lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]]
    source_results: __lf_runtime_graph_state__List[__lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]]
    current_datasets: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]
    source_snapshots: __lf_runtime_graph_state__List[__lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]]
    result: __lf_runtime_graph_state__Dict[str, __lf_runtime_graph_state__Any]

# ---- visible runtime: _runtime.graph.builder ----
"""Small routing helpers that mirror the LangGraph branch contract."""
__lf_runtime_graph_builder__AgentGraphState = __lf_runtime_graph_state__AgentGraphState

def __lf_runtime_graph_builder__route_after_resolve(state: __lf_runtime_graph_builder__AgentGraphState) -> str:
    """Return the first visible branch after request resolution."""
    if state.get('query_mode') == 'followup_transform' and isinstance(state.get('current_data'), dict):
        return 'followup_analysis'
    return 'plan_retrieval'

def __lf_runtime_graph_builder__route_after_retrieval_plan(state: __lf_runtime_graph_builder__AgentGraphState) -> str:
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

Component = __lf_component_base__Component
DataInput = __lf_component_base__DataInput
Output = __lf_component_base__Output
make_branch_data = __lf_component_base__make_branch_data
read_state_payload = __lf_component_base__read_state_payload
route_after_retrieval_plan = __lf_runtime_graph_builder__route_after_retrieval_plan


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
