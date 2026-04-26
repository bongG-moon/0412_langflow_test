from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from importlib import import_module
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
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
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


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return str(value)


def _pd():
    return import_module("pandas")


SAFE_BUILTINS = {"len": len, "min": min, "max": max, "sum": sum, "sorted": sorted, "abs": abs, "round": round, "str": str, "int": int, "float": float, "list": list}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "os", "sys", "subprocess", "socket", "requests", "httpx"}


def _rows_columns(rows: list[Dict[str, Any]]) -> list[str]:
    return [str(key) for key in rows[0].keys()] if rows and isinstance(rows[0], dict) else []


def _analysis_plan_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("analysis_plan_payload") if isinstance(payload.get("analysis_plan_payload"), dict) else payload


def _retrieval_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("retrieval_payload") if isinstance(payload.get("retrieval_payload"), dict) else payload


def _source_results(retrieval: Dict[str, Any]) -> list[Dict[str, Any]]:
    results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
    return [item for item in results if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        parts = str(item or "").split(",") if isinstance(item, str) else [str(item or "")]
        for part in parts:
            text = part.strip()
            if text and text not in result:
                result.append(text)
    return result


def _dataset_matches(rule_value: Any, dataset_name: str) -> bool:
    names = _string_list(rule_value)
    if not names:
        return True
    dataset_parts = {part for part in str(dataset_name or "").split("+") if part}
    dataset_parts.add(str(dataset_name or ""))
    return any(name in dataset_parts for name in names)


def _join_rule_columns(domain: Dict[str, Any], left_name: str, right_name: str, shared: set[str]) -> list[str]:
    rules = domain.get("join_rules") if isinstance(domain.get("join_rules"), list) else []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        keys = (
            _string_list(rule.get("keys"))
            or _string_list(rule.get("columns"))
            or _string_list(rule.get("join_columns"))
            or _string_list(rule.get("on"))
        )
        if not keys or any(key not in shared for key in keys):
            continue
        left_rule = rule.get("left_dataset", rule.get("left_dataset_key", rule.get("left")))
        right_rule = rule.get("right_dataset", rule.get("right_dataset_key", rule.get("right")))
        direct = _dataset_matches(left_rule, left_name) and _dataset_matches(right_rule, right_name)
        swapped = _dataset_matches(left_rule, right_name) and _dataset_matches(right_rule, left_name)
        if direct or swapped:
            return keys
    return []


def _non_numeric_join_columns(left: Any, right: Any, shared: set[str]) -> list[str]:
    pd = _pd()
    result: list[str] = []
    for column in sorted(shared):
        if column not in left.columns or column not in right.columns:
            continue
        left_numeric = pd.api.types.is_numeric_dtype(left[column])
        right_numeric = pd.api.types.is_numeric_dtype(right[column])
        if not (left_numeric and right_numeric):
            result.append(column)
    return result


def _select_join_columns(domain: Dict[str, Any], left_name: str, right_name: str, left: Any, right: Any, shared: set[str]) -> list[str]:
    return _join_rule_columns(domain, left_name, right_name, shared) or _non_numeric_join_columns(left, right, shared) or sorted(shared)[:3]


def _merge_sources(source_results: list[Dict[str, Any]], domain: Dict[str, Any] | None = None) -> Dict[str, Any]:
    domain = domain or {}
    valid = [item for item in source_results if item.get("success") and isinstance(item.get("data"), list)]
    failed = [item for item in source_results if not item.get("success")]
    if failed:
        first = failed[0]
        return {"success": False, "data": [], "columns": [], "summary": first.get("error_message", "Retrieval failed."), "merge_notes": [], "failed_source_results": failed}
    if not valid:
        return {"success": False, "data": [], "columns": [], "summary": "No source data is available.", "merge_notes": []}
    if len(valid) == 1:
        rows = deepcopy(valid[0].get("data", []))
        return {"success": True, "data": rows, "columns": _rows_columns(rows), "summary": valid[0].get("summary", f"{len(rows)} rows"), "merge_notes": ["single_source"]}

    pd = _pd()
    frames = []
    dataset_keys = []
    for result in valid:
        rows = [row for row in result.get("data", []) if isinstance(row, dict)]
        if rows:
            frames.append(pd.DataFrame(rows))
            dataset_keys.append(str(result.get("dataset_key") or result.get("tool_name") or f"source_{len(frames)}"))
    if not frames:
        return {"success": False, "data": [], "columns": [], "summary": "No mergeable source data is available.", "merge_notes": []}

    merged = frames[0]
    notes: list[str] = []
    current_name = dataset_keys[0]
    for index in range(1, len(frames)):
        right = frames[index]
        right_name = dataset_keys[index]
        shared = set(str(column) for column in merged.columns) & set(str(column) for column in right.columns)
        join_columns = _select_join_columns(domain, current_name, right_name, merged, right, shared)
        if not join_columns:
            return {"success": False, "data": [], "columns": [], "summary": f"No common join key between {current_name} and {right_name}.", "merge_notes": notes}
        merged = merged.merge(right, how="inner", on=join_columns, suffixes=("", f"_{right_name}"))
        notes.append(f"{current_name}+{right_name}: keys={', '.join(join_columns)}")
        current_name = f"{current_name}+{right_name}"
    merged = merged.where(pd.notnull(merged), None)
    rows = merged.to_dict(orient="records")
    return {"success": True, "data": rows, "columns": [str(column) for column in merged.columns], "summary": f"merged rows {len(rows)}", "merge_notes": notes}


def _apply_filters(frame: Any, filters: Dict[str, Any]) -> tuple[Any, list[str]]:
    pd = _pd()
    notes: list[str] = []
    for key, value in filters.items():
        columns = [str(key)] if str(key) in frame.columns else []
        values = [_normalize_text(item) for item in _as_list(value) if str(item).strip()]
        if not columns or not values:
            continue
        before = len(frame)
        mask = pd.Series([False] * len(frame), index=frame.index)
        for column in columns:
            series = frame[column].astype(str).map(_normalize_text)
            for normalized_value in values:
                mask = mask | series.eq(normalized_value) | series.str.contains(normalized_value, regex=False, na=False)
        frame = frame[mask]
        notes.append(f"filter {key}: {before}->{len(frame)}")
    return frame, notes


def _apply_filter_plan(frame: Any, filter_plan: list[Any], column_filters: Dict[str, Any]) -> tuple[Any, list[str]]:
    pd = _pd()
    notes: list[str] = []
    conditions: list[tuple[str, list[str], Any]] = []
    for item in filter_plan:
        if not isinstance(item, dict):
            continue
        columns = [str(column) for column in _as_list(item.get("columns")) if str(column) in frame.columns]
        if columns:
            conditions.append((str(item.get("field") or ""), columns, item.get("values")))
    for column, values in column_filters.items():
        if str(column) in frame.columns:
            conditions.append((str(column), [str(column)], values))
    seen: set[str] = set()
    for field, columns, values in conditions:
        signature = json.dumps([field, columns, values], ensure_ascii=False, default=str)
        if signature in seen:
            continue
        seen.add(signature)
        normalized_values = [_normalize_text(item) for item in _as_list(values) if str(item).strip()]
        if not normalized_values:
            continue
        before = len(frame)
        mask = pd.Series([False] * len(frame), index=frame.index)
        for column in columns:
            series = frame[column].astype(str).map(_normalize_text)
            for normalized_value in normalized_values:
                mask = mask | series.eq(normalized_value) | series.str.contains(normalized_value, regex=False, na=False)
        frame = frame[mask]
        notes.append(f"filter {field}: {before}->{len(frame)}")
    return frame, notes


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
        denominator_columns = _metric_denominator_columns(str(metric.get("formula") or ""), source_columns)
        mask = f"result[{source_columns!r}].notna().all(axis=1)"
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


def _validate_code(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Generated pandas code syntax error: {exc}"
    has_result = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.With, ast.Try, ast.While, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.Delete)):
            return False, f"Forbidden Python node: {type(node).__name__}"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return False, f"Forbidden Python name: {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, "Dunder attribute access is forbidden."
        if isinstance(node, ast.Assign):
            has_result = has_result or any(isinstance(target, ast.Name) and target.id == "result" for target in node.targets)
    return (True, "") if has_result else (False, "Generated pandas code must assign result.")


def _execute_code(code: str, rows: list[Dict[str, Any]], plan: Dict[str, Any]) -> Dict[str, Any]:
    pd = _pd()
    frame = pd.DataFrame(rows or [])
    frame, filter_notes = _apply_filter_plan(frame, plan.get("filter_plan", []) if isinstance(plan.get("filter_plan"), list) else [], plan.get("column_filters", {}) if isinstance(plan.get("column_filters"), dict) else {})
    if not filter_notes:
        frame, filter_notes = _apply_filters(frame, plan.get("filters", {}) if isinstance(plan.get("filters"), dict) else {})
    ok, error = _validate_code(code)
    if not ok:
        return {"success": False, "error_message": error, "data": [], "filter_notes": filter_notes}
    local_vars = {"df": frame.copy(), "pd": pd, "result": None}
    try:
        exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
    except Exception as exc:
        return {"success": False, "error_message": f"Pandas code execution failed: {exc}", "data": [], "filter_notes": filter_notes}
    result = local_vars.get("result")
    if isinstance(result, pd.Series):
        result = result.to_frame().reset_index()
    if not isinstance(result, pd.DataFrame):
        return {"success": False, "error_message": "Pandas code result is not a DataFrame.", "data": [], "filter_notes": filter_notes}
    result = result.where(pd.notnull(result), None)
    return {"success": True, "data": result.to_dict(orient="records"), "filter_notes": filter_notes}


def execute_pandas_analysis(analysis_plan_payload_value: Any, retrieval_payload_value: Any = None) -> Dict[str, Any]:
    payload = _analysis_plan_payload(analysis_plan_payload_value)
    retrieval = payload.get("retrieval_payload") if isinstance(payload.get("retrieval_payload"), dict) else {}
    if retrieval_payload_value is not None:
        override = _retrieval_payload(retrieval_payload_value)
        if override:
            retrieval = override

    plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else retrieval.get("intent_plan", {})
    analysis_plan = payload.get("analysis_plan") if isinstance(payload.get("analysis_plan"), dict) else {}
    domain = payload.get("domain") if isinstance(payload.get("domain"), dict) else {}
    state = retrieval.get("state") if isinstance(retrieval.get("state"), dict) else {}
    source_results = _source_results(retrieval)
    if payload.get("skipped") or retrieval.get("skipped"):
        result = {"skipped": True, "skip_reason": payload.get("skip_reason") or retrieval.get("skip_reason", "route skipped"), "success": False, "tool_name": "analyze_current_data", "data": [], "summary": "", "error_message": "", "analysis_logic": "post_analysis_skipped", "analysis_plan": analysis_plan, "source_results": [], "intent_plan": plan if isinstance(plan, dict) else {}, "state": state, "awaiting_analysis_choice": False}
        return {"analysis_result": result}

    if isinstance(retrieval.get("early_result"), dict):
        result = {**retrieval["early_result"], "success": False, "data": [], "summary": retrieval["early_result"].get("response", ""), "analysis_logic": "early_result", "source_results": source_results, "state": state, "intent_plan": plan}
        return {"analysis_result": result}

    table = payload.get("table") if isinstance(payload.get("table"), dict) and payload.get("table") else _merge_sources(source_results, domain)
    rows = table.get("data") if isinstance(table.get("data"), list) else []
    columns = table.get("columns") if isinstance(table.get("columns"), list) else _rows_columns(rows)
    if not table.get("success") or not rows:
        result = {"success": False, "tool_name": "analyze_current_data", "data": [], "summary": table.get("summary", "No data to analyze."), "error_message": table.get("summary", "No data to analyze."), "analysis_logic": "no_data", "source_results": source_results, "state": state, "intent_plan": plan, "awaiting_analysis_choice": False}
        return {"analysis_result": result}

    code = str(analysis_plan.get("code") or "").strip()
    analysis_logic = str(analysis_plan.get("source") or "analysis_plan")
    if not code:
        code = _fallback_code(plan, [str(column) for column in columns], domain, [row for row in rows if isinstance(row, dict)])
        analysis_plan = {**analysis_plan, "code": code, "source": "fallback"}
        analysis_logic = "fallback"

    executed = _execute_code(code, rows, plan)
    if not executed.get("success") and analysis_logic == "llm":
        primary_error = executed.get("error_message", "")
        fallback = _fallback_code(plan, [str(column) for column in columns], domain, [row for row in rows if isinstance(row, dict)])
        executed = _execute_code(fallback, rows, plan)
        if executed.get("success"):
            code = fallback
            analysis_plan = {**analysis_plan, "code": fallback, "source": "fallback_after_error", "warnings": [*_as_list(analysis_plan.get("warnings")), primary_error]}
            analysis_logic = "fallback_after_error"

    result_rows = executed.get("data", []) if executed.get("success") else []
    result = {
        "success": bool(executed.get("success")),
        "tool_name": "analyze_current_data",
        "data": _json_safe(result_rows),
        "summary": f"data analysis complete: {len(result_rows)} rows" if executed.get("success") else executed.get("error_message", "data analysis failed"),
        "error_message": "" if executed.get("success") else executed.get("error_message", ""),
        "analysis_logic": analysis_logic,
        "analysis_plan": analysis_plan,
        "generated_code": code,
        "filter_notes": executed.get("filter_notes", []),
        "source_results": source_results,
        "source_dataset_keys": [str(item.get("dataset_key")) for item in source_results if item.get("dataset_key")],
        "current_datasets": retrieval.get("current_datasets", {}),
        "source_snapshots": retrieval.get("source_snapshots", []),
        "retrieval_applied_params": plan.get("required_params", {}) if isinstance(plan, dict) else {},
        "retrieval_applied_filters": plan.get("filters", {}) if isinstance(plan, dict) else {},
        "retrieval_applied_column_filters": plan.get("column_filters", {}) if isinstance(plan, dict) else {},
        "filter_plan": plan.get("filter_plan", []) if isinstance(plan, dict) else [],
        "followup_applied_params": plan if isinstance(plan, dict) and plan.get("query_mode") == "followup_transform" else {},
        "intent_plan": plan if isinstance(plan, dict) else {},
        "state": state,
        "user_question": state.get("pending_user_question", ""),
        "merge_notes": table.get("merge_notes", []),
        "awaiting_analysis_choice": bool(executed.get("success")),
    }
    return {"analysis_result": result}


class PandasAnalysisExecutor(Component):
    display_name = "Pandas Analysis Executor"
    description = "Execute a normalized pandas analysis plan and emit the canonical analysis result."
    icon = "Play"
    name = "PandasAnalysisExecutor"

    inputs = [
        DataInput(name="analysis_plan_payload", display_name="Analysis Plan Payload", info="Output from Normalize Pandas Plan.", input_types=["Data", "JSON"]),
        DataInput(name="retrieval_payload", display_name="Retrieval Payload Override", info="Optional override for direct wiring experiments.", input_types=["Data", "JSON"], advanced=True),
    ]
    outputs = [Output(name="analysis_result", display_name="Analysis Result", method="build_result", types=["Data"])]

    def build_result(self):
        payload = execute_pandas_analysis(getattr(self, "analysis_plan_payload", None), getattr(self, "retrieval_payload", None))
        result = payload.get("analysis_result", {})
        self.status = {"success": result.get("success"), "rows": len(result.get("data", [])) if isinstance(result.get("data"), list) else 0, "logic": result.get("analysis_logic")}
        return _make_data(payload)

