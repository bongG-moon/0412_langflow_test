from __future__ import annotations

import json
import random
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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


DEFAULT_PROCESSES = ["D/A1", "D/A2", "D/A3", "WB1", "WB2", "PKG", "TEST"]
DEFAULT_PRODUCTS = [
    {
        "MODE": "LPDDR4",
        "DEN": "128G",
        "TECH": "FC",
        "MCP_NO": "POP-A100",
        "PKG_TYPE1": "LFBGA",
        "PKG_TYPE2": "POP",
        "FAB": "FAB1",
        "DEVICE": "LP4_A",
        "OWNER": "OWN1",
        "GRADE": "A",
        "MCP_SALES_NO": "P-100K1Q",
        "TSV_DIE_TYP": "",
    },
    {
        "MODE": "LPDDR5",
        "DEN": "256G",
        "TECH": "FC",
        "MCP_NO": "MOBILE-B200",
        "PKG_TYPE1": "TFBGA",
        "PKG_TYPE2": "MOBILE",
        "FAB": "FAB1",
        "DEVICE": "LP5_B",
        "OWNER": "OWN1",
        "GRADE": "A",
        "MCP_SALES_NO": "",
        "TSV_DIE_TYP": "",
    },
    {
        "MODE": "DDR5",
        "DEN": "512G",
        "TECH": "TSV",
        "MCP_NO": "HBM-C300",
        "PKG_TYPE1": "FCBGA",
        "PKG_TYPE2": "HBM",
        "FAB": "FAB2",
        "DEVICE": "HBM_C",
        "OWNER": "OWN2",
        "GRADE": "B",
        "MCP_SALES_NO": "H-300K1N",
        "TSV_DIE_TYP": "4Hi",
    },
    {
        "MODE": "AUTO",
        "DEN": "64G",
        "TECH": "WB",
        "MCP_NO": "AUTO-D400",
        "PKG_TYPE1": "VFBGA",
        "PKG_TYPE2": "AUTO",
        "FAB": "FAB3",
        "DEVICE": "AUTO_D",
        "OWNER": "OWN3",
        "GRADE": "S",
        "MCP_SALES_NO": "L-111K1Q",
        "TSV_DIE_TYP": "",
    },
]


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


def _main_context_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    main_context = payload.get("main_context")
    return main_context if isinstance(main_context, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload


def _get_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else payload


def _stable_seed(tool_name: str, params: Dict[str, Any]) -> int:
    text = json.dumps({"tool_name": tool_name, "params": params}, ensure_ascii=False, sort_keys=True)
    return sum(ord(ch) for ch in text)


def _param(params: Dict[str, Any], *names: str, default: str = "") -> str:
    for name in names:
        value = params.get(name)
        if value not in (None, "", []):
            return str(value)
    return default


def _domain_processes(domain: Dict[str, Any]) -> list[str]:
    processes: list[str] = []
    groups = domain.get("process_groups") if isinstance(domain.get("process_groups"), dict) else {}
    for key, group in groups.items():
        if isinstance(group, dict):
            processes.extend(str(item) for item in _as_list(group.get("processes")) if str(item).strip())
        else:
            processes.append(str(key))
    return processes or list(DEFAULT_PROCESSES)


def _domain_products(domain: Dict[str, Any]) -> list[Dict[str, Any]]:
    products: list[Dict[str, Any]] = []
    product_docs = domain.get("products") if isinstance(domain.get("products"), dict) else {}
    for key, product in product_docs.items():
        row = {"PRODUCT_KEY": key}
        if isinstance(product, dict):
            filters = product.get("filters") if isinstance(product.get("filters"), dict) else {}
            row.update({str(k): v for k, v in filters.items()})
            row.setdefault("MODE", product.get("mode") or product.get("display_name") or key)
            row.setdefault("DEN", product.get("den") or "UNKNOWN")
            row.setdefault("TECH", product.get("tech") or "UNKNOWN")
            row.setdefault("MCP_NO", product.get("mcp_no") or key)
            row.setdefault("PKG_TYPE1", product.get("pkg_type1") or "")
            row.setdefault("PKG_TYPE2", product.get("pkg_type2") or "")
        products.append(row)
    return products or deepcopy(DEFAULT_PRODUCTS)


def _summary_for_rows(dataset_key: str, rows: list[Dict[str, Any]]) -> str:
    if not rows:
        return f"{dataset_key} dummy data 0 rows"
    numeric_totals: list[str] = []
    for key, value in rows[0].items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total = sum(float(row.get(key) or 0) for row in rows if isinstance(row.get(key), (int, float)))
            numeric_totals.append(f"{key} total {total:,.0f}")
    suffix = ", ".join(numeric_totals[:3])
    return f"{dataset_key} dummy data {len(rows)} rows" + (f", {suffix}" if suffix else "")


def get_production_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "WORK_DT", default="2026-04-22")
    rng = random.Random(_stable_seed("get_production_data", {"date": date}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            qty = int(rng.uniform(1800, 5400))
            rows.append(
                {
                    "WORK_DT": date,
                    "OPER_NAME": process,
                    "OPER_DESC": "INPUT" if process_index % 5 == 0 else process,
                    "PROCESS_GROUP": process.split("/", 1)[0],
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "production": qty,
                    "input_qty": qty if process_index % 5 == 0 else 0,
                    "lot_count": int(qty / rng.uniform(80, 140)),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_production_data",
        "dataset_key": "production",
        "data": rows,
        "summary": _summary_for_rows("production", rows),
        "applied_params": {"date": date},
        "from_dummy": True,
    }


def get_target_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "target_date", "WORK_DT", default="2026-04-22")
    plan_version = _param(params, "plan_version", "version", default="BASE")
    rng = random.Random(_stable_seed("get_target_data", {"date": date, "plan_version": plan_version}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            rows.append(
                {
                    "WORK_DT": date,
                    "PLAN_VERSION": plan_version,
                    "OPER_NAME": process,
                    "PROCESS_GROUP": process.split("/", 1)[0],
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "target": int(rng.uniform(2600, 5900)),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_target_data",
        "dataset_key": "target",
        "data": rows,
        "summary": _summary_for_rows("target", rows),
        "applied_params": {"date": date, "plan_version": plan_version},
        "from_dummy": True,
    }


def get_schedule_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "schedule_date", "WORK_DT", default="2026-04-22")
    rng = random.Random(_stable_seed("get_schedule_data", {"date": date}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product_index, product in enumerate(_domain_products(domain), start=1):
            input_plan = int(rng.uniform(1800, 5200))
            rows.append(
                {
                    "WORK_DT": date,
                    "SCHD_SEQ": f"SCHD-{process_index:02d}-{product_index:02d}",
                    "OPER_NAME": process,
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "schedule_input_qty": input_plan,
                    "schedule_output_qty": int(input_plan * rng.uniform(0.90, 1.05)),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_schedule_data",
        "dataset_key": "schedule",
        "data": rows,
        "summary": _summary_for_rows("schedule", rows),
        "applied_params": {"date": date},
        "from_dummy": True,
    }


def get_capa_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "capa_date", "WORK_DT", default="2026-04-22")
    rng = random.Random(_stable_seed("get_capa_data", {"date": date}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            rows.append(
                {
                    "WORK_DT": date,
                    "OPER_NAME": process,
                    "PROCESS_GROUP": process.split("/", 1)[0],
                    **product,
                    "capa_qty": int(rng.uniform(3200, 7600)),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_capa_data",
        "dataset_key": "capa",
        "data": rows,
        "summary": _summary_for_rows("capa", rows),
        "applied_params": {"date": date},
        "from_dummy": True,
    }


def get_defect_rate(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "inspection_date", "WORK_DT", default="2026-04-22")
    inspection_type = _param(params, "inspection_type", "test_type", default="FINAL")
    defect_codes = ["OPEN", "SHORT", "CRACK", "ALIGN", "CONTAM"]
    rng = random.Random(_stable_seed("get_defect_rate", {"date": date, "inspection_type": inspection_type}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            inspection_qty = int(rng.uniform(3000, 8500))
            defect_qty = int(rng.uniform(12, 220))
            rows.append(
                {
                    "WORK_DT": date,
                    "INSPECTION_TYPE": inspection_type,
                    "OPER_NAME": process,
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "inspection_qty": inspection_qty,
                    "defect_qty": defect_qty,
                    "defect_rate": round(defect_qty / inspection_qty * 100, 3),
                    "top_defect_code": defect_codes[(process_index + len(rows)) % len(defect_codes)],
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_defect_rate",
        "dataset_key": "defect",
        "data": rows,
        "summary": _summary_for_rows("defect", rows),
        "applied_params": {"date": date, "inspection_type": inspection_type},
        "from_dummy": True,
    }


def get_equipment_status(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "status_date", "WORK_DT", default="2026-04-22")
    equipment_area = _param(params, "equipment_area", "area", default="ALL")
    rng = random.Random(_stable_seed("get_equipment_status", {"date": date, "equipment_area": equipment_area}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for equipment_index in range(1, 4):
            planned_hours = 24.0
            down_minutes = int(rng.uniform(0, 180))
            actual_hours = round(planned_hours - down_minutes / 60, 2)
            rows.append(
                {
                    "WORK_DT": date,
                    "EQUIPMENT_AREA": equipment_area,
                    "OPER_NAME": process,
                    "EQUIPMENT_ID": f"{process.replace('/', '')}-EQ{equipment_index:02d}",
                    "LINE": f"LINE-{equipment_index}",
                    "planned_hours": planned_hours,
                    "actual_hours": actual_hours,
                    "down_minutes": down_minutes,
                    "utilization_rate": round(actual_hours / planned_hours * 100, 2),
                    "status": "RUN" if down_minutes < 90 else "CHECK",
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_equipment_status",
        "dataset_key": "equipment",
        "data": rows,
        "summary": _summary_for_rows("equipment", rows),
        "applied_params": {"date": date, "equipment_area": equipment_area},
        "from_dummy": True,
    }


def get_wip_status(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "snapshot_date", "WORK_DT", default="2026-04-22")
    snapshot_time = _param(params, "snapshot_time", "time", default="08:00")
    rng = random.Random(_stable_seed("get_wip_status", {"date": date, "snapshot_time": snapshot_time}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            avg_wait = int(rng.uniform(15, 360))
            rows.append(
                {
                    "WORK_DT": date,
                    "SNAPSHOT_TIME": snapshot_time,
                    "OPER_NAME": process,
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "wip_qty": int(rng.uniform(200, 2800)),
                    "avg_wait_minutes": avg_wait,
                    "aging_bucket": "LONG" if avg_wait >= 180 else "NORMAL",
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_wip_status",
        "dataset_key": "wip",
        "data": rows,
        "summary": _summary_for_rows("wip", rows),
        "applied_params": {"date": date, "snapshot_time": snapshot_time},
        "from_dummy": True,
    }


def get_yield_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "test_date", "WORK_DT", default="2026-04-22")
    test_step = _param(params, "test_step", "step", default="FINAL")
    rng = random.Random(_stable_seed("get_yield_data", {"date": date, "test_step": test_step}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            tested_qty = int(rng.uniform(3200, 9000))
            pass_qty = int(tested_qty * rng.uniform(0.88, 0.995))
            rows.append(
                {
                    "WORK_DT": date,
                    "TEST_STEP": test_step,
                    "OPER_NAME": process,
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "tested_qty": tested_qty,
                    "pass_qty": pass_qty,
                    "yield_rate": round(pass_qty / tested_qty * 100, 3),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_yield_data",
        "dataset_key": "yield",
        "data": rows,
        "summary": _summary_for_rows("yield", rows),
        "applied_params": {"date": date, "test_step": test_step},
        "from_dummy": True,
    }


def get_hold_lot_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "hold_date", "WORK_DT", default="2026-04-22")
    hold_reason_group = _param(params, "hold_reason_group", "hold_group", default="ALL")
    reasons = ["SPEC_CHECK", "EQ_ALARM", "QUALITY_REVIEW", "MATERIAL_WAIT"]
    rng = random.Random(_stable_seed("get_hold_lot_data", {"date": date, "hold_reason_group": hold_reason_group}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            rows.append(
                {
                    "WORK_DT": date,
                    "HOLD_REASON_GROUP": hold_reason_group,
                    "OPER_NAME": process,
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "hold_qty": int(rng.uniform(5, 260)),
                    "hold_hours": round(rng.uniform(0.5, 48), 2),
                    "hold_reason": reasons[(process_index + len(rows)) % len(reasons)],
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_hold_lot_data",
        "dataset_key": "hold",
        "data": rows,
        "summary": _summary_for_rows("hold", rows),
        "applied_params": {"date": date, "hold_reason_group": hold_reason_group},
        "from_dummy": True,
    }


def get_scrap_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "scrap_date", "WORK_DT", default="2026-04-22")
    scrap_type = _param(params, "scrap_type", "loss_type", default="TOTAL")
    rng = random.Random(_stable_seed("get_scrap_data", {"date": date, "scrap_type": scrap_type}))
    rows: list[Dict[str, Any]] = []
    for process_index, process in enumerate(_domain_processes(domain), start=1):
        for product in _domain_products(domain):
            input_qty = int(rng.uniform(2800, 9000))
            scrap_qty = int(rng.uniform(8, 180))
            rows.append(
                {
                    "WORK_DT": date,
                    "SCRAP_TYPE": scrap_type,
                    "OPER_NAME": process,
                    "LINE": f"LINE-{(process_index % 3) + 1}",
                    **product,
                    "input_qty": input_qty,
                    "scrap_qty": scrap_qty,
                    "scrap_rate": round(scrap_qty / input_qty * 100, 3),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_scrap_data",
        "dataset_key": "scrap",
        "data": rows,
        "summary": _summary_for_rows("scrap", rows),
        "applied_params": {"date": date, "scrap_type": scrap_type},
        "from_dummy": True,
    }


def get_recipe_condition_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    date = _param(params, "date", "effective_date", "WORK_DT", default="2026-04-22")
    process = _param(params, "process", "oper_name", "OPER_NAME", default="")
    processes = _domain_processes(domain)
    selected_process = process or (processes[0] if processes else "D/A1")
    conditions = ["TEMP", "PRESSURE", "SPEED", "TIME", "FORCE"]
    rng = random.Random(_stable_seed("get_recipe_condition_data", {"date": date, "process": selected_process}))
    rows: list[Dict[str, Any]] = []
    for product in _domain_products(domain):
        for condition_index, condition in enumerate(conditions, start=1):
            target = round(rng.uniform(10, 200), 2)
            tolerance = round(rng.uniform(0.5, 5.0), 2)
            rows.append(
                {
                    "WORK_DT": date,
                    "OPER_NAME": selected_process,
                    "RECIPE_ID": f"RCP-{selected_process.replace('/', '')}-{condition_index:02d}",
                    **product,
                    "condition_name": condition,
                    "condition_value": target,
                    "lower_limit": round(target - tolerance, 2),
                    "upper_limit": round(target + tolerance, 2),
                }
            )
            if len(rows) >= row_limit:
                break
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_recipe_condition_data",
        "dataset_key": "recipe",
        "data": rows,
        "summary": _summary_for_rows("recipe", rows),
        "applied_params": {"date": date, "process": selected_process},
        "from_dummy": True,
    }


def get_lot_trace_data(params: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> Dict[str, Any]:
    lot_id = _param(params, "lot_id", "LOT_ID", default="LOT-DEMO-001")
    date = _param(params, "date", "WORK_DT", default="2026-04-22")
    product = _domain_products(domain)[0]
    rng = random.Random(_stable_seed("get_lot_trace_data", {"lot_id": lot_id, "date": date}))
    rows: list[Dict[str, Any]] = []
    hour = 8
    for sequence, process in enumerate(_domain_processes(domain), start=1):
        stay_hours = rng.randint(1, 4)
        rows.append(
            {
                "WORK_DT": date,
                "LOT_ID": lot_id,
                "SEQ": sequence,
                "OPER_NAME": process,
                **product,
                "move_in_time": f"{date} {hour:02d}:00",
                "move_out_time": f"{date} {hour + stay_hours:02d}:00",
                "stay_hours": stay_hours,
                "lot_status": "COMPLETE" if sequence < len(_domain_processes(domain)) else "CURRENT",
            }
        )
        hour += stay_hours
        if len(rows) >= row_limit:
            break
    return {
        "success": True,
        "tool_name": "get_lot_trace_data",
        "dataset_key": "lot_trace",
        "data": rows,
        "summary": _summary_for_rows("lot_trace", rows),
        "applied_params": {"lot_id": lot_id, "date": date},
        "from_dummy": True,
    }


DUMMY_TOOL_REGISTRY = {
    "production": get_production_data,
    "get_production_data": get_production_data,
    "target": get_target_data,
    "get_target_data": get_target_data,
    "schedule": get_schedule_data,
    "get_schedule_data": get_schedule_data,
    "capa": get_capa_data,
    "get_capa_data": get_capa_data,
    "defect": get_defect_rate,
    "get_defect_rate": get_defect_rate,
    "equipment": get_equipment_status,
    "get_equipment_status": get_equipment_status,
    "wip": get_wip_status,
    "get_wip_status": get_wip_status,
    "yield": get_yield_data,
    "get_yield_data": get_yield_data,
    "hold": get_hold_lot_data,
    "hold_lot": get_hold_lot_data,
    "get_hold_lot_data": get_hold_lot_data,
    "scrap": get_scrap_data,
    "get_scrap_data": get_scrap_data,
    "recipe": get_recipe_condition_data,
    "get_recipe_condition_data": get_recipe_condition_data,
    "lot_trace": get_lot_trace_data,
    "get_lot_trace_data": get_lot_trace_data,
}


def _source_result_from_current_data(current_data: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(current_data)
    result.setdefault("success", True)
    result.setdefault("tool_name", result.get("original_tool_name") or result.get("tool_name") or "current_data")
    result.setdefault(
        "dataset_key",
        (result.get("source_dataset_keys") or ["current_data"])[0]
        if isinstance(result.get("source_dataset_keys"), list)
        else "current_data",
    )
    result.setdefault("dataset_label", result.get("dataset_key", "current_data"))
    result.setdefault(
        "summary",
        f"현재 데이터 {len(result.get('data', [])) if isinstance(result.get('data'), list) else 0}건 재사용",
    )
    return result


def _build_current_datasets(source_results: list[Dict[str, Any]]) -> Dict[str, Any]:
    current_datasets: Dict[str, Any] = {}
    for result in source_results:
        dataset_key = str(result.get("dataset_key") or result.get("tool_name") or "source")
        rows = result.get("data") if isinstance(result.get("data"), list) else []
        first = rows[0] if rows and isinstance(rows[0], dict) else {}
        current_datasets[dataset_key] = {
            "label": result.get("dataset_label", dataset_key),
            "tool_name": result.get("tool_name", ""),
            "summary": result.get("summary", ""),
            "row_count": len(rows),
            "columns": list(first.keys()),
            "data": deepcopy(rows),
        }
    return current_datasets


def _build_source_snapshots(source_results: list[Dict[str, Any]], jobs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    snapshots: list[Dict[str, Any]] = []
    for result, job in zip(source_results, jobs):
        rows = result.get("data") if isinstance(result.get("data"), list) else []
        first = rows[0] if rows and isinstance(rows[0], dict) else {}
        snapshots.append(
            {
                "dataset_key": result.get("dataset_key", job.get("dataset_key")),
                "dataset_label": result.get("dataset_label", job.get("dataset_key")),
                "tool_name": result.get("tool_name", ""),
                "summary": result.get("summary", ""),
                "row_count": len(rows),
                "columns": list(first.keys()),
                "required_params": deepcopy(job.get("params", {})),
                "data": deepcopy(rows),
            }
        )
    return snapshots


def _unsupported_tool_result(job: Dict[str, Any], index: int, dataset_key: str, tool_name: str) -> Dict[str, Any]:
    params = job.get("params") if isinstance(job.get("params"), dict) else {}
    return {
        "success": False,
        "tool_name": tool_name or f"get_{dataset_key}_data",
        "dataset_key": dataset_key,
        "dataset_label": job.get("dataset_label", dataset_key),
        "data": [],
        "summary": "",
        "error_message": f"Unsupported dummy retrieval tool: {tool_name or dataset_key}",
        "applied_params": deepcopy(params),
        "post_filters": deepcopy(job.get("post_filters", {})),
        "filter_expressions": deepcopy(job.get("filter_expressions", [])),
        "source_tag": f"source_{index}",
        "from_dummy": True,
    }


def retrieve_dummy_data(
    retrieval_plan_payload: Any,
    domain_payload: Any,
    agent_state_payload: Any = None,
    row_limit_value: Any = None,
    main_context_payload: Any = None,
) -> Dict[str, Any]:
    payload = _payload_from_value(retrieval_plan_payload)
    main_context = _main_context_from_value(main_context_payload) or _main_context_from_value(payload)
    plan = payload.get("retrieval_plan") if isinstance(payload.get("retrieval_plan"), dict) else payload
    agent_state = _get_state(agent_state_payload) or payload.get("agent_state") or {}
    if not agent_state and isinstance(main_context.get("agent_state"), dict):
        agent_state = main_context["agent_state"]
    if domain_payload is None and main_context:
        domain_payload = main_context.get("domain_payload") or {"domain": main_context.get("domain", {})}
    domain = _get_domain(domain_payload)
    try:
        row_limit = max(1, int(row_limit_value or 200))
    except Exception:
        row_limit = 200

    if isinstance(payload.get("early_result"), dict) or plan.get("route") == "finish":
        return {
            "retrieval_result": {
                "route": "finish",
                "source_results": [],
                "early_result": payload.get("early_result"),
                "retrieval_plan": plan,
            },
            "retrieval_plan": plan,
            "intent": payload.get("intent", {}),
            "agent_state": agent_state,
            "main_context": main_context,
        }

    if plan.get("route") == "followup_transform":
        current_data = agent_state.get("current_data")
        source_results = [_source_result_from_current_data(current_data)] if isinstance(current_data, dict) else []
        return {
            "retrieval_result": {
                "route": "followup_transform",
                "source_results": source_results,
                "current_datasets": _build_current_datasets(source_results),
                "source_snapshots": current_data.get("source_snapshots", []) if isinstance(current_data, dict) else [],
                "retrieval_plan": plan,
                "used_dummy_data": False,
            },
            "retrieval_plan": plan,
            "intent": payload.get("intent", {}),
            "agent_state": agent_state,
            "main_context": main_context,
        }

    jobs = payload.get("retrieval_jobs") if isinstance(payload.get("retrieval_jobs"), list) else plan.get("jobs", [])
    source_results: list[Dict[str, Any]] = []
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            continue
        dataset_key = str(job.get("dataset_key") or f"dataset_{index}")
        tool_name = str(job.get("tool_name") or dataset_key).strip()
        params = job.get("params") if isinstance(job.get("params"), dict) else {}
        tool = DUMMY_TOOL_REGISTRY.get(tool_name) or DUMMY_TOOL_REGISTRY.get(dataset_key)
        result = tool(params, domain, row_limit) if tool else _unsupported_tool_result(job, index, dataset_key, tool_name)
        result["dataset_key"] = dataset_key
        result["dataset_label"] = job.get("dataset_label", dataset_key)
        result["post_filters"] = deepcopy(job.get("post_filters", {}))
        result["filter_expressions"] = deepcopy(job.get("filter_expressions", []))
        result["source_tag"] = f"source_{index}"
        source_results.append(result)

    return {
        "retrieval_result": {
            "route": plan.get("route", "single_retrieval"),
            "source_results": source_results,
            "current_datasets": _build_current_datasets(source_results),
            "source_snapshots": _build_source_snapshots(source_results, jobs),
            "retrieval_plan": plan,
            "used_dummy_data": True,
        },
        "retrieval_plan": plan,
        "intent": payload.get("intent", {}),
        "agent_state": agent_state,
        "main_context": main_context,
    }


class DummyDataRetriever(Component):
    display_name = "Dummy Data Retriever"
    description = "Create deterministic dummy source data by running dataset-specific retrieval tool functions."
    icon = "TestTube"
    name = "DummyDataRetriever"

    inputs = [
        DataInput(name="retrieval_plan", display_name="Retrieval Plan", info="Output from Retrieval Plan Builder.", input_types=["Data", "JSON"]),
        DataInput(name="main_context", display_name="Main Context", info="Optional direct output from Main Flow Context Builder. Usually propagated by Retrieval Plan.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Legacy direct domain input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="agent_state", display_name="Agent State", info="Legacy direct state input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        MessageTextInput(name="row_limit", display_name="Row Limit", info="Optional numeric row limit. Default is 200.", value="200", advanced=True),
    ]

    outputs = [
        Output(name="retrieval_result", display_name="Retrieval Result", method="build_retrieval_result", types=["Data"]),
    ]

    def build_retrieval_result(self) -> Data:
        payload = retrieve_dummy_data(
            getattr(self, "retrieval_plan", None),
            getattr(self, "domain_payload", None),
            getattr(self, "agent_state", None),
            getattr(self, "row_limit", None),
            getattr(self, "main_context", None),
        )
        result = payload.get("retrieval_result", {})
        self.status = {
            "route": result.get("route", ""),
            "source_count": len(result.get("source_results", [])) if isinstance(result.get("source_results"), list) else 0,
            "used_dummy_data": result.get("used_dummy_data", False),
        }
        return _make_data(payload)
