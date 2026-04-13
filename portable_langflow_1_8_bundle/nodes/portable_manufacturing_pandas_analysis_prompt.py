"""Portable Langflow node: build an LLM prompt for pandas-based current-data analysis."""

from __future__ import annotations

import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


def _message_text(value: Any) -> str:
    if value is None:
        return ""
    text = getattr(value, "text", None)
    if text is not None:
        return str(text)
    if isinstance(value, dict):
        return str(value.get("text") or "")
    return str(value)


def _collect_columns(state: dict[str, Any]) -> list[str]:
    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    rows = current_data.get("rows") if isinstance(current_data.get("rows"), list) else []
    if rows:
        return [str(key) for key in rows[0].keys()]

    source_results = state.get("source_results") if isinstance(state.get("source_results"), dict) else {}
    columns: list[str] = []
    for rows in source_results.values():
        if isinstance(rows, list) and rows:
            for key in rows[0].keys():
                if key not in columns:
                    columns.append(str(key))
    return columns


def _preview_rows(state: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    rows = current_data.get("rows") if isinstance(current_data.get("rows"), list) else []
    if rows:
        return rows[:limit]

    source_results = state.get("source_results") if isinstance(state.get("source_results"), dict) else {}
    preview: list[dict[str, Any]] = []
    for dataset_key, dataset_rows in source_results.items():
        if isinstance(dataset_rows, list):
            for row in dataset_rows[:2]:
                preview.append({"dataset_key": dataset_key, **row})
                if len(preview) >= limit:
                    return preview
    return preview


class PortableManufacturingPandasAnalysisPromptComponent(Component):
    display_name = "Portable Manufacturing Pandas Analysis Prompt"
    description = "Build a JSON prompt for LLM-generated pandas analysis on the current or retrieved table."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "TableProperties"
    name = "portable_manufacturing_pandas_analysis_prompt"

    inputs = [
        DataInput(name="state", display_name="State", info="Follow-up state or sufficient retrieval state"),
        MessageInput(name="domain_rules", display_name="Domain Rules", advanced=False, info="Optional rules text"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON"),
    ]

    outputs = [
        Output(name="prompt_message", display_name="Prompt Message", method="prompt_message", types=["Message"], selected="Message"),
        Output(name="prompt_data", display_name="Prompt Data", method="prompt_data", types=["Data"], selected="Data"),
    ]

    _cached_payload: dict[str, Any] | None = None

    def _build(self) -> dict[str, Any]:
        if self._cached_payload is not None:
            return self._cached_payload

        state = _as_payload(getattr(self, "state", None))
        registry = _as_payload(getattr(self, "domain_registry", None))
        query = str(state.get("user_input") or "").strip()
        extracted_params = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
        retrieval_plan = state.get("retrieval_plan") if isinstance(state.get("retrieval_plan"), dict) else {}
        rules_text = _message_text(getattr(self, "domain_rules", None)).strip()
        analysis_rules = (registry.get("custom_registry") or registry).get("analysis_rules", [])
        join_rules = (registry.get("custom_registry") or registry).get("join_rules", [])
        columns = _collect_columns(state)
        preview = _preview_rows(state)

        prompt = f"""You are writing safe pandas code for a manufacturing analytics assistant.
Return JSON only.

The runtime will provide:
- pandas as `pd`
- a pre-built pandas DataFrame named `df`
- you must assign the final DataFrame to `result`

Restrictions:
- do not import anything
- do not use files, network, subprocess, eval, exec, or try/except
- do not use lambda expressions or custom functions
- only reference columns that appear in the available column list
- if grouping or ranking is requested, keep the result concise
- if a ratio metric is requested, compute it explicitly in pandas

Domain rules:
{rules_text or "(use manufacturing-aware reasoning)"}

Available columns in df:
{json.dumps(columns, ensure_ascii=False)}

Preview rows:
{json.dumps(preview, ensure_ascii=False, indent=2)}

Extracted params:
{json.dumps(extracted_params, ensure_ascii=False, indent=2)}

Retrieval plan:
{json.dumps(retrieval_plan, ensure_ascii=False, indent=2)}

Registered analysis rules:
{json.dumps(analysis_rules, ensure_ascii=False, indent=2)}

Join rules:
{json.dumps(join_rules, ensure_ascii=False, indent=2)}

User question:
{query}

Return only:
{{
  "analysis_logic": "short explanation",
  "code": "python pandas code assigning DataFrame to result",
  "output_columns": ["col1", "col2"]
}}
"""

        payload = {"prompt": prompt, "state": state}
        self._cached_payload = payload
        self.status = "Pandas analysis prompt ready"
        return payload

    def prompt_message(self) -> Message:
        payload = self._build()
        return Message(text=str(payload["prompt"]), data={"kind": "portable_manufacturing_pandas_analysis_prompt"})

    def prompt_data(self) -> Data:
        return Data(data=self._build())
