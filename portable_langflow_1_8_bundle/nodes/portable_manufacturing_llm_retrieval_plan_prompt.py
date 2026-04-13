"""Portable Langflow node: build an LLM prompt for retrieval planning."""

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


class PortableManufacturingLlmRetrievalPlanPromptComponent(Component):
    display_name = "Portable Manufacturing LLM Retrieval Plan Prompt"
    description = "Build a JSON retrieval-planning prompt for a built-in LLM Model node."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "NotebookPen"
    name = "portable_manufacturing_llm_retrieval_plan_prompt"

    inputs = [
        DataInput(name="state", display_name="State", info="State from Portable Manufacturing LLM Param Parser"),
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
        rules_text = _message_text(getattr(self, "domain_rules", None)).strip()
        dataset_keyword_map = registry.get("dataset_keyword_map", {})
        analysis_rules = (registry.get("custom_registry") or registry).get("analysis_rules", [])
        dataset_catalog = list(dataset_keyword_map.keys()) if isinstance(dataset_keyword_map, dict) else []

        prompt = f"""You are planning which manufacturing datasets should be retrieved.
Return JSON only.

Domain rules:
{rules_text or "(use manufacturing-aware reasoning)"}

Dataset keyword map:
{json.dumps(dataset_keyword_map, ensure_ascii=False, indent=2)}

Registered analysis rules:
{json.dumps(analysis_rules, ensure_ascii=False, indent=2)}

Already extracted parameters:
{json.dumps(extracted_params, ensure_ascii=False, indent=2)}

User question:
{query}

Return only:
{{
  "dataset_keys": {json.dumps(dataset_catalog, ensure_ascii=False)},
  "needs_post_processing": true,
  "analysis_goal": "short description",
  "merge_hints": {{
    "group_dimensions": [],
    "aggregation": "sum",
    "reason": "short reason"
  }}
}}
Rules:
- Choose only dataset keys from the available dataset list.
- If a custom or derived metric is requested, include every base dataset needed for the final answer.
- Set needs_post_processing=true for grouping, joining, ranking, comparing, top-N, averages, or derived metrics.
- Return pure JSON.
"""

        payload = {"prompt": prompt, "state": state}
        self._cached_payload = payload
        self.status = "LLM retrieval-plan prompt ready"
        return payload

    def prompt_message(self) -> Message:
        payload = self._build()
        return Message(text=str(payload["prompt"]), data={"kind": "portable_manufacturing_llm_retrieval_plan_prompt"})

    def prompt_data(self) -> Data:
        return Data(data=self._build())
