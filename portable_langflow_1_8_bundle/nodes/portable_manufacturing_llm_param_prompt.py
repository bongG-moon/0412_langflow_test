"""Portable Langflow node: build an LLM prompt for manufacturing parameter extraction."""

from __future__ import annotations

import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


DEFAULT_RULES_TEXT = """Use manufacturing-aware extraction.
- Expand process groups like D/A, W/B, FCB, P/C, SAT, P/L, DP.
- Expand custom process groups like 후공정A -> D/A1, D/A2.
- Interpret 양품률 as yield, 생산 목표 차이율 as production+target, HOLD 이상여부 as wip status based analysis.
- Return JSON only.
"""


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


class PortableManufacturingLlmParamPromptComponent(Component):
    display_name = "Portable Manufacturing LLM Param Prompt"
    description = "Build a JSON extraction prompt for a built-in LLM Model node."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "FileSearch"
    name = "portable_manufacturing_llm_param_prompt"

    inputs = [
        DataInput(name="state", display_name="State", info="Session state from Portable Manufacturing Session State"),
        MessageInput(name="domain_rules", display_name="Domain Rules", advanced=False, info="Optional rules text from Portable Manufacturing Domain Rules Text"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON from Portable Manufacturing Domain Registry JSON"),
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
        chat_history = state.get("chat_history") if isinstance(state.get("chat_history"), list) else []
        context = state.get("context") if isinstance(state.get("context"), dict) else {}
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
        current_columns = current_data.get("columns") if isinstance(current_data.get("columns"), list) else []
        rules_text = _message_text(getattr(self, "domain_rules", None)).strip() or DEFAULT_RULES_TEXT
        registry_summary = {
            "dataset_keyword_map": registry.get("dataset_keyword_map", {}),
            "value_groups": (registry.get("custom_registry") or registry).get("value_groups", []),
            "analysis_rules": (registry.get("custom_registry") or registry).get("analysis_rules", []),
        }

        prompt = f"""You are extracting retrieval-safe parameters for a manufacturing assistant.
Return JSON only.

Rules:
- Extract only retrieval parameters and grouping hints.
- Keep unknown fields as null.
- Normalize date into YYYY-MM-DD when possible.
- If the question clearly asks to transform a previous result, still extract filters but do not invent a new dataset.

Domain rules:
{rules_text}

Domain registry summary:
{json.dumps(registry_summary, ensure_ascii=False, indent=2)}

Recent chat:
{json.dumps(chat_history[-6:], ensure_ascii=False)}

Context:
{json.dumps(context, ensure_ascii=False)}

Current table columns:
{", ".join(str(column) for column in current_columns) if current_columns else "(none)"}

User question:
{query}

Return only:
{{
  "date": "YYYY-MM-DD or null",
  "process_name": ["value"] or null,
  "oper_num": ["value"] or null,
  "pkg_type1": ["value"] or null,
  "pkg_type2": ["value"] or null,
  "product_name": "string or null",
  "line_name": ["value"] or null,
  "mode": ["value"] or null,
  "den": ["value"] or null,
  "tech": ["value"] or null,
  "lead": "string or null",
  "mcp_no": "string or null",
  "group_by": "column or null"
}}"""

        payload = {"prompt": prompt, "user_input": query, "state": state}
        self._cached_payload = payload
        self.status = "LLM parameter prompt ready"
        return payload

    def prompt_message(self) -> Message:
        payload = self._build()
        return Message(text=str(payload["prompt"]), data={"kind": "portable_manufacturing_llm_param_prompt"})

    def prompt_data(self) -> Data:
        return Data(data=self._build())
