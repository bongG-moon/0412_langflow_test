from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


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


def _domain_metrics(domain: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    metrics = domain.get("metrics") if isinstance(domain.get("metrics"), dict) else {}
    return {str(key): value for key, value in metrics.items() if isinstance(value, dict)}


def _domain_datasets(domain: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    return {str(key): value for key, value in datasets.items() if isinstance(value, dict)}


def _metric_definitions(plan: Dict[str, Any], domain: Dict[str, Any]) -> list[Dict[str, Any]]:
    result: list[Dict[str, Any]] = []
    raw_definitions = plan.get("metric_definitions") if isinstance(plan.get("metric_definitions"), dict) else {}
    domain_metrics = _domain_metrics(domain)
    for metric_key in _as_list(plan.get("metric_keys")):
        key = str(metric_key or "").strip()
        metric = raw_definitions.get(key) if isinstance(raw_definitions.get(key), dict) else domain_metrics.get(key)
        if isinstance(metric, dict):
            result.append({**deepcopy(metric), "metric_key": key})
    for key, metric in raw_definitions.items():
        if isinstance(metric, dict) and str(key) not in {item.get("metric_key") for item in result}:
            result.append({**deepcopy(metric), "metric_key": str(key)})
    return result


def _metric_formula_expression(formula: str, source_columns: list[str]) -> str:
    expression = str(formula or "").strip()
    if not expression:
        return ""
    allowed_names = {str(column) for column in source_columns}

    def replace_sum(match: re.Match[str]) -> str:
        column = match.group(1).strip().strip("'\"")
        return f"result[{column!r}]" if column in allowed_names else "__INVALID_COLUMN__"

    expression = re.sub(r"sum\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", replace_sum, expression)
    if "__INVALID_COLUMN__" in expression or "sum(" in expression.lower():
        return ""
    allowed_chars = set("0123456789+-*/(). []_'\"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if any(char not in allowed_chars for char in expression):
        return ""
    if not all(token in expression for token in ("result[", "]")):
        return ""
    remainder = re.sub(r"result\[[^\]]+\]", "0", expression)
    if re.search(r"[A-Za-z_]", remainder):
        return ""
    return expression


def _metric_denominator_columns(formula: str, source_columns: list[str]) -> list[str]:
    columns: list[str] = []
    for match in re.finditer(r"/\s*sum\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", str(formula or "")):
        column = match.group(1).strip()
        if column in source_columns:
            columns.append(column)
    return _unique_strings(columns)


def _metric_fallback_code(plan: Dict[str, Any], domain: Dict[str, Any], columns: list[str], group_by: list[str], suffix: str) -> str:
    for metric in _metric_definitions(plan, domain):
        output_column = str(metric.get("output_column") or metric.get("metric_key") or "").strip()
        source_columns = _unique_strings([str(column) for column in _as_list(metric.get("source_columns")) if str(column) in columns])
        expression = _metric_formula_expression(str(metric.get("formula") or ""), source_columns)
        if not output_column or not source_columns or not expression:
            continue
        if group_by:
            prefix = f"result = df.groupby({group_by!r}, as_index=False)[{source_columns!r}].sum()\n"
        else:
            values = ", ".join(f"{column!r}: [df[{column!r}].sum()]" for column in source_columns)
            prefix = f"result = pd.DataFrame({{{values}}})\n"
        mask_columns = source_columns
        denominator_columns = _metric_denominator_columns(str(metric.get("formula") or ""), source_columns)
        mask = f"result[{mask_columns!r}].notna().all(axis=1)"
        for column in denominator_columns:
            mask += f" & (result[{column!r}] != 0)"
        return prefix + f"result[{output_column!r}] = None\nmask = {mask}\nresult.loc[mask, {output_column!r}] = {expression}" + suffix
    return ""


def _numeric_columns(plan: Dict[str, Any], domain: Dict[str, Any], columns: list[str], rows: list[Dict[str, Any]]) -> list[str]:
    candidates: list[str] = []
    sort_plan = plan.get("sort") if isinstance(plan.get("sort"), dict) else {}
    candidates.extend(_as_list(sort_plan.get("column")))
    for metric in _metric_definitions(plan, domain):
        candidates.extend(_as_list(metric.get("output_column") or metric.get("metric_key")))
        candidates.extend(_as_list(metric.get("source_columns")))
    datasets = _domain_datasets(domain)
    for dataset_key in _as_list(plan.get("needed_datasets")):
        dataset = datasets.get(str(dataset_key), {})
        candidates.extend(_as_list(dataset.get("primary_quantity_column")))
        candidates.extend(_as_list(dataset.get("numeric_columns") or dataset.get("measure_columns") or dataset.get("value_columns")))
    for column in columns:
        values = [row.get(column) for row in rows if isinstance(row, dict) and row.get(column) is not None]
        if values and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values[:20]):
            candidates.append(column)
    return [column for column in _unique_strings([str(item) for item in candidates]) if column in columns]


def _fallback_code(plan: Dict[str, Any], columns: list[str], domain: Dict[str, Any] | None = None, rows: list[Dict[str, Any]] | None = None) -> str:
    domain = domain or {}
    rows = rows or []
    group_by = [column for column in _as_list(plan.get("group_by")) if str(column) in columns]
    numeric_cols = _numeric_columns(plan, domain, columns, rows)
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
    metric_code = _metric_fallback_code(plan, domain, columns, group_by, suffix)
    if metric_code:
        return metric_code
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
    domain = prompt_payload.get("domain") if isinstance(prompt_payload.get("domain"), dict) else {}
    columns = [str(column) for column in _as_list(prompt_payload.get("columns") or table.get("columns"))]
    rows = table.get("data") if isinstance(table.get("data"), list) else []
    if llm_result.get("skipped") or prompt_payload.get("skipped") or retrieval.get("skipped"):
        analysis_plan = {"code": "", "source": "skipped", "operations": [], "warnings": [prompt_payload.get("skip_reason") or llm_result.get("skip_reason") or retrieval.get("skip_reason") or "route skipped"]}
        return {"analysis_plan_payload": {"skipped": True, "skip_reason": analysis_plan["warnings"][0], "analysis_plan": analysis_plan, "retrieval_payload": retrieval, "table": table, "intent_plan": plan if isinstance(plan, dict) else {}, "domain": domain, "columns": columns}, "analysis_plan": analysis_plan}

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
        code = _fallback_code(plan if isinstance(plan, dict) else {}, columns, domain, [row for row in rows if isinstance(row, dict)])
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
            "domain": domain,
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

