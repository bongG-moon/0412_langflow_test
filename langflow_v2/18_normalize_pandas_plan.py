from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


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


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _strip_code_fence(text: str) -> str:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json|JSON)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _parse_jsonish(value: Any) -> tuple[Any, list[str]]:
    if value is None:
        return {}, []
    if isinstance(value, (dict, list)):
        return deepcopy(value), []
    text = _strip_code_fence(str(value or ""))
    if not text:
        return {}, []
    errors: list[str] = []
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text), []
        except Exception as exc:
            errors.append(str(exc))
    return {}, errors


def _extract_json_object(text: str) -> Dict[str, Any]:
    parsed, errors = _parse_jsonish(text)
    if isinstance(parsed, dict) and parsed:
        return parsed
    match = re.search(r"\{.*\}", str(text or ""), flags=re.DOTALL)
    if match:
        parsed, errors = _parse_jsonish(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    return {"_parse_errors": errors}


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return deepcopy(data)
    text = getattr(value, "text", None) or getattr(value, "content", None)
    if isinstance(text, str):
        parsed, _errors = _parse_jsonish(text)
        return parsed if isinstance(parsed, dict) else {"text": text}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _fallback_code(plan: Dict[str, Any], columns: list[str]) -> str:
    group_by = [column for column in _as_list(plan.get("group_by")) if str(column) in columns]
    numeric_priority = ["production", "target", "achievement_rate", "wip_qty", "hold_qty", "scrap_qty", "defect_qty", "inspection_qty", "pass_qty", "tested_qty", "yield_rate", "utilization_rate"]
    numeric_cols = [column for column in numeric_priority if column in columns]
    sort_plan = plan.get("sort") if isinstance(plan.get("sort"), dict) else {}
    sort_column = str(sort_plan.get("column") or "").strip()
    ascending = bool(sort_plan.get("ascending")) if sort_plan else False
    try:
        top_n = int(plan.get("top_n") or 0)
    except Exception:
        top_n = 0
    suffix = ""
    if sort_column:
        suffix += f"\nif {sort_column!r} in result.columns:\n    result = result.sort_values({sort_column!r}, ascending={ascending!r})"
    if top_n > 0:
        suffix += f"\nresult = result.head({top_n})"
    if "production" in columns and "target" in columns:
        if group_by:
            prefix = f"result = df.groupby({group_by!r}, as_index=False)[['production', 'target']].sum()\n"
        else:
            prefix = "result = pd.DataFrame({'production': [df['production'].sum()], 'target': [df['target'].sum()]})\n"
        return prefix + "result['achievement_rate'] = None\nmask = result['target'].notna() & (result['target'] != 0)\nresult.loc[mask, 'achievement_rate'] = result.loc[mask, 'production'] / result.loc[mask, 'target'] * 100" + suffix
    if group_by and numeric_cols:
        return f"result = df.groupby({group_by!r}, as_index=False)[{numeric_cols!r}].sum()" + suffix
    if numeric_cols:
        values = ", ".join(f"{column!r}: [df[{column!r}].sum()]" for column in numeric_cols[:5])
        return f"result = pd.DataFrame({{{values}}})" + suffix
    return "result = df.copy()" + suffix


def normalize_pandas_plan(llm_result_value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(llm_result_value)
    llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
    prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
    retrieval = prompt_payload.get("retrieval_payload") if isinstance(prompt_payload.get("retrieval_payload"), dict) else {}
    table = prompt_payload.get("table") if isinstance(prompt_payload.get("table"), dict) else {}
    plan = prompt_payload.get("intent_plan") if isinstance(prompt_payload.get("intent_plan"), dict) else retrieval.get("intent_plan", {})
    columns = [str(column) for column in _as_list(prompt_payload.get("columns") or table.get("columns"))]
    if llm_result.get("skipped") or prompt_payload.get("skipped") or retrieval.get("skipped"):
        analysis_plan = {"code": "", "source": "skipped", "operations": [], "warnings": [prompt_payload.get("skip_reason") or llm_result.get("skip_reason") or retrieval.get("skip_reason") or "route skipped"]}
        return {"analysis_plan_payload": {"skipped": True, "skip_reason": analysis_plan["warnings"][0], "analysis_plan": analysis_plan, "retrieval_payload": retrieval, "table": table, "intent_plan": plan if isinstance(plan, dict) else {}, "columns": columns}, "analysis_plan": analysis_plan}

    warnings = [str(item) for item in _as_list(llm_result.get("errors")) if str(item).strip()]
    raw_plan = _extract_json_object(str(llm_result.get("llm_text") or ""))
    code = ""
    source = "llm"
    if isinstance(raw_plan, dict) and raw_plan and not raw_plan.get("_parse_errors"):
        code = str(raw_plan.get("code") or "").strip()
    else:
        if raw_plan.get("_parse_errors"):
            warnings.extend(str(item) for item in _as_list(raw_plan.get("_parse_errors")) if str(item).strip())
        raw_plan = {}

    if not plan.get("needs_pandas", True):
        code = "result = df.copy()"
        source = "direct_table"
        raw_plan = {**raw_plan, "operations": _as_list(raw_plan.get("operations")) or ["pass_through"]}
    elif not code:
        code = _fallback_code(plan if isinstance(plan, dict) else {}, columns)
        source = "fallback"

    analysis_plan = {
        "code": code,
        "source": source,
        "operations": _as_list(raw_plan.get("operations")) if isinstance(raw_plan, dict) else [],
        "warnings": _unique_strings([*_as_list(raw_plan.get("warnings") if isinstance(raw_plan, dict) else []), *warnings]),
        "raw_plan": raw_plan,
    }
    return {
        "analysis_plan_payload": {
            "analysis_plan": analysis_plan,
            "retrieval_payload": retrieval,
            "table": table,
            "intent_plan": plan if isinstance(plan, dict) else {},
            "columns": columns,
        },
        "analysis_plan": analysis_plan,
    }


class NormalizePandasPlan(Component):
    display_name = "Normalize Pandas Plan"
    description = "Parse and normalize LLM pandas JSON into a short executable analysis plan."
    icon = "ListChecks"
    name = "NormalizePandasPlan"

    inputs = [
        DataInput(name="llm_result", display_name="LLM Result", info="Output from LLM JSON Caller.", input_types=["Data", "JSON"])
    ]
    outputs = [Output(name="analysis_plan_payload", display_name="Analysis Plan Payload", method="build_plan", types=["Data"])]

    def build_plan(self):
        payload = normalize_pandas_plan(getattr(self, "llm_result", None))
        plan = payload["analysis_plan_payload"].get("analysis_plan", {})
        self.status = {"source": plan.get("source"), "code_chars": len(plan.get("code", "")), "warnings": len(plan.get("warnings", []))}
        return _make_data(payload)

