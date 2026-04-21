from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# Compatibility scaffolding for local tests. In lfx Langflow this can be
# replaced with direct imports from lfx.custom, lfx.io, and lfx.schema.
def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback


class _FallbackComponent:
    display_name = ""
    description = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""


@dataclass
class _FallbackInput:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    advanced: bool = False
    tool_mode: bool = False
    input_types: list[str] | None = None


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


DEFAULT_PLAN: Dict[str, Any] = {
    "intent": "current data analysis",
    "operations": [],
    "output_columns": [],
    "group_by_columns": [],
    "filters": [],
    "sort_by": "",
    "sort_order": "desc",
    "top_n": None,
    "metric_column": "",
    "warnings": [],
    "code": "",
    "source": "llm",
}


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return {"text": text}
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return {"text": content}
    return {}


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("llm_text", "text", "output", "content", "result"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return text.strip()
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(value or "").strip()


def _extract_json_object(text: str) -> str:
    cleaned = str(text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _normalize_plan(parsed: Any, errors: list[str]) -> Dict[str, Any]:
    if not isinstance(parsed, dict):
        errors.append("Pandas analysis JSON root must be an object.")
        return dict(DEFAULT_PLAN)
    plan = dict(DEFAULT_PLAN)
    plan.update(parsed)
    for key in ("operations", "output_columns", "group_by_columns", "warnings"):
        plan[key] = [str(item).strip() for item in _as_list(plan.get(key)) if str(item).strip()]
    filters = plan.get("filters")
    plan["filters"] = filters if isinstance(filters, list) else []
    plan["sort_by"] = str(plan.get("sort_by") or "").strip()
    plan["sort_order"] = str(plan.get("sort_order") or "desc").strip().lower()
    if plan["sort_order"] not in {"asc", "desc", "ascending", "descending"}:
        plan["sort_order"] = "desc"
    try:
        if plan.get("top_n") is not None:
            plan["top_n"] = int(plan["top_n"])
    except Exception:
        plan["top_n"] = None
    plan["metric_column"] = str(plan.get("metric_column") or "").strip()
    plan["code"] = str(plan.get("code") or "").strip()
    plan["intent"] = str(plan.get("intent") or "current data analysis").strip()
    plan["source"] = "llm"
    if not plan["code"]:
        errors.append("Pandas analysis code is empty.")
    return plan


def parse_pandas_analysis_json(llm_output: Any) -> Dict[str, Any]:
    text = _extract_text(llm_output)
    errors: list[str] = []
    if not text:
        errors.append("llm_output is empty.")
        plan = dict(DEFAULT_PLAN)
    else:
        try:
            parsed = json.loads(_extract_json_object(text))
            plan = _normalize_plan(parsed, errors)
        except Exception as exc:
            errors.append(f"Pandas analysis JSON parse failed: {exc}")
            plan = dict(DEFAULT_PLAN)
    return {
        "analysis_plan": plan,
        "parse_errors": errors,
        "llm_text_chars": len(text),
    }


class ParsePandasAnalysisJSON(Component):
    display_name = "Parse Pandas Analysis JSON"
    description = "Parse built-in LLM output into a pandas analysis plan."
    icon = "Braces"
    name = "ParsePandasAnalysisJSON"

    inputs = [
        DataInput(
            name="llm_output",
            display_name="LLM Output",
            info="Output from built-in LLM node connected after Build Pandas Analysis Prompt.",
            input_types=["Data", "Message", "Text", "JSON"],
        ),
    ]

    outputs = [
        Output(name="analysis_plan", display_name="Analysis Plan", method="build_plan", types=["Data"]),
    ]

    def build_plan(self) -> Data:
        payload = parse_pandas_analysis_json(getattr(self, "llm_output", None))
        self.status = {
            "parse_errors": len(payload.get("parse_errors", [])),
            "has_code": bool(payload.get("analysis_plan", {}).get("code")),
        }
        return _make_data(payload)
