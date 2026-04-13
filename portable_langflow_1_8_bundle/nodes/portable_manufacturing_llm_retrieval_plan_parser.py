"""Portable Langflow node: parse LLM retrieval plan and build jobs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
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


def _extract_date_slices(text: str, default_date: str | None) -> list[dict[str, str]]:
    lowered = str(text or "").lower()
    now = datetime.now()
    slices: list[dict[str, str]] = []
    if "어제" in str(text or "") or "yesterday" in lowered:
        slices.append({"label": "어제", "date": (now - timedelta(days=1)).strftime("%Y-%m-%d")})
    if "오늘" in str(text or "") or "today" in lowered:
        slices.append({"label": "오늘", "date": now.strftime("%Y-%m-%d")})
    for year, month, day in re.findall(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?(0[1-9]|[12]\d|3[01])", str(text or "")):
        date_value = f"{year}-{month}-{day}"
        if date_value not in [item["date"] for item in slices]:
            slices.append({"label": date_value, "date": date_value})
    if not slices and default_date:
        slices.append({"label": default_date, "date": default_date})
    return slices


class PortableManufacturingLlmRetrievalPlanParserComponent(Component):
    display_name = "Portable Manufacturing LLM Retrieval Plan Parser"
    description = "Parse LLM retrieval plan JSON, validate dataset keys, and build retrieval jobs."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "ListChecks"
    name = "portable_manufacturing_llm_retrieval_plan_parser"

    inputs = [
        DataInput(name="state", display_name="State", info="State from Portable Manufacturing LLM Param Parser"),
        MessageInput(name="llm_message", display_name="LLM Message", info="Response from built-in LLM Model"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON"),
    ]

    outputs = [
        Output(name="finish_result", display_name="Finish Result", method="finish_result", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="jobs_state", display_name="Jobs State", method="jobs_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _resolved: tuple[dict[str, Any] | None, dict[str, Any] | None] | None = None

    def _resolve(self) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if self._resolved is not None:
            return self._resolved

        state = _as_payload(getattr(self, "state", None))
        registry = _as_payload(getattr(self, "domain_registry", None))
        parsed = _parse_json_block(_message_text(getattr(self, "llm_message", None)))
        extracted_params = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
        query = str(state.get("user_input") or "").strip()
        dataset_keyword_map = registry.get("dataset_keyword_map", {})
        available_dataset_keys = list(dataset_keyword_map.keys()) if isinstance(dataset_keyword_map, dict) and dataset_keyword_map else ["production", "target", "defect", "equipment", "wip", "yield", "hold", "scrap", "recipe", "lot_trace"]
        dataset_keys = [str(item) for item in parsed.get("dataset_keys", []) if str(item) in available_dataset_keys]
        if not dataset_keys:
            dataset_keys = ["production"]

        requires_date = any(dataset_key in {"production", "target", "defect", "equipment", "wip", "yield", "hold", "scrap", "recipe", "lot_trace"} for dataset_key in dataset_keys)
        date_value = str(extracted_params.get("date") or "").strip()
        if requires_date and not date_value:
            finish_payload = {
                "response": "조회 기준 날짜가 필요합니다. 예: 오늘, 어제, 2026-04-12",
                "tool_results": [],
                "current_data": state.get("current_data"),
                "extracted_params": extracted_params,
                "failure_type": "missing_date",
                "awaiting_analysis_choice": False,
            }
            self._resolved = (finish_payload, None)
            self.status = "Missing date"
            return self._resolved

        date_slices = _extract_date_slices(query, date_value)
        retrieval_jobs = []
        if len(dataset_keys) == 1 and len(date_slices) > 1:
            for date_slice in date_slices:
                job_params = dict(extracted_params)
                job_params["date"] = date_slice["date"]
                retrieval_jobs.append({"dataset_key": dataset_keys[0], "params": job_params, "result_label": date_slice["label"]})
        else:
            for dataset_key in dataset_keys:
                job_params = dict(extracted_params)
                if len(date_slices) == 1:
                    job_params["date"] = date_slices[0]["date"]
                retrieval_jobs.append({"dataset_key": dataset_key, "params": job_params, "result_label": None})

        jobs_state = {
            **state,
            "retrieval_plan": {
                "dataset_keys": dataset_keys,
                "needs_post_processing": bool(parsed.get("needs_post_processing", False)),
                "analysis_goal": str(parsed.get("analysis_goal") or "").strip(),
                "merge_hints": parsed.get("merge_hints") if isinstance(parsed.get("merge_hints"), dict) else {},
            },
            "retrieval_jobs": retrieval_jobs,
            "selected_dataset_keys": dataset_keys,
        }
        self._resolved = (None, jobs_state)
        self.status = f"Built {len(retrieval_jobs)} retrieval jobs"
        return self._resolved

    def finish_result(self) -> Data | None:
        finish_payload, _ = self._resolve()
        return Data(data=finish_payload) if finish_payload else None

    def jobs_state(self) -> Data | None:
        _, jobs_state = self._resolve()
        return Data(data=jobs_state) if jobs_state else None
