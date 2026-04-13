"""Portable Langflow node: parse LLM parameter extraction and route follow-up vs retrieval."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, Output
from lfx.schema.data import Data


FOLLOWUP_KEYWORDS = ["그 결과", "그거", "이전 결과", "정리", "상위", "평균", "합계", "비교", "공정별", "라인별", "제품별", "top", "average", "sum", "group", "compare"]


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


def _normalize(text: Any) -> str:
    return re.sub(r"[^a-z0-9\uac00-\ud7a3]+", "", str(text or "").lower())


def _contains_alias(text: str, alias: str) -> bool:
    alias_norm = _normalize(alias)
    return bool(alias_norm) and alias_norm in _normalize(text)


def _fallback_date(text: str) -> str | None:
    lowered = str(text or "").lower()
    now = datetime.now()
    if "어제" in text or "yesterday" in lowered:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if "오늘" in text or "today" in lowered:
        return now.strftime("%Y-%m-%d")
    return None


def _merge_unique(value: Any) -> list[str] | None:
    values = value if isinstance(value, list) else [value] if value else []
    result: list[str] = []
    for item in values:
        cleaned = str(item).strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result or None


def _expand_groups(raw_values: Any, field_name: str, registry: dict[str, Any], user_input: str) -> list[str] | None:
    values = _merge_unique(raw_values) or []
    attribute_groups = registry.get("attribute_groups", {})
    groups = registry.get("process_groups", {}) if field_name == "process_name" else attribute_groups.get(field_name, {})
    custom_groups = (registry.get("custom_registry") or registry).get("value_groups", [])
    expanded: list[str] = []
    for raw_value in values:
        matched = False
        for group in groups.values():
            aliases = [str(group.get("group_name") or ""), *(group.get("synonyms") or []), *(group.get("actual_values") or [])]
            if any(_normalize(raw_value) == _normalize(alias) for alias in aliases):
                expanded.extend(str(item) for item in group.get("actual_values") or [])
                matched = True
                break
        if not matched:
            expanded.append(raw_value)
    for group in custom_groups:
        if str(group.get("field") or "") != field_name:
            continue
        aliases = [str(group.get("canonical") or ""), *(group.get("synonyms") or [])]
        if any(_contains_alias(user_input, alias) for alias in aliases):
            expanded.extend(str(item) for item in group.get("values") or [])
    return _merge_unique(expanded)


class PortableManufacturingLlmParamParserComponent(Component):
    display_name = "Portable Manufacturing LLM Param Parser"
    description = "Parse LLM JSON parameters, normalize with registry groups, and route follow-up vs retrieval."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Braces"
    name = "portable_manufacturing_llm_param_parser"

    inputs = [
        DataInput(name="state", display_name="State", info="Original session state"),
        MessageInput(name="llm_message", display_name="LLM Message", info="Response from built-in LLM Model"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON"),
    ]

    outputs = [
        Output(name="state_with_params", display_name="State With Params", method="state_with_params", types=["Data"], selected="Data"),
        Output(name="followup_state", display_name="Followup State", method="followup_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="retrieval_state", display_name="Retrieval State", method="retrieval_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _resolved: tuple[dict[str, Any], str] | None = None

    def _resolve(self) -> tuple[dict[str, Any], str]:
        if self._resolved is not None:
            return self._resolved

        state = _as_payload(getattr(self, "state", None))
        registry = _as_payload(getattr(self, "domain_registry", None))
        parsed = _parse_json_block(_message_text(getattr(self, "llm_message", None)))
        query = str(state.get("user_input") or "").strip()
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else None
        context = state.get("context") if isinstance(state.get("context"), dict) else {}

        extracted_params = {
            "date": parsed.get("date") or _fallback_date(query) or context.get("date"),
            "process_name": _expand_groups(parsed.get("process_name"), "process_name", registry, query) or context.get("process_name"),
            "oper_num": _merge_unique(parsed.get("oper_num")) or context.get("oper_num"),
            "pkg_type1": _expand_groups(parsed.get("pkg_type1"), "pkg_type1", registry, query) or context.get("pkg_type1"),
            "pkg_type2": _expand_groups(parsed.get("pkg_type2"), "pkg_type2", registry, query) or context.get("pkg_type2"),
            "product_name": str(parsed.get("product_name") or context.get("product_name") or "").strip() or None,
            "line_name": _merge_unique(parsed.get("line_name")) or context.get("line_name"),
            "mode": _expand_groups(parsed.get("mode"), "mode", registry, query) or context.get("mode"),
            "den": _expand_groups(parsed.get("den"), "den", registry, query) or context.get("den"),
            "tech": _expand_groups(parsed.get("tech"), "tech", registry, query) or context.get("tech"),
            "lead": str(parsed.get("lead") or context.get("lead") or "").strip() or None,
            "mcp_no": str(parsed.get("mcp_no") or context.get("mcp_no") or "").strip() or None,
            "group_by": str(parsed.get("group_by") or "").strip() or None,
        }

        explicit_reset = bool(extracted_params["date"]) or any(_contains_alias(query, keyword) for keywords in registry.get("dataset_keyword_map", {}).values() for keyword in keywords or [])
        lowered = query.lower()
        explicit_followup = any(keyword in query for keyword in FOLLOWUP_KEYWORDS if keyword not in {"top", "average", "sum", "group", "compare"}) or any(keyword in lowered for keyword in ["top", "average", "sum", "group", "compare"])
        query_mode = "followup" if current_data and explicit_followup and not explicit_reset else "retrieval"

        resolved_state = {**state, "extracted_params": extracted_params, "query_mode": query_mode}
        self._resolved = (resolved_state, query_mode)
        self.status = f"LLM params parsed: {query_mode}"
        return self._resolved

    def state_with_params(self) -> Data:
        return Data(data=self._resolve()[0])

    def followup_state(self) -> Data | None:
        state, mode = self._resolve()
        return Data(data=state) if mode == "followup" else None

    def retrieval_state(self) -> Data | None:
        state, mode = self._resolve()
        return Data(data=state) if mode == "retrieval" else None
