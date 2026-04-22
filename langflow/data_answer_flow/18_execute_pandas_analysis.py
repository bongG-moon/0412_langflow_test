from __future__ import annotations

import ast
import json
from copy import deepcopy
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
FILTER_COLUMN_ALIASES = {
    "process": ["OPER_NAME", "공정군", "PROCESS", "process"],
    "oper_name": ["OPER_NAME"],
    "line": ["LINE", "라인", "line"],
    "mode": ["MODE"],
    "den": ["DEN"],
    "tech": ["TECH"],
    "mcp_no": ["MCP_NO"],
    "product": ["PRODUCT_KEY", "MCP_NO", "MODE", "DEN", "TECH", "PKG_TYPE1", "PKG_TYPE2", "TSV_DIE_TYP"],
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
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _analysis_context(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    context = payload.get("analysis_context")
    return context if isinstance(context, dict) else payload


def _analysis_plan(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    plan = payload.get("analysis_plan")
    return plan if isinstance(plan, dict) else payload


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _load_pandas() -> Any:
    try:
        return import_module("pandas")
    except Exception as exc:
        raise RuntimeError(f"pandas import failed: {exc}") from exc


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
        return False, f"생성된 pandas 코드 문법 오류: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            return False, f"허용되지 않는 구문입니다: {type(node).__name__}"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return False, f"허용되지 않는 이름입니다: {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, "dunder 속성 접근은 허용되지 않습니다."
    if not _has_result_assignment(tree):
        return False, "pandas 코드는 `result = ...` 할당이 필요합니다."
    return True, None


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "")


def _matching_columns(frame: Any, filter_key: str) -> list[str]:
    candidates = FILTER_COLUMN_ALIASES.get(str(filter_key).lower(), [filter_key])
    return [column for column in candidates if column in frame.columns]


def _apply_series_filter(frame: Any, columns: list[str], values: list[Any]) -> Any:
    if not columns or not values:
        return frame
    pd = _load_pandas()
    mask = pd.Series([False] * len(frame), index=frame.index)
    normalized_values = [_normalize_text(value) for value in values if str(value).strip()]
    for column in columns:
        series = frame[column].astype(str).map(_normalize_text)
        for value in normalized_values:
            mask = mask | series.eq(value) | series.str.contains(value, regex=False, na=False)
    return frame[mask]


def _apply_intent_filters(frame: Any, intent: Dict[str, Any]) -> tuple[Any, list[str]]:
    notes: list[str] = []
    filters = intent.get("filters") if isinstance(intent.get("filters"), dict) else {}
    for key, value in filters.items():
        columns = _matching_columns(frame, str(key))
        if not columns:
            continue
        before = len(frame)
        frame = _apply_series_filter(frame, columns, _as_list(value))
        notes.append(f"filter {key} on {','.join(columns)}: {before}->{len(frame)}")

    for expr in _as_list(intent.get("filter_expressions")):
        if not isinstance(expr, dict):
            continue
        column = str(expr.get("column") or expr.get("field") or "").strip()
        if column not in frame.columns:
            continue
        operator = str(expr.get("operator") or expr.get("op") or "eq").lower()
        value = expr.get("value")
        before = len(frame)
        if operator in {"eq", "=", "=="}:
            frame = _apply_series_filter(frame, [column], _as_list(value))
        elif operator in {"in"}:
            frame = _apply_series_filter(frame, [column], _as_list(value))
        elif operator in {"contains"}:
            frame = _apply_series_filter(frame, [column], _as_list(value))
        elif operator in {"ne", "!=", "not_eq"}:
            normalized_values = {_normalize_text(item) for item in _as_list(value)}
            frame = frame[~frame[column].astype(str).map(_normalize_text).isin(normalized_values)]
        notes.append(f"filter_expression {column} {operator}: {before}->{len(frame)}")
    return frame, notes


def _fallback_code(intent: Dict[str, Any], columns: list[str]) -> str:
    group_by = [column for column in _as_list(intent.get("group_by")) if str(column) in columns]
    numeric_candidates = [
        column
        for column in ["production", "target", "wip_qty", "hold_qty", "scrap_qty", "defect_qty", "pass_qty", "tested_qty"]
        if column in columns
    ]
    if not numeric_candidates:
        numeric_candidates = [column for column in columns if column not in group_by][:1]
    if group_by and numeric_candidates:
        return f"result = df.groupby({group_by!r}, as_index=False)[{numeric_candidates!r}].sum()"
    if numeric_candidates:
        items = ", ".join(f"{column!r}: [df[{column!r}].sum()]" for column in numeric_candidates)
        return f"result = pd.DataFrame({{{items}}})"
    return "result = df.copy()"


def _execute_code(code: str, rows: list[Dict[str, Any]], intent: Dict[str, Any]) -> Dict[str, Any]:
    pd = _load_pandas()
    ok, error = _validate_python_code(code)
    if not ok:
        return {"success": False, "error_message": error, "data": []}
    frame = pd.DataFrame(rows or [])
    frame, filter_notes = _apply_intent_filters(frame, intent)
    local_vars = {"df": frame.copy(), "pd": pd, "result": None}
    safe_globals = {"__builtins__": SAFE_BUILTINS}
    try:
        exec(code, safe_globals, local_vars)
    except Exception as exc:
        return {"success": False, "error_message": f"분석 코드 실행 실패: {exc}", "data": [], "filter_notes": filter_notes}
    result = local_vars.get("result")
    if result is None:
        return {"success": False, "error_message": "분석 코드가 result 변수를 만들지 않았습니다.", "data": [], "filter_notes": filter_notes}
    if isinstance(result, pd.Series):
        result = result.to_frame().reset_index()
    if not isinstance(result, pd.DataFrame):
        return {"success": False, "error_message": "분석 결과가 DataFrame이 아닙니다.", "data": [], "filter_notes": filter_notes}
    result = result.where(pd.notnull(result), None)
    return {"success": True, "data": result.to_dict(orient="records"), "filter_notes": filter_notes}


def _source_keys(source_results: list[Dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for result in source_results:
        key = str(result.get("dataset_key") or "").strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def execute_pandas_analysis(analysis_context_payload: Any, analysis_plan_payload: Any) -> Dict[str, Any]:
    context = _analysis_context(analysis_context_payload)
    plan = _analysis_plan(analysis_plan_payload)
    table = context.get("analysis_table") if isinstance(context.get("analysis_table"), dict) else {}
    agent_state = context.get("agent_state") if isinstance(context.get("agent_state"), dict) else {}
    intent = context.get("intent") if isinstance(context.get("intent"), dict) else {}

    if isinstance(context.get("early_result"), dict):
        return {
            "analysis_result": {
                **context["early_result"],
                "success": False,
                "data": [],
                "summary": context["early_result"].get("response", ""),
                "analysis_logic": "early_result",
                "agent_state": agent_state,
            }
        }

    rows = table.get("data") if isinstance(table.get("data"), list) else []
    columns = table.get("columns") if isinstance(table.get("columns"), list) else (list(rows[0].keys()) if rows and isinstance(rows[0], dict) else [])
    if not rows:
        return {
            "analysis_result": {
                "success": False,
                "tool_name": "analyze_current_data",
                "error_message": table.get("summary", "분석할 데이터가 없습니다."),
                "data": [],
                "summary": table.get("summary", "분석할 데이터가 없습니다."),
                "current_data": agent_state.get("current_data"),
                "extracted_params": intent.get("required_params", {}),
                "awaiting_analysis_choice": False,
                "agent_state": agent_state,
            }
        }

    code = str(plan.get("code") or "").strip()
    analysis_logic = "llm_primary"
    if not code:
        code = _fallback_code(intent, [str(column) for column in columns])
        plan = {**plan, "code": code, "source": "fallback"}
        analysis_logic = "fallback"

    executed = _execute_code(code, rows, intent)
    if not executed.get("success") and analysis_logic != "fallback":
        fallback = _fallback_code(intent, [str(column) for column in columns])
        fallback_executed = _execute_code(fallback, rows, intent)
        if fallback_executed.get("success"):
            executed = fallback_executed
            plan = {**plan, "code": fallback, "source": "fallback_after_error", "warnings": [*plan.get("warnings", []), executed.get("error_message", "")]}
            analysis_logic = "fallback_after_error"

    source_results = context.get("source_results") if isinstance(context.get("source_results"), list) else []
    result_rows = executed.get("data", []) if executed.get("success") else []
    analysis_result = {
        "success": bool(executed.get("success")),
        "tool_name": "analyze_current_data",
        "data": result_rows,
        "summary": (
            f"데이터 분석 완료: {len(result_rows)}건"
            if executed.get("success")
            else executed.get("error_message", "데이터 분석에 실패했습니다.")
        ),
        "error_message": "" if executed.get("success") else executed.get("error_message", ""),
        "analysis_plan": plan,
        "analysis_logic": analysis_logic,
        "generated_code": code,
        "filter_notes": executed.get("filter_notes", []),
        "transformation_summary": {
            "input_rows": len(rows),
            "output_rows": len(result_rows),
            "operations": plan.get("operations", []),
            "analysis_logic": analysis_logic,
        },
        "source_results": source_results,
        "source_dataset_keys": _source_keys(source_results),
        "current_datasets": context.get("current_datasets", {}),
        "source_snapshots": context.get("source_snapshots", []),
        "retrieval_plan": context.get("retrieval_plan", {}),
        "merge_notes": context.get("merge_notes", []),
        "retrieval_applied_params": (
            context.get("retrieval_plan", {}).get("jobs", [{}])[0].get("params", {})
            if isinstance(context.get("retrieval_plan", {}).get("jobs"), list) and context.get("retrieval_plan", {}).get("jobs")
            else intent.get("required_params", {})
        ),
        "followup_applied_params": intent if context.get("route") == "followup_transform" else {},
        "intent": intent,
        "agent_state": agent_state,
        "user_question": context.get("user_question", ""),
        "awaiting_analysis_choice": bool(executed.get("success")),
    }
    return {"analysis_result": analysis_result}


class ExecutePandasAnalysis(Component):
    display_name = "Execute Pandas Analysis"
    description = "Safely execute generated pandas code against the analysis table and return the analysis result."
    icon = "Play"
    name = "ExecutePandasAnalysis"

    inputs = [
        DataInput(name="analysis_context", display_name="Analysis Context", info="Output from Analysis Base Builder.", input_types=["Data", "JSON"]),
        DataInput(name="analysis_plan", display_name="Analysis Plan", info="Output from Parse Pandas Analysis JSON.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="analysis_result", display_name="Analysis Result", method="build_result", types=["Data"]),
    ]

    def build_result(self) -> Data:
        payload = execute_pandas_analysis(getattr(self, "analysis_context", None), getattr(self, "analysis_plan", None))
        result = payload.get("analysis_result", {})
        self.status = {
            "success": result.get("success", False),
            "row_count": len(result.get("data", [])) if isinstance(result.get("data"), list) else 0,
            "logic": result.get("analysis_logic", ""),
        }
        return _make_data(payload)
