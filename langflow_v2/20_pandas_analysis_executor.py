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
FILTER_COLUMNS = {
    "process_name": ["OPER_NAME", "PROCESS", "process"],
    "process": ["OPER_NAME", "PROCESS", "process"],
    "mode": ["MODE"],
    "line_name": ["LINE", "line"],
    "line": ["LINE", "line"],
    "product_name": ["MCP_NO", "MODE", "DEN", "TECH", "PKG_TYPE1", "PKG_TYPE2"],
    "product": ["MCP_NO", "MODE", "DEN", "TECH", "PKG_TYPE1", "PKG_TYPE2"],
}
PREFERRED_JOIN_COLUMNS = ["WORK_DT", "WORK_DATE", "OPER_NAME", "OPER_NUM", "MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2", "LINE", "line"]


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


def _merge_sources(source_results: list[Dict[str, Any]]) -> Dict[str, Any]:
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
        join_columns = [column for column in PREFERRED_JOIN_COLUMNS if column in shared] or sorted(shared)[:3]
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
        columns = [column for column in FILTER_COLUMNS.get(str(key), [str(key)]) if column in frame.columns]
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
    state = retrieval.get("state") if isinstance(retrieval.get("state"), dict) else {}
    source_results = _source_results(retrieval)
    if payload.get("skipped") or retrieval.get("skipped"):
        result = {"skipped": True, "skip_reason": payload.get("skip_reason") or retrieval.get("skip_reason", "route skipped"), "success": False, "tool_name": "analyze_current_data", "data": [], "summary": "", "error_message": "", "analysis_logic": "post_analysis_skipped", "analysis_plan": analysis_plan, "source_results": [], "intent_plan": plan if isinstance(plan, dict) else {}, "state": state, "awaiting_analysis_choice": False}
        return {"analysis_result": result}

    if isinstance(retrieval.get("early_result"), dict):
        result = {**retrieval["early_result"], "success": False, "data": [], "summary": retrieval["early_result"].get("response", ""), "analysis_logic": "early_result", "source_results": source_results, "state": state, "intent_plan": plan}
        return {"analysis_result": result}

    table = payload.get("table") if isinstance(payload.get("table"), dict) and payload.get("table") else _merge_sources(source_results)
    rows = table.get("data") if isinstance(table.get("data"), list) else []
    columns = table.get("columns") if isinstance(table.get("columns"), list) else _rows_columns(rows)
    if not table.get("success") or not rows:
        result = {"success": False, "tool_name": "analyze_current_data", "data": [], "summary": table.get("summary", "No data to analyze."), "error_message": table.get("summary", "No data to analyze."), "analysis_logic": "no_data", "source_results": source_results, "state": state, "intent_plan": plan, "awaiting_analysis_choice": False}
        return {"analysis_result": result}

    code = str(analysis_plan.get("code") or "").strip()
    analysis_logic = str(analysis_plan.get("source") or "analysis_plan")
    if not code:
        code = _fallback_code(plan, [str(column) for column in columns])
        analysis_plan = {**analysis_plan, "code": code, "source": "fallback"}
        analysis_logic = "fallback"

    executed = _execute_code(code, rows, plan)
    if not executed.get("success") and analysis_logic == "llm":
        primary_error = executed.get("error_message", "")
        fallback = _fallback_code(plan, [str(column) for column in columns])
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

