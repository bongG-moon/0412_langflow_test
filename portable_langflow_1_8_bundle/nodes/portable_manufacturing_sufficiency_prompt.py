"""Portable Langflow node: build an LLM prompt for retrieval sufficiency review."""

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
    source_results = state.get("source_results") if isinstance(state.get("source_results"), dict) else {}
    columns: list[str] = []
    for rows in source_results.values():
        if isinstance(rows, list) and rows:
            for key in rows[0].keys():
                if key not in columns:
                    columns.append(str(key))
    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    for key in current_data.get("columns") or []:
        if key not in columns:
            columns.append(str(key))
    return columns


class PortableManufacturingSufficiencyPromptComponent(Component):
    display_name = "Portable Manufacturing Sufficiency Prompt"
    description = "Build an LLM review prompt to decide whether the current retrieval selection is sufficient."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "BadgeHelp"
    name = "portable_manufacturing_sufficiency_prompt"

    inputs = [
        DataInput(name="state", display_name="State", info="Executed retrieval state"),
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
        rules_text = _message_text(getattr(self, "domain_rules", None)).strip()
        retrieval_plan = state.get("retrieval_plan") if isinstance(state.get("retrieval_plan"), dict) else {}
        selected_dataset_keys = retrieval_plan.get("dataset_keys") if isinstance(retrieval_plan.get("dataset_keys"), list) else state.get("selected_dataset_keys", [])
        columns = _collect_columns(state)
        dataset_catalog = list((registry.get("dataset_keyword_map") or {}).keys())

        prompt = f"""You are reviewing whether the current manufacturing retrieval selection is sufficient.
Return JSON only.

Domain rules:
{rules_text or "(use manufacturing-aware reasoning)"}

Available dataset list:
{json.dumps(dataset_catalog, ensure_ascii=False)}

Current selected dataset keys:
{json.dumps(selected_dataset_keys, ensure_ascii=False)}

Current available columns:
{json.dumps(columns, ensure_ascii=False)}

User question:
{query}

Return only:
{{
  "is_sufficient": true,
  "missing_dataset_keys": [],
  "reason": "short explanation"
}}
Rules:
- If the question needs another base dataset for comparison, ratio, achievement, hold-load, or similar, mark is_sufficient=false.
- Only use dataset keys from the available dataset list.
- Return JSON only.
"""

        payload = {"prompt": prompt, "state": state}
        self._cached_payload = payload
        self.status = "Sufficiency prompt ready"
        return payload

    def prompt_message(self) -> Message:
        payload = self._build()
        return Message(text=str(payload["prompt"]), data={"kind": "portable_manufacturing_sufficiency_prompt"})

    def prompt_data(self) -> Data:
        return Data(data=self._build())
