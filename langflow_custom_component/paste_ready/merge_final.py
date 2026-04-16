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
from typing import Any, Dict, Tuple

Component = __lf_component_base__Component
DataInput = __lf_component_base__DataInput
Output = __lf_component_base__Output
make_data = __lf_component_base__make_data
read_data_payload = __lf_component_base__read_data_payload


class MergeFinalComponent(Component):
    display_name = "Merge Result"
    description = "Merge visible branch outputs into one final manufacturing result payload."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitMerge"
    name = "merge_final"

    inputs = [
        DataInput(name="followup_result", display_name="Followup", info="Follow-up branch result"),
        DataInput(name="finish_result", display_name="Finish", info="Early finish branch result"),
        DataInput(name="single_direct_result", display_name="Single Direct", info="Single direct-response branch result"),
        DataInput(name="single_analysis_result", display_name="Single Analysis", info="Single post-analysis branch result"),
        DataInput(name="multi_overview_result", display_name="Multi Overview", info="Multi overview branch result"),
        DataInput(name="multi_analysis_result", display_name="Multi Analysis", info="Multi post-analysis branch result"),
    ]
    outputs = [Output(name="result_out", display_name="Result", method="merged_result", types=["Data"], selected="Data")]

    _cached: Tuple[Dict[str, Any], str] | None = None

    @staticmethod
    def _unwrap_result_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        if "response" in payload or "tool_results" in payload or "current_data" in payload:
            return payload
        nested_result = payload.get("result")
        if isinstance(nested_result, dict):
            return nested_result
        state = payload.get("state")
        if isinstance(state, dict) and isinstance(state.get("result"), dict):
            return state["result"]
        return {}

    def _resolve(self) -> Tuple[Dict[str, Any], str]:
        if self._cached is not None:
            return self._cached

        candidates = [
            ("followup_result", "followup", getattr(self, "followup_result", None)),
            ("finish_result", "finish", getattr(self, "finish_result", None)),
            ("single_direct_result", "single_direct", getattr(self, "single_direct_result", None)),
            ("single_analysis_result", "single_analysis", getattr(self, "single_analysis_result", None)),
            ("multi_overview_result", "multi_overview", getattr(self, "multi_overview_result", None)),
            ("multi_analysis_result", "multi_analysis", getattr(self, "multi_analysis_result", None)),
        ]
        for input_name, branch_name, raw_value in candidates:
            payload = self._unwrap_result_payload(read_data_payload(raw_value))
            if not payload:
                continue
            if not any(key in payload for key in ("response", "tool_results", "current_data", "failure_type")):
                continue
            payload = {**payload, "merged_from_branch": branch_name, "merged_from_input": input_name}
            self.status = f"Merged branch: {branch_name}"
            self._cached = (payload, branch_name)
            return self._cached

        self.status = "No active final branch"
        self._cached = ({}, "")
        return self._cached

    def merged_result(self):
        payload, _ = self._resolve()
        if not payload:
            return None
        response_text = str(payload.get("response", "") or "")
        return make_data(payload, text=response_text)
