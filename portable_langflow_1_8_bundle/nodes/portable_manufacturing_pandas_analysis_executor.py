"""Portable Langflow node: safely execute LLM-generated pandas analysis code."""

from __future__ import annotations

import ast
import importlib
import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


SAFE_BUILTINS = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "abs": abs,
    "round": round,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
}

FORBIDDEN_NAMES = {
    "open",
    "exec",
    "eval",
    "compile",
    "__import__",
    "os",
    "sys",
    "subprocess",
    "socket",
    "requests",
    "httpx",
}

FORBIDDEN_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.Try,
    ast.While,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.Delete,
)

DEFAULT_JOIN_KEYS = ["WORK_DT", "OPER_NAME", "line_name", "product_name"]


def _load_pandas():
    try:
        return importlib.import_module("pandas")
    except ModuleNotFoundError:
        return None


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
        return {"code": cleaned}
    try:
        return json.loads(cleaned[start : end + 1])
    except Exception:
        return {"code": cleaned}


def _merge_registry(raw_value: Any) -> dict[str, Any]:
    payload = _as_payload(raw_value)
    custom = payload.get("custom_registry") if isinstance(payload.get("custom_registry"), dict) else payload
    return {
        "analysis_rules": custom.get("analysis_rules", []),
        "join_rules": custom.get("join_rules", []),
    }


def _has_result_assignment(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "result":
                    return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "result":
            return True
    return False


def _validate_python_code(code: str) -> tuple[bool, str | None]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Generated pandas code has a syntax error: {exc}"

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            return False, f"Forbidden syntax detected: {type(node).__name__}"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return False, f"Forbidden name detected: {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, "Dunder attribute access is not allowed."

    if not _has_result_assignment(tree):
        return False, "Generated pandas code must assign a DataFrame to `result`."

    return True, None


def _execute_safe_dataframe_code(code: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    pd = _load_pandas()
    if pd is None:
        return {
            "success": False,
            "error_message": "pandas is not installed. Install pandas first with Portable Dependency Bootstrap.",
            "data": [],
        }
    ok, error = _validate_python_code(code)
    if not ok:
        return {"success": False, "error_message": error, "data": []}

    df = pd.DataFrame(rows or [])
    safe_globals = {"__builtins__": SAFE_BUILTINS}
    local_vars = {"df": df.copy(), "pd": pd, "result": None}
    try:
        exec(code, safe_globals, local_vars)
    except Exception as exc:
        return {"success": False, "error_message": f"Pandas analysis execution failed: {exc}", "data": []}

    result = local_vars.get("result")
    if result is None:
        return {"success": False, "error_message": "The generated code did not populate `result`.", "data": []}
    if pd is not None and isinstance(result, pd.Series):
        result = result.to_frame().reset_index()
    if pd is None or not isinstance(result, pd.DataFrame):
        return {"success": False, "error_message": "The generated analysis result is not a DataFrame.", "data": []}
    result = result.where(pd.notnull(result), None)
    return {"success": True, "data": result.to_dict(orient="records")}


def _join_keys(left_rows: list[dict[str, Any]], right_rows: list[dict[str, Any]], join_rules: list[dict[str, Any]]) -> list[str]:
    for rule in join_rules:
        keys = [str(item) for item in rule.get("join_keys", []) if str(item).strip()]
        if keys:
            return keys
    if left_rows and right_rows:
        left_keys = set(left_rows[0].keys())
        right_keys = set(right_rows[0].keys())
        return [key for key in DEFAULT_JOIN_KEYS if key in left_keys and key in right_keys] or [key for key in left_keys.intersection(right_keys) if key in {"WORK_DT", "OPER_NAME"}]
    return ["WORK_DT", "OPER_NAME"]


def _merge_rows(left_rows: list[dict[str, Any]], right_rows: list[dict[str, Any]], dataset_key: str, join_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not left_rows:
        return [dict(row) for row in right_rows]
    if not right_rows:
        return [dict(row) for row in left_rows]

    keys = _join_keys(left_rows, right_rows, join_rules)
    right_index = {tuple(str(row.get(key) or "") for key in keys): row for row in right_rows}
    merged: list[dict[str, Any]] = []
    for left in left_rows:
        joined = dict(left)
        right = right_index.get(tuple(str(left.get(key) or "") for key in keys), {})
        for key, value in right.items():
            if key in keys:
                continue
            if key not in joined:
                joined[key] = value
            elif joined.get(key) != value:
                joined[f"{dataset_key}_{key}"] = value
        merged.append(joined)
    return merged


def _analysis_input_rows(state: dict[str, Any], join_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    current_rows = current_data.get("rows") if isinstance(current_data.get("rows"), list) else []
    if current_rows and not state.get("source_results"):
        return [dict(row) for row in current_rows]

    source_results = state.get("source_results") if isinstance(state.get("source_results"), dict) else {}
    if not source_results:
        return []

    dataset_keys = []
    retrieval_plan = state.get("retrieval_plan") if isinstance(state.get("retrieval_plan"), dict) else {}
    if isinstance(retrieval_plan.get("dataset_keys"), list):
        dataset_keys = [str(item) for item in retrieval_plan["dataset_keys"] if str(item).strip()]
    if not dataset_keys:
        dataset_keys = [str(key) for key in source_results.keys()]

    merged_rows: list[dict[str, Any]] = []
    for index, dataset_key in enumerate(dataset_keys):
        dataset_rows = source_results.get(dataset_key) if isinstance(source_results.get(dataset_key), list) else []
        if index == 0:
            merged_rows = [dict(row) for row in dataset_rows]
        else:
            merged_rows = _merge_rows(merged_rows, dataset_rows, dataset_key, join_rules)
    return merged_rows


def _numeric_keys(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [key for key in rows[0] if all(isinstance(row.get(key), (int, float)) for row in rows if key in row)]


def _aggregate_rows(rows: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    if not group_by:
        return rows
    numeric_keys = _numeric_keys(rows)
    bucket: dict[str, dict[str, Any]] = {}
    for row in rows:
        group_value = str(row.get(group_by) or "unknown")
        current = bucket.setdefault(group_value, {group_by: group_value})
        for key in numeric_keys:
            current[key] = round(float(current.get(key, 0) or 0) + float(row.get(key, 0) or 0), 2)
    return list(bucket.values())


def _sort_rows(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    numeric_keys = _numeric_keys(rows)
    preferred = ["achievement_rate", "plan_gap_rate", "hold_load_index", "production_saturation_rate", "yield_rate", "production", "target", "defect_rate", "wip_qty", "hold_qty"]
    metric = next((key for key in preferred if key in numeric_keys), numeric_keys[0] if numeric_keys else "")
    ordered = sorted(rows, key=lambda row: float(row.get(metric, 0) or 0), reverse=True) if metric else rows
    return ordered[:top_n] if top_n else ordered


def _rule_by_name(state: dict[str, Any], analysis_rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    extracted = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
    matched_names = extracted.get("matched_analysis_rules") if isinstance(extracted.get("matched_analysis_rules"), list) else state.get("matched_analysis_rules", [])
    names = [str(item) for item in matched_names or []]
    for rule in analysis_rules:
        if str(rule.get("name") or "") in names:
            return rule
    return analysis_rules[0] if len(analysis_rules) == 1 else None


def _apply_rule_fallback(state: dict[str, Any], rows: list[dict[str, Any]], rule: dict[str, Any]) -> list[dict[str, Any]]:
    pd = _load_pandas()
    if pd is None:
        return []
    group_by = str((state.get("extracted_params") or {}).get("group_by") or (rule.get("default_group_by") or [""])[0] or "")
    top_n = int((state.get("extracted_params") or {}).get("top_n") or 0)
    mode = str(rule.get("calculation_mode") or "")
    df = pd.DataFrame(rows or [])
    if df.empty:
        return []

    if mode == "condition_flag":
        source_column = str((rule.get("source_columns") or [{"column": "\uc0c1\ud0dc"}])[0].get("column") or "\uc0c1\ud0dc")
        output_column = str(rule.get("output_column") or "flag")
        df[output_column] = df[source_column].apply(lambda value: "\uc774\uc0c1" if str(value) in {"HOLD", "REWORK"} else "\uc815\uc0c1")
        result = df
        if group_by and group_by in result.columns:
            result = result[[group_by, output_column]].drop_duplicates()
        return result.to_dict(orient="records")[:50]

    if mode == "preferred_metric":
        metric = str((rule.get("source_columns") or [{"column": "yield_rate"}])[0].get("column") or "yield_rate")
        result = df
        if group_by and group_by in df.columns and metric in df.columns:
            result = df.groupby(group_by, as_index=False)[metric].mean()
        return _sort_rows(result.round(4).to_dict(orient="records"), top_n)[:50]

    sources = rule.get("source_columns") or []
    if len(sources) < 2:
        grouped = _aggregate_rows(rows, group_by)
        return _sort_rows(grouped, top_n)[:50]

    numerator_col = str(sources[0].get("column") or "")
    denominator_col = str(sources[1].get("column") or "")
    output_column = str(rule.get("output_column") or "derived_metric")
    grouped_df = df
    if group_by and group_by in df.columns:
        agg_map = {column: "sum" for column in [numerator_col, denominator_col] if column in df.columns}
        grouped_df = df.groupby(group_by, as_index=False).agg(agg_map)
    if numerator_col in grouped_df.columns and denominator_col in grouped_df.columns:
        if mode == "custom_ratio_gap":
            grouped_df[output_column] = grouped_df.apply(
                lambda row: round(((float(row[numerator_col]) - float(row[denominator_col])) / float(row[denominator_col])) * 100, 2)
                if float(row[denominator_col] or 0)
                else 0.0,
                axis=1,
            )
        else:
            grouped_df[output_column] = grouped_df.apply(
                lambda row: round((float(row[numerator_col]) / float(row[denominator_col])) * 100, 2)
                if float(row[denominator_col] or 0)
                else 0.0,
                axis=1,
            )
    return _sort_rows(grouped_df.to_dict(orient="records"), top_n)[:50]


def _minimal_fallback(state: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    params = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
    grouped = _aggregate_rows(rows, str(params.get("group_by") or ""))
    return _sort_rows(grouped, int(params.get("top_n") or 0))[:50]


class PortableManufacturingPandasAnalysisExecutorComponent(Component):
    display_name = "Portable Manufacturing Pandas Analysis Executor"
    description = "Validate and execute LLM-generated pandas code with domain-rule fallback."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "PlaySquare"
    name = "portable_manufacturing_pandas_analysis_executor"

    inputs = [
        DataInput(name="state", display_name="State", info="Follow-up state or sufficient retrieval state"),
        MessageInput(name="llm_message", display_name="LLM Message", info="Response from built-in LLM Model"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON for join rules and analysis rules"),
    ]

    outputs = [
        Output(name="result_data", display_name="Result Data", method="result_data", types=["Data"], selected="Data"),
        Output(name="response_message", display_name="Response Message", method="response_message", types=["Message"], selected="Message"),
    ]

    _cached_result: dict[str, Any] | None = None

    def _run(self) -> dict[str, Any]:
        if self._cached_result is not None:
            return self._cached_result

        state = _as_payload(getattr(self, "state", None))
        registry = _merge_registry(getattr(self, "domain_registry", None))
        parsed = _parse_json_block(_message_text(getattr(self, "llm_message", None)))
        analysis_logic = str(parsed.get("analysis_logic") or "").strip() or "llm_generated_analysis"
        generated_code = str(parsed.get("code") or "").strip()

        rows = _analysis_input_rows(state, registry.get("join_rules", []))
        if not rows:
            result = {
                "response": "There is no current table to analyze.",
                "tool_results": state.get("tool_results", []),
                "current_data": state.get("current_data"),
                "extracted_params": state.get("extracted_params", {}),
                "failure_type": "missing_analysis_input",
                "awaiting_analysis_choice": False,
            }
            self._cached_result = result
            self.status = "No analysis input"
            return result

        executed = _execute_safe_dataframe_code(generated_code, rows) if generated_code else {"success": False, "error_message": "Missing code", "data": []}
        fallback_used = ""
        if not executed.get("success"):
            fallback_rule = _rule_by_name(state, registry.get("analysis_rules", []))
            if fallback_rule is not None:
                executed = {"success": True, "data": _apply_rule_fallback(state, rows, fallback_rule)}
                fallback_used = str(fallback_rule.get("name") or "domain_rule_fallback")
            else:
                executed = {"success": True, "data": _minimal_fallback(state, rows)}
                fallback_used = "minimal_fallback"

        result_rows = executed.get("data", []) if isinstance(executed.get("data"), list) else []
        columns = list(result_rows[0].keys()) if result_rows else []
        dataset_keys = (state.get("retrieval_plan") or {}).get("dataset_keys", state.get("selected_dataset_keys", []))
        response = f"LLM pandas analysis completed with {len(result_rows)} rows."
        if fallback_used:
            response = f"LLM pandas analysis fallback `{fallback_used}` applied with {len(result_rows)} rows."

        payload = {
            "response": response,
            "tool_results": state.get("tool_results", []),
            "tool_calls": state.get("tool_calls", []),
            "current_data": {"title": "analysis_result", "columns": columns, "rows": result_rows[:50]},
            "extracted_params": state.get("extracted_params", {}),
            "selected_dataset_keys": dataset_keys,
            "matched_analysis_rules": state.get("matched_analysis_rules", (state.get("extracted_params") or {}).get("matched_analysis_rules", [])),
            "analysis_logic": analysis_logic,
            "generated_code": generated_code,
            "analysis_input_columns": list(rows[0].keys()) if rows else [],
            "analysis_fallback": fallback_used or None,
            "awaiting_analysis_choice": False,
        }
        self._cached_result = payload
        self.status = "Pandas analysis executed"
        return payload

    def result_data(self) -> Data:
        return Data(data=self._run())

    def response_message(self) -> Message:
        payload = self._run()
        session_id = str(_as_payload(getattr(self, "state", None)).get("session_id") or "")
        return Message(text=str(payload.get("response") or ""), data=payload, session_id=session_id)
