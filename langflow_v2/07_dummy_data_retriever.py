from __future__ import annotations

import json
import random
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
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
    return [value]


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _normalize_yyyymmdd(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return datetime.now().strftime("%Y%m%d")


def _stable_seed(value: Any, offset: int = 0) -> int:
    text = str(value or "")
    return int(text) + offset if text.isdigit() else sum(ord(ch) for ch in text) + offset


def _quantity(value: Any) -> str:
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return str(value)


PROCESSES = [
    {"OPER_NAME": "D/A1", "OPER_NUM": "DA10", "family": "DA", "LINE": "DA-L1"},
    {"OPER_NAME": "D/A2", "OPER_NUM": "DA20", "family": "DA", "LINE": "DA-L2"},
    {"OPER_NAME": "D/A3", "OPER_NUM": "DA30", "family": "DA", "LINE": "DA-L3"},
    {"OPER_NAME": "W/B1", "OPER_NUM": "WB10", "family": "WB", "LINE": "WB-L1"},
    {"OPER_NAME": "W/B2", "OPER_NUM": "WB20", "family": "WB", "LINE": "WB-L2"},
    {"OPER_NAME": "PLH", "OPER_NUM": "PL10", "family": "PL", "LINE": "PL-L1"},
]


PRODUCTS = [
    {"MODE": "DDR5", "DEN": "512G", "TECH": "WB", "MCP_NO": "MCP-A1", "PKG_TYPE1": "PKG_A", "PKG_TYPE2": "AUTO"},
    {"MODE": "DDR5", "DEN": "256G", "TECH": "WB", "MCP_NO": "MCP-A2", "PKG_TYPE1": "PKG_A", "PKG_TYPE2": "STD"},
    {"MODE": "LPDDR5", "DEN": "128G", "TECH": "FC", "MCP_NO": "MCP-B1", "PKG_TYPE1": "PKG_B", "PKG_TYPE2": "MOBILE"},
    {"MODE": "HBM3", "DEN": "1024G", "TECH": "TSV", "MCP_NO": "MCP-H1", "PKG_TYPE1": "PKG_H", "PKG_TYPE2": "HBM"},
]


def _matches(value: Any, expected: Any) -> bool:
    values = [_normalize_text(item) for item in _as_list(expected) if str(item).strip()]
    if not values:
        return True
    actual = _normalize_text(value)
    return any(actual == item or item in actual for item in values)


def _apply_filters(rows: list[Dict[str, Any]], params: Dict[str, Any]) -> list[Dict[str, Any]]:
    filtered = []
    for row in rows:
        if not _matches(row.get("OPER_NAME"), params.get("process_name") or params.get("process")):
            continue
        if not _matches(row.get("OPER_NUM"), params.get("oper_num")):
            continue
        if not _matches(row.get("LINE"), params.get("line_name") or params.get("line")):
            continue
        if not _matches(row.get("MODE"), params.get("mode")):
            continue
        if not _matches(row.get("DEN"), params.get("den")):
            continue
        if not _matches(row.get("TECH"), params.get("tech")):
            continue
        if not _matches(row.get("MCP_NO"), params.get("mcp_no")):
            continue
        product_name = params.get("product_name") or params.get("product")
        if product_name and not any(_matches(row.get(column), product_name) for column in ("MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2")):
            continue
        filtered.append(row)
    return filtered


def _base_rows(params: Dict[str, Any], offset: int = 0) -> list[Dict[str, Any]]:
    work_date = _normalize_yyyymmdd(params.get("date"))
    random.seed(_stable_seed(work_date, offset))
    rows = [{"WORK_DT": work_date, **process, **product} for process in PROCESSES for product in PRODUCTS]
    return _apply_filters(rows, params)


def _result(tool_name: str, dataset_key: str, rows: list[Dict[str, Any]], summary: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": True,
        "tool_name": tool_name,
        "dataset_key": dataset_key,
        "dataset_label": dataset_key,
        "data": rows,
        "summary": summary,
        "applied_params": deepcopy(params),
    }


def get_production_data(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 100)
    for row in rows:
        base = 3300 if row.get("family") == "DA" else 2200
        row["production"] = int(base * random.uniform(0.6, 1.2))
        if row.get("OPER_NAME") == "D/A3" and row.get("MODE") == "DDR5":
            row["production"] = 2940 if row.get("DEN") == "512G" else 2680
    total = sum(int(row["production"]) for row in rows)
    return _result("get_production_data", "production", rows, f"total rows {len(rows)}, production {_quantity(total)}", params)


def get_target_data(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 200)
    for row in rows:
        row["target"] = 3600 if row.get("family") == "DA" else 2600
        if row.get("OPER_NAME") == "D/A3" and row.get("MODE") == "DDR5":
            row["target"] = 3600 if row.get("DEN") == "512G" else 3400
    total = sum(int(row["target"]) for row in rows)
    return _result("get_target_data", "target", rows, f"total rows {len(rows)}, target {_quantity(total)}", params)


def get_wip_status(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 300)
    for row in rows:
        row["wip_qty"] = random.randint(100, 2600)
        row["avg_wait_minutes"] = random.randint(10, 240)
        row["status"] = random.choice(["QUEUED", "RUNNING", "HOLD", "REWORK"])
    total = sum(int(row["wip_qty"]) for row in rows)
    return _result("get_wip_status", "wip", rows, f"total rows {len(rows)}, WIP {_quantity(total)}", params)


def get_equipment_status(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 400)
    for index, row in enumerate(rows, start=1):
        row["equipment_id"] = f"EQ-{index:03d}"
        row["planned_hours"] = 24.0
        row["actual_hours"] = round(random.uniform(14.0, 23.5), 1)
        row["utilization_rate"] = round(row["actual_hours"] / row["planned_hours"] * 100, 1)
    return _result("get_equipment_status", "equipment", rows, f"total rows {len(rows)}", params)


def get_defect_rate(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 500)
    for row in rows:
        row["inspection_qty"] = random.randint(2500, 8000)
        row["defect_qty"] = int(row["inspection_qty"] * random.uniform(0.004, 0.03))
        row["defect_rate"] = round(row["defect_qty"] / row["inspection_qty"] * 100, 2)
    return _result("get_defect_rate", "defect", rows, f"total rows {len(rows)}", params)


def get_yield_data(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 600)
    for row in rows:
        row["tested_qty"] = random.randint(2200, 7800)
        row["yield_rate"] = round(random.uniform(92.0, 99.8), 2)
        row["pass_qty"] = int(row["tested_qty"] * row["yield_rate"] / 100)
    return _result("get_yield_data", "yield", rows, f"total rows {len(rows)}", params)


def get_hold_lot_data(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 700)
    for index, row in enumerate(rows, start=1):
        row["lot_id"] = f"LOT-{row['WORK_DT'][-4:]}-{index:03d}"
        row["hold_qty"] = random.randint(80, 1800)
        row["hold_reason"] = random.choice(["recipe approval hold", "QA review", "material hold"])
    return _result("get_hold_lot_data", "hold", rows, f"total rows {len(rows)}", params)


def get_scrap_data(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 800)
    for row in rows:
        row["input_qty"] = random.randint(1800, 7200)
        row["scrap_qty"] = int(row["input_qty"] * random.uniform(0.002, 0.028))
        row["scrap_rate"] = round(row["scrap_qty"] / row["input_qty"] * 100, 2)
    return _result("get_scrap_data", "scrap", rows, f"total rows {len(rows)}", params)


def get_recipe_condition_data(params: Dict[str, Any]) -> Dict[str, Any]:
    rows = _base_rows(params, 900)
    for row in rows:
        row["recipe_id"] = f"RC-{row['family']}-{random.randint(10, 99)}"
        row["temp_c"] = round(random.uniform(25, 245), 1)
        row["pressure_kpa"] = round(random.uniform(0, 130), 1)
    return _result("get_recipe_condition_data", "recipe", rows, f"total rows {len(rows)}", params)


def get_lot_trace_data(params: Dict[str, Any]) -> Dict[str, Any]:
    lot_id = str(params.get("lot_id") or "LOT-DEMO-001")
    rows = [{"lot_id": lot_id, "route_step": index, "OPER_NAME": process["OPER_NAME"], "status": random.choice(["WAIT", "RUNNING", "MOVE_OUT", "HOLD"])} for index, process in enumerate(PROCESSES, start=1)]
    return _result("get_lot_trace_data", "lot_trace", rows, f"lot trace rows {len(rows)}", params)


TOOL_REGISTRY = {
    "production": get_production_data,
    "get_production_data": get_production_data,
    "target": get_target_data,
    "get_target_data": get_target_data,
    "wip": get_wip_status,
    "get_wip_status": get_wip_status,
    "equipment": get_equipment_status,
    "get_equipment_status": get_equipment_status,
    "defect": get_defect_rate,
    "get_defect_rate": get_defect_rate,
    "yield": get_yield_data,
    "get_yield_data": get_yield_data,
    "hold": get_hold_lot_data,
    "get_hold_lot_data": get_hold_lot_data,
    "scrap": get_scrap_data,
    "get_scrap_data": get_scrap_data,
    "recipe": get_recipe_condition_data,
    "get_recipe_condition_data": get_recipe_condition_data,
    "lot_trace": get_lot_trace_data,
    "get_lot_trace_data": get_lot_trace_data,
}


def _rows_columns(rows: list[Dict[str, Any]]) -> list[str]:
    return [str(key) for key in rows[0].keys()] if rows and isinstance(rows[0], dict) else []


def _build_current_datasets(source_results: list[Dict[str, Any]]) -> Dict[str, Any]:
    datasets = {}
    for result in source_results:
        dataset_key = str(result.get("dataset_key") or result.get("tool_name") or "source")
        rows = [row for row in result.get("data", []) if isinstance(row, dict)] if isinstance(result.get("data"), list) else []
        datasets[dataset_key] = {"label": result.get("dataset_label", dataset_key), "tool_name": result.get("tool_name", ""), "summary": result.get("summary", ""), "row_count": len(rows), "columns": _rows_columns(rows), "data": deepcopy(rows)}
    return datasets


def _build_source_snapshots(source_results: list[Dict[str, Any]], jobs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    snapshots = []
    for index, result in enumerate(source_results):
        job = jobs[index] if index < len(jobs) and isinstance(jobs[index], dict) else {}
        rows = [row for row in result.get("data", []) if isinstance(row, dict)] if isinstance(result.get("data"), list) else []
        snapshots.append({"dataset_key": result.get("dataset_key", job.get("dataset_key", f"source_{index + 1}")), "dataset_label": result.get("dataset_label", job.get("dataset_label", "")), "tool_name": result.get("tool_name", job.get("tool_name", "")), "summary": result.get("summary", ""), "row_count": len(rows), "columns": _rows_columns(rows), "required_params": deepcopy(job.get("params", {})), "data": deepcopy(rows)})
    return snapshots


def _source_result_from_current_data(current_data: Dict[str, Any]) -> Dict[str, Any]:
    rows = [row for row in current_data.get("data", []) if isinstance(row, dict)] if isinstance(current_data.get("data"), list) else []
    dataset_keys = current_data.get("source_dataset_keys") if isinstance(current_data.get("source_dataset_keys"), list) else []
    return {"success": True, "tool_name": current_data.get("tool_name") or current_data.get("original_tool_name") or "current_data", "dataset_key": dataset_keys[0] if dataset_keys else current_data.get("dataset_key", "current_data"), "dataset_label": current_data.get("dataset_label", "Current Data"), "data": deepcopy(rows), "summary": current_data.get("summary", f"current data {len(rows)} rows reused"), "reused_current_data": True}


def _error_result(job: Dict[str, Any], message: str, failure_type: str = "retrieval_failed") -> Dict[str, Any]:
    dataset_key = str(job.get("dataset_key") or "unknown")
    return {"success": False, "tool_name": job.get("tool_name", dataset_key), "dataset_key": dataset_key, "dataset_label": job.get("dataset_label", dataset_key), "data": [], "summary": "", "error_message": message, "failure_type": failure_type, "applied_params": deepcopy(job.get("params", {}))}


def _run_job(job: Dict[str, Any]) -> Dict[str, Any]:
    tool_name = str(job.get("tool_name") or job.get("dataset_key") or "")
    tool = TOOL_REGISTRY.get(tool_name) or TOOL_REGISTRY.get(str(job.get("dataset_key") or ""))
    if tool is None:
        return _error_result(job, f"Unsupported dummy retrieval tool: {tool_name}", "unsupported_tool")
    params = deepcopy(job.get("params", {}))
    params.update({key: value for key, value in (job.get("filters") or {}).items() if value not in (None, "", [])})
    result = tool(params)
    result["dataset_key"] = job.get("dataset_key", result.get("dataset_key"))
    result["dataset_label"] = job.get("dataset_label", result.get("dataset_label", result.get("dataset_key")))
    return result


def retrieve_dummy_data(intent_plan_value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(intent_plan_value)
    plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}

    if plan.get("route") == "finish" or plan.get("query_mode") == "finish":
        early_result = {"response": plan.get("response", ""), "tool_results": [], "current_data": state.get("current_data"), "extracted_params": plan.get("required_params", {}), "awaiting_analysis_choice": bool(state.get("current_data")), "failure_type": plan.get("failure_type", "early_finish")}
        return {"retrieval_payload": {"route": "finish", "early_result": early_result, "source_results": [], "intent_plan": plan, "state": state, "used_dummy_data": False}, "intent_plan": plan, "state": state}

    if plan.get("route") == "followup_transform":
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
        source_results = [_source_result_from_current_data(current_data)] if current_data else []
        return {"retrieval_payload": {"route": "followup_transform", "source_results": source_results, "current_datasets": _build_current_datasets(source_results), "source_snapshots": deepcopy(current_data.get("source_snapshots", [])) if isinstance(current_data, dict) else [], "intent_plan": plan, "state": state, "used_dummy_data": False}, "intent_plan": plan, "state": state}

    jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
    source_results = [_run_job(job) for job in jobs if isinstance(job, dict)]
    return {"retrieval_payload": {"route": plan.get("route", "single_retrieval"), "source_results": source_results, "current_datasets": _build_current_datasets(source_results), "source_snapshots": _build_source_snapshots(source_results, jobs), "intent_plan": plan, "state": state, "used_dummy_data": True}, "intent_plan": plan, "state": state}


class DummyDataRetriever(Component):
    display_name = "V2 Dummy Data Retriever"
    description = "Standalone dummy retriever that executes every planned retrieval job."
    icon = "Database"
    name = "V2DummyDataRetriever"

    inputs = [DataInput(name="intent_plan", display_name="Intent Plan", info="Output from V2 Normalize Intent Plan.", input_types=["Data", "JSON"])]
    outputs = [Output(name="retrieval_payload", display_name="Retrieval Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = retrieve_dummy_data(getattr(self, "intent_plan", None))
        retrieval = payload.get("retrieval_payload", {})
        source_results = retrieval.get("source_results", []) if isinstance(retrieval.get("source_results"), list) else []
        self.status = {"route": retrieval.get("route"), "source_count": len(source_results), "success_count": sum(1 for item in source_results if isinstance(item, dict) and item.get("success"))}
        return _make_data(payload)
