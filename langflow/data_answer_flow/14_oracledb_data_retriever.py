from __future__ import annotations

import json
import os
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
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


ORACLE_TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "get_production_data": {
        "dataset_key": "production",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   LINE, QTY AS production
              FROM PROD_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_target_data": {
        "dataset_key": "target",
        "db_key": "PLAN",
        "sql": """
            SELECT WORK_DT, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   TARGET_QTY AS target
              FROM TARGET_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_schedule_data": {
        "dataset_key": "schedule",
        "db_key": "PLAN",
        "sql": """
            SELECT WORK_DT, SCHD_SEQ, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   LINE, PLAN_INPUT_QTY AS schedule_input_qty,
                   PLAN_OUTPUT_QTY AS schedule_output_qty
              FROM SCHD_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_capa_data": {
        "dataset_key": "capa",
        "db_key": "PLAN",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   CAPA_QTY AS capa_qty
              FROM CAPA_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_defect_rate": {
        "dataset_key": "defect",
        "db_key": "QMS",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   INSPECTION_QTY AS inspection_qty,
                   DEFECT_QTY AS defect_qty,
                   DEFECT_RATE AS defect_rate
              FROM DEFECT_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_equipment_status": {
        "dataset_key": "equipment",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, OPER_NAME, EQUIPMENT_ID, LINE,
                   PLANNED_HOURS AS planned_hours,
                   ACTUAL_HOURS AS actual_hours,
                   UTILIZATION_RATE AS utilization_rate
              FROM EQUIPMENT_STATUS_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_wip_status": {
        "dataset_key": "wip",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   WIP_QTY AS wip_qty,
                   AVG_WAIT_MINUTES AS avg_wait_minutes
              FROM WIP_STATUS_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_yield_data": {
        "dataset_key": "yield",
        "db_key": "QMS",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   TESTED_QTY AS tested_qty,
                   PASS_QTY AS pass_qty,
                   YIELD_RATE AS yield_rate
              FROM YIELD_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_hold_lot_data": {
        "dataset_key": "hold",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   HOLD_QTY AS hold_qty,
                   HOLD_HOURS AS hold_hours
              FROM HOLD_LOT_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_scrap_data": {
        "dataset_key": "scrap",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
                   INPUT_QTY AS input_qty,
                   SCRAP_QTY AS scrap_qty,
                   SCRAP_RATE AS scrap_rate
              FROM SCRAP_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_recipe_condition_data": {
        "dataset_key": "recipe",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, OPER_NAME, RECIPE_ID, CONDITION_NAME, CONDITION_VALUE,
                   LOWER_LIMIT, UPPER_LIMIT
              FROM RECIPE_CONDITION_TABLE
             WHERE WORK_DT = :date
        """,
    },
    "get_lot_trace_data": {
        "dataset_key": "lot_trace",
        "db_key": "MES",
        "sql": """
            SELECT WORK_DT, LOT_ID, OPER_NAME, MOVE_IN_TIME, MOVE_OUT_TIME,
                   MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2
              FROM LOT_TRACE_TABLE
             WHERE LOT_ID = :lot_id
        """,
    },
}

TOOL_NAME_BY_DATASET = {
    str(spec["dataset_key"]): tool_name for tool_name, spec in ORACLE_TOOL_SPECS.items()
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


def _main_context_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    main_context = payload.get("main_context")
    return main_context if isinstance(main_context, dict) else {}


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("text", "json", "db_connections_json"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None)
    return str(text or "").strip()


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload


def _get_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else payload


def _get_table_catalog(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    table_catalog = payload.get("table_catalog")
    return table_catalog if isinstance(table_catalog, dict) else payload


def _parse_db_connections(value: Any) -> tuple[Dict[str, Any], list[str]]:
    text = _extract_text(value)
    if not text:
        return {}, ["db_connections_json is empty."]
    try:
        parsed = json.loads(text)
    except Exception as exc:
        return {}, [f"DB connections JSON parse failed: {exc}"]
    if not isinstance(parsed, dict):
        return {}, ["DB connections JSON root must be an object."]
    return parsed, []


def _oracle_module(client_lib_dir: str = "") -> Any:
    try:
        module = import_module("oracledb")
    except Exception as exc:
        raise RuntimeError(f"oracledb import failed: {exc}") from exc
    if client_lib_dir:
        try:
            module.init_oracle_client(lib_dir=client_lib_dir)
        except Exception:
            pass
    return module


def _resolve_tns(value: Dict[str, Any]) -> str:
    return str(
        value.get("tns")
        or value.get("tns_name")
        or value.get("tns_alias")
        or value.get("tns_info")
        or ""
    ).strip()


def _safe_connection_info(connections: Dict[str, Any], db_key: str) -> Dict[str, Any]:
    info = connections.get(db_key)
    if not isinstance(info, dict) and db_key != "default":
        info = connections.get("default")
    return info if isinstance(info, dict) else {}


def _connect(oracle_module: Any, info: Dict[str, Any], tns_admin: str = "") -> Any:
    user = str(info.get("user") or info.get("username") or info.get("id") or "").strip()
    password = str(info.get("password") or info.get("pw") or "").strip()
    tns = _resolve_tns(info)
    if not (user and password and tns):
        raise RuntimeError("Oracle connection info must include user/id, password/pw, and tns.")
    if tns_admin:
        os.environ["TNS_ADMIN"] = tns_admin
    return oracle_module.connect(user=user, password=password, dsn=tns)


def _fetch_rows(connection: Any, sql: str, binds: Dict[str, Any], fetch_limit: int) -> list[Dict[str, Any]]:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, binds)
        columns = [str(item[0]) for item in cursor.description or []]
        rows = cursor.fetchmany(fetch_limit)
        return [dict(zip(columns, row)) for row in rows]
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def _catalog_dataset(table_catalog: Dict[str, Any], dataset_key: str) -> Dict[str, Any]:
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    dataset = datasets.get(dataset_key)
    return dataset if isinstance(dataset, dict) else {}


def _domain_db_key(domain: Dict[str, Any], dataset_key: str, fallback_db_key: str) -> str:
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    dataset = datasets.get(dataset_key) if isinstance(datasets.get(dataset_key), dict) else {}
    oracle = dataset.get("oracle") if isinstance(dataset.get("oracle"), dict) else {}
    source = dataset.get("source") if isinstance(dataset.get("source"), dict) else {}
    return str(
        oracle.get("db_key")
        or source.get("db_key")
        or dataset.get("db_key")
        or fallback_db_key
        or "default"
    ).strip()


def _resolve_db_key(domain: Dict[str, Any], table_catalog: Dict[str, Any], dataset_key: str, fallback_db_key: str) -> str:
    dataset = _catalog_dataset(table_catalog, dataset_key)
    return str(dataset.get("db_key") or _domain_db_key(domain, dataset_key, fallback_db_key)).strip()


def _bind_values(params: Dict[str, Any], bind_params: Any) -> Dict[str, Any]:
    if not isinstance(bind_params, dict) or not bind_params:
        return deepcopy(params)
    binds: Dict[str, Any] = {}
    for bind_name, param_name in bind_params.items():
        bind_key = str(bind_name or "").strip()
        source_key = str(param_name or bind_key).strip()
        if bind_key:
            binds[bind_key] = params.get(source_key, params.get(bind_key))
    return binds


def _resolve_execution_spec(tool_name: str, dataset_key: str, table_catalog: Dict[str, Any]) -> Dict[str, Any] | None:
    catalog_dataset = _catalog_dataset(table_catalog, dataset_key)
    if catalog_dataset:
        return {
            "tool_name": str(catalog_dataset.get("tool_name") or tool_name or f"get_{dataset_key}_data").strip(),
            "dataset_key": dataset_key,
            "db_key": catalog_dataset.get("db_key") or "default",
            "sql": catalog_dataset.get("sql_template") or "",
            "bind_params": catalog_dataset.get("bind_params") if isinstance(catalog_dataset.get("bind_params"), dict) else {},
        }
    resolved_tool = tool_name or TOOL_NAME_BY_DATASET.get(dataset_key, "")
    spec = ORACLE_TOOL_SPECS.get(resolved_tool)
    if not spec:
        spec = ORACLE_TOOL_SPECS.get(TOOL_NAME_BY_DATASET.get(dataset_key, ""))
    if not isinstance(spec, dict):
        return None
    return {
        "tool_name": resolved_tool,
        "dataset_key": str(spec.get("dataset_key") or dataset_key),
        "db_key": spec.get("db_key") or "default",
        "sql": spec.get("sql") or "",
        "bind_params": {},
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


def _execute_oracle_dataset(
    tool_name: str,
    dataset_key: str,
    oracle_module: Any,
    connections: Dict[str, Any],
    domain: Dict[str, Any],
    table_catalog: Dict[str, Any],
    params: Dict[str, Any],
    fetch_limit: int,
    tns_admin: str,
) -> Dict[str, Any]:
    spec = _resolve_execution_spec(tool_name, dataset_key, table_catalog)
    if spec is None:
        raise RuntimeError(f"Unsupported oracle retrieval tool: {tool_name or dataset_key}")
    resolved_dataset_key = str(spec.get("dataset_key") or dataset_key)
    resolved_tool_name = str(spec.get("tool_name") or tool_name or f"get_{resolved_dataset_key}_data")
    db_key = _resolve_db_key(domain, table_catalog, resolved_dataset_key, str(spec.get("db_key") or "default"))
    sql = str(spec.get("sql") or "").strip()
    if not sql:
        raise RuntimeError(f"Oracle SQL is empty for dataset '{resolved_dataset_key}'.")
    binds = _bind_values(params, spec.get("bind_params"))
    info = _safe_connection_info(connections, db_key)
    connection = _connect(oracle_module, info, tns_admin)
    try:
        rows = _fetch_rows(connection, sql, binds, fetch_limit)
    finally:
        try:
            connection.close()
        except Exception:
            pass
    return {
        "success": True,
        "tool_name": resolved_tool_name,
        "dataset_key": resolved_dataset_key,
        "data": rows,
        "summary": f"Oracle {resolved_dataset_key} 조회 완료: {len(rows)}건",
        "applied_params": deepcopy(params),
        "bind_params": deepcopy(binds),
        "db_key": db_key,
        "from_oracle": True,
    }


def get_production_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_production_data", "production", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_target_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_target_data", "target", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_schedule_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_schedule_data", "schedule", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_capa_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_capa_data", "capa", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_defect_rate(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_defect_rate", "defect", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_equipment_status(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_equipment_status", "equipment", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_wip_status(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_wip_status", "wip", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_yield_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_yield_data", "yield", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_hold_lot_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_hold_lot_data", "hold", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_scrap_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_scrap_data", "scrap", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_recipe_condition_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_recipe_condition_data", "recipe", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


def get_lot_trace_data(oracle_module: Any, connections: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int, tns_admin: str) -> Dict[str, Any]:
    return _execute_oracle_dataset("get_lot_trace_data", "lot_trace", oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)


ORACLE_TOOL_REGISTRY = {
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


def _error_source_result(job: Dict[str, Any], index: int, message: str) -> Dict[str, Any]:
    dataset_key = str(job.get("dataset_key") or f"dataset_{index}")
    tool_name = str(job.get("tool_name") or TOOL_NAME_BY_DATASET.get(dataset_key) or dataset_key)
    params = job.get("params") if isinstance(job.get("params"), dict) else {}
    return {
        "success": False,
        "tool_name": tool_name,
        "dataset_key": dataset_key,
        "dataset_label": job.get("dataset_label", dataset_key),
        "data": [],
        "summary": "",
        "error_message": message,
        "applied_params": deepcopy(params),
        "post_filters": deepcopy(job.get("post_filters", {})),
        "filter_expressions": deepcopy(job.get("filter_expressions", [])),
        "source_tag": f"source_{index}",
    }


def retrieve_oracle_data(
    retrieval_plan_payload: Any,
    domain_payload: Any,
    db_connections_json: Any,
    agent_state_payload: Any = None,
    fetch_limit_value: Any = None,
    tns_admin: str = "",
    client_lib_dir: str = "",
    main_context_payload: Any = None,
    table_catalog_payload: Any = None,
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
    if table_catalog_payload is None and main_context:
        table_catalog_payload = main_context.get("table_catalog_payload") or {"table_catalog": main_context.get("table_catalog", {})}
    table_catalog = _get_table_catalog(table_catalog_payload)

    try:
        fetch_limit = max(1, int(fetch_limit_value or 5000))
    except Exception:
        fetch_limit = 5000

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
                "used_oracle_data": False,
            },
            "retrieval_plan": plan,
            "intent": payload.get("intent", {}),
            "agent_state": agent_state,
            "main_context": main_context,
        }

    jobs = payload.get("retrieval_jobs") if isinstance(payload.get("retrieval_jobs"), list) else plan.get("jobs", [])
    connections, connection_errors = _parse_db_connections(db_connections_json)
    errors: list[str] = list(connection_errors)
    oracle_module = None
    if not connection_errors:
        try:
            oracle_module = _oracle_module(client_lib_dir)
        except Exception as exc:
            errors.append(str(exc))

    source_results: list[Dict[str, Any]] = []
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            continue
        dataset_key = str(job.get("dataset_key") or f"dataset_{index}")
        tool_name = str(job.get("tool_name") or TOOL_NAME_BY_DATASET.get(dataset_key) or dataset_key).strip()
        tool = ORACLE_TOOL_REGISTRY.get(tool_name) or ORACLE_TOOL_REGISTRY.get(dataset_key)
        if errors:
            source_results.append(_error_source_result(job, index, "; ".join(errors)))
            continue
        if tool is None and _resolve_execution_spec(tool_name, dataset_key, table_catalog) is None:
            source_results.append(_error_source_result(job, index, f"Unsupported oracle retrieval tool: {tool_name}"))
            continue
        params = job.get("params") if isinstance(job.get("params"), dict) else {}
        try:
            if tool is not None:
                result = tool(oracle_module, connections, domain, table_catalog, params, fetch_limit, tns_admin)
            else:
                result = _execute_oracle_dataset(
                    tool_name,
                    dataset_key,
                    oracle_module,
                    connections,
                    domain,
                    table_catalog,
                    params,
                    fetch_limit,
                    tns_admin,
                )
            result["dataset_key"] = dataset_key
            result["dataset_label"] = job.get("dataset_label", dataset_key)
            result["post_filters"] = deepcopy(job.get("post_filters", {}))
            result["filter_expressions"] = deepcopy(job.get("filter_expressions", []))
            result["source_tag"] = f"source_{index}"
            source_results.append(result)
        except Exception as exc:
            source_results.append(_error_source_result(job, index, f"Oracle query failed for {dataset_key}: {exc}"))

    return {
        "retrieval_result": {
            "route": plan.get("route", "single_retrieval"),
            "source_results": source_results,
            "current_datasets": _build_current_datasets(source_results),
            "source_snapshots": _build_source_snapshots(source_results, jobs),
            "retrieval_plan": plan,
            "used_oracle_data": True,
        },
        "retrieval_plan": plan,
        "intent": payload.get("intent", {}),
        "agent_state": agent_state,
        "main_context": main_context,
    }


class OracleDBDataRetriever(Component):
    display_name = "OracleDB Data Retriever"
    description = "Execute dataset retrieval tools with oracledb using table catalog SQL and TNS connection info."
    icon = "DatabaseZap"
    name = "OracleDBDataRetriever"

    inputs = [
        DataInput(name="retrieval_plan", display_name="Retrieval Plan", info="Output from Retrieval Plan Builder.", input_types=["Data", "JSON"]),
        DataInput(name="main_context", display_name="Main Context", info="Optional direct output from Main Flow Context Builder. Usually propagated by Retrieval Plan.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Legacy direct domain input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="table_catalog_payload", display_name="Table Catalog Payload", info="Legacy direct table catalog input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        MultilineInput(
            name="db_connections_json",
            display_name="Oracle TNS Connections JSON",
            info='Example: {"MES": {"id": "...", "pw": "...", "tns": "MES_TNS_ALIAS"}, "PLAN": {...}, "QMS": {...}, "default": {...}}',
            value="{}",
        ),
        DataInput(name="agent_state", display_name="Agent State", info="Legacy direct state input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        MessageTextInput(name="fetch_limit", display_name="Fetch Limit", value="5000", advanced=True),
        MessageTextInput(name="tns_admin", display_name="TNS Admin", value="", advanced=True),
        MessageTextInput(name="client_lib_dir", display_name="Oracle Client Lib Dir", value="", advanced=True),
    ]

    outputs = [
        Output(name="retrieval_result", display_name="Retrieval Result", method="build_retrieval_result", types=["Data"]),
    ]

    def build_retrieval_result(self) -> Data:
        payload = retrieve_oracle_data(
            getattr(self, "retrieval_plan", None),
            getattr(self, "domain_payload", None),
            getattr(self, "db_connections_json", ""),
            getattr(self, "agent_state", None),
            getattr(self, "fetch_limit", "5000"),
            getattr(self, "tns_admin", ""),
            getattr(self, "client_lib_dir", ""),
            getattr(self, "main_context", None),
            getattr(self, "table_catalog_payload", None),
        )
        result = payload.get("retrieval_result", {})
        source_results = result.get("source_results", []) if isinstance(result.get("source_results"), list) else []
        self.status = {
            "route": result.get("route", ""),
            "source_count": len(source_results),
            "success_count": sum(1 for item in source_results if isinstance(item, dict) and item.get("success")),
        }
        return _make_data(payload)
