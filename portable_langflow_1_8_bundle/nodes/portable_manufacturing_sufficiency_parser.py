"""Portable Langflow node: parse sufficiency review and route to retry or proceed."""

from __future__ import annotations

import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, Output
from lfx.schema.data import Data


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


def _parse_json_block(text: str) -> dict[str, Any]:
    cleaned = str(text or "").strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(cleaned[start : end + 1])
    except Exception:
        return {}


class PortableManufacturingSufficiencyParserComponent(Component):
    display_name = "Portable Manufacturing Sufficiency Parser"
    description = "Parse sufficiency review JSON and route either to retry re-plan or to final analysis."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Split"
    name = "portable_manufacturing_sufficiency_parser"

    inputs = [
        DataInput(name="state", display_name="State", info="Executed retrieval state"),
        MessageInput(name="llm_message", display_name="LLM Message", info="Response from built-in LLM Model"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON"),
    ]

    outputs = [
        Output(name="sufficient_state", display_name="Sufficient State", method="sufficient_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="retry_state", display_name="Retry State", method="retry_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _resolved: tuple[dict[str, Any] | None, dict[str, Any] | None] | None = None

    def _resolve(self) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if self._resolved is not None:
            return self._resolved

        state = _as_payload(getattr(self, "state", None))
        registry = _as_payload(getattr(self, "domain_registry", None))
        available_dataset_keys = list((registry.get("dataset_keyword_map") or {}).keys())
        parsed = _parse_json_block(_message_text(getattr(self, "llm_message", None)))
        missing_dataset_keys = [str(item) for item in parsed.get("missing_dataset_keys", []) if not available_dataset_keys or str(item) in available_dataset_keys]
        is_sufficient = bool(parsed.get("is_sufficient", not missing_dataset_keys))
        review = {"is_sufficient": is_sufficient, "missing_dataset_keys": missing_dataset_keys, "reason": str(parsed.get("reason") or "").strip()}
        updated_state = {**state, "sufficiency_review": review}

        if is_sufficient or not missing_dataset_keys:
            self._resolved = (updated_state, None)
            self.status = "Retrieval judged sufficient"
        else:
            self._resolved = (None, updated_state)
            self.status = f"Retry needed: {', '.join(missing_dataset_keys)}"
        return self._resolved

    def sufficient_state(self) -> Data | None:
        state, _ = self._resolve()
        return Data(data=state) if state else None

    def retry_state(self) -> Data | None:
        _, state = self._resolve()
        return Data(data=state) if state else None
