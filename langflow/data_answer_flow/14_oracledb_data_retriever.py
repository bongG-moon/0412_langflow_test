from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
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


# SQL is intentionally written inside each get_* tool function below. This map
# is only for resolving dataset_key -> callable name in routing/error payloads.
TOOL_NAME_BY_DATASET = {
    "production": "get_production_data",
    "target": "get_target_data",
    "schedule": "get_schedule_data",
    "capa": "get_capa_data",
    "defect": "get_defect_rate",
    "equipment": "get_equipment_status",
    "wip": "get_wip_status",
    "yield": "get_yield_data",
    "hold": "get_hold_lot_data",
    "scrap": "get_scrap_data",
    "recipe": "get_recipe_condition_data",
    "lot_trace": "get_lot_trace_data",
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
    payload = _payload_from_value(value)
    direct = payload.get("db_connections") or payload.get("db_config") or payload.get("DB_CONFIG")
    if isinstance(direct, dict):
        return direct, []
    if payload and not any(isinstance(payload.get(key), str) for key in ("text", "json", "db_connections_json")):
        return payload, []

    text = _extract_text(value)
    if not text:
        return {}, ["db_connections_json is empty."]
    try:
        parsed = json.loads(text)
    except Exception as exc:
        normalized_text = _normalize_triple_quoted_json(text)
        if normalized_text != text:
            try:
                parsed = json.loads(normalized_text)
            except Exception:
                return {}, [f"DB connections JSON parse failed: {exc}"]
        else:
            return {}, [f"DB connections JSON parse failed: {exc}"]
    if not isinstance(parsed, dict):
        return {}, ["DB connections JSON root must be an object."]
    return parsed, []


def _normalize_triple_quoted_json(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        return json.dumps(match.group(1))

    normalized = re.sub(r'"""(.*?)"""', _replace, text, flags=re.DOTALL)
    normalized = re.sub(r"'''(.*?)'''", _replace, normalized, flags=re.DOTALL)
    return normalized


def _oracle_module() -> Any:
    try:
        module = import_module("oracledb")
    except Exception as exc:
        raise RuntimeError(f"oracledb import failed: {exc}") from exc
    return module


def _resolve_dsn(value: Dict[str, Any]) -> str:
    return str(value.get("dsn") or value.get("tns") or value.get("tns_name") or value.get("tns_alias") or value.get("tns_info") or "").strip()


def _safe_connection_info(connections: Dict[str, Any], db_key: str) -> Dict[str, Any]:
    info = connections.get(db_key)
    if not isinstance(info, dict) and db_key != "default":
        info = connections.get("default")
    return info if isinstance(info, dict) else {}


class DBConnector:
    def __init__(self, config: Dict[str, Any], oracle_module: Any | None = None):
        self.config = config
        self.oracle_module = oracle_module or _oracle_module()

    def get_connection(self, target_db: str) -> Any:
        info = _safe_connection_info(self.config, target_db)
        user = str(info.get("user") or info.get("username") or info.get("id") or "").strip()
        password = str(info.get("password") or info.get("pw") or "").strip()
        dsn = _resolve_dsn(info)
        if not (user and password and dsn):
            raise RuntimeError("Oracle connection info must include user/id, password/pw, and dsn/tns.")
        return self.oracle_module.connect(user=user, password=password, dsn=dsn)

    def execute_query(self, target_db: str, sql: str, fetch_limit: int = 5000) -> list[Dict[str, Any]]:
        connection = self.get_connection(target_db)
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            columns = [str(item[0]) for item in cursor.description or []]
            rows = cursor.fetchmany(fetch_limit) if fetch_limit else cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

    def execute_query_df(self, target_db: str, sql: str, fetch_limit: int = 5000) -> list[Dict[str, Any]]:
        pd = import_module("pandas")
        connection = self.get_connection(target_db)
        try:
            frame = pd.read_sql(sql, connection)
            if fetch_limit:
                frame = frame.head(fetch_limit)
            return frame.to_dict(orient="records")
        finally:
            try:
                connection.close()
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


def _is_missing_param(value: Any) -> bool:
    return value is None or value == "" or value == []


def _missing_param_names(params: Dict[str, Any], required_params: list[str]) -> list[str]:
    missing: list[str] = []
    for name in required_params:
        key = str(name or "").strip()
        if key and _is_missing_param(params.get(key)):
            missing.append(key)
    return missing


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _ordered_format_keys(format_params: Any, params: Dict[str, Any]) -> list[str]:
    if isinstance(format_params, (list, tuple)):
        return [str(item).strip() for item in format_params if str(item).strip()]
    if isinstance(format_params, dict) and format_params:
        items = list(format_params.items())
        if all(str(key).strip().isdigit() for key, _ in items):
            items = sorted(items, key=lambda item: int(str(item[0]).strip()))
        keys: list[str] = []
        for key, value in items:
            source_key = str(value or key).strip()
            if source_key:
                keys.append(source_key)
        return keys
    return [str(key).strip() for key in params.keys() if str(key).strip()]


def _normalize_yyyymmdd(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    text = str(value or "").strip()
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 8:
        return digits[:8]
    raise ValueError("expected YYYY-MM-DD or YYYYMMDD")


DATE_FORMAT_PARAMS = ("date",)
LOT_TRACE_FORMAT_PARAMS = ("lot_id",)
DATE_PARAM_TRANSFORMS = {"date": _normalize_yyyymmdd}


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (list, tuple, set)):
        return ", ".join(_sql_literal(item) for item in value)
    if isinstance(value, (datetime, date)):
        value = value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return "NULL"
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def _strip_leading_sql_comments(sql: str) -> str:
    text = str(sql or "")
    while True:
        before = text
        text = re.sub(r"^\s+", "", text)
        text = re.sub(r"^--[^\r\n]*(?:\r?\n|$)", "", text)
        text = re.sub(r"^/\*.*?\*/", "", text, flags=re.DOTALL)
        if text == before:
            return text


def _ensure_read_query(sql: str) -> None:
    text = _strip_leading_sql_comments(sql)
    match = re.match(r"([A-Za-z]+)\b", text)
    first_token = match.group(1).upper() if match else ""
    if first_token not in {"SELECT", "WITH"}:
        raise RuntimeError("Oracle query must start with SELECT or WITH.")


def _format_sql(sql: str, params: Dict[str, Any], format_params: Any, dataset_key: str) -> tuple[str, Dict[str, Any], list[str]]:
    _ensure_read_query(sql)
    keys = _ordered_format_keys(format_params, params)
    raw_values = {key: params.get(key) for key in keys}
    sql_literals = [_sql_literal(raw_values[key]) for key in keys]
    try:
        formatted_sql = sql.format(*sql_literals)
    except Exception as exc:
        raise RuntimeError(f"Oracle SQL format failed for dataset '{dataset_key}': {exc}") from exc
    _ensure_read_query(formatted_sql)
    return formatted_sql, raw_values, sql_literals


def _apply_param_transforms(params: Dict[str, Any], param_transforms: Any) -> tuple[Dict[str, Any], Dict[str, str]]:
    prepared = deepcopy(params)
    invalid: Dict[str, str] = {}
    transforms = param_transforms if isinstance(param_transforms, dict) else {}
    for key, transform in transforms.items():
        name = str(key or "").strip()
        if not name or _is_missing_param(prepared.get(name)):
            continue
        try:
            prepared[name] = transform(prepared[name])
        except Exception as exc:
            invalid[name] = str(exc)
    return prepared, invalid


def _execute_query_rows(db_connector: Any, db_key: str, sql: str, fetch_limit: int) -> list[Dict[str, Any]]:
    try:
        return db_connector.execute_query(db_key, sql, fetch_limit=fetch_limit)
    except TypeError as exc:
        try:
            rows = db_connector.execute_query(db_key, sql)
        except TypeError:
            raise exc
        return rows[:fetch_limit] if fetch_limit and isinstance(rows, list) else rows


def _failed_sql_dataset_result(
    tool_name: str,
    dataset_key: str,
    db_key: str,
    params: Dict[str, Any],
    message: str,
    failure_type: str,
    required_params: list[str] | None = None,
    missing_params: list[str] | None = None,
    invalid_params: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    result = {
        "success": False,
        "tool_name": tool_name,
        "dataset_key": dataset_key,
        "data": [],
        "summary": "",
        "error_message": message,
        "failure_type": failure_type,
        "applied_params": deepcopy(params),
        "db_key": db_key,
        "from_oracle": True,
    }
    if required_params is not None:
        result["required_params"] = deepcopy(required_params)
    if missing_params is not None:
        result["missing_params"] = deepcopy(missing_params)
    if invalid_params is not None:
        result["invalid_params"] = deepcopy(invalid_params)
    return result


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


def _execute_sql_dataset(
    tool_name: str,
    dataset_key: str,
    db_key: str,
    sql: str,
    db_connector: DBConnector,
    params: Dict[str, Any],
    fetch_limit: int,
    format_params: Any = None,
    required_params: Any = None,
    param_transforms: Any = None,
) -> Dict[str, Any]:
    sql = str(sql or "").strip()
    if not sql:
        raise RuntimeError(f"Oracle SQL is empty for dataset '{dataset_key}'.")
    format_keys = _ordered_format_keys(format_params, params)
    required_keys = _ordered_format_keys(required_params, params) if required_params is not None else format_keys
    required_keys = _unique_strings([*required_keys, *format_keys])
    missing_params = _missing_param_names(params, required_keys)
    if missing_params:
        required_label = ", ".join(required_keys)
        missing_label = ", ".join(missing_params)
        return _failed_sql_dataset_result(
            tool_name,
            dataset_key,
            db_key,
            params,
            f"Missing required parameter(s) for {dataset_key}: {missing_label}. Required: {required_label}.",
            "missing_required_params",
            required_params=required_keys,
            missing_params=missing_params,
        )

    prepared_params, invalid_params = _apply_param_transforms(params, param_transforms)
    if invalid_params:
        invalid_label = ", ".join(f"{key} ({message})" for key, message in invalid_params.items())
        return _failed_sql_dataset_result(
            tool_name,
            dataset_key,
            db_key,
            params,
            f"Invalid parameter value(s) for {dataset_key}: {invalid_label}.",
            "invalid_params",
            required_params=required_keys,
            invalid_params=invalid_params,
        )

    formatted_sql, format_values, sql_literals = _format_sql(sql, prepared_params, format_keys, dataset_key)
    rows = _execute_query_rows(db_connector, db_key, formatted_sql, fetch_limit)
    return {
        "success": True,
        "tool_name": tool_name,
        "dataset_key": dataset_key,
        "data": rows,
        "summary": f"Oracle {dataset_key} query complete: {len(rows)} rows",
        "applied_params": deepcopy(prepared_params),
        "required_params": deepcopy(required_keys),
        "format_params": deepcopy(format_values),
        "format_literals": deepcopy(sql_literals),
        "db_key": db_key,
        "from_oracle": True,
    }


def get_production_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "production"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               LINE, QTY AS production
          FROM PROD_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_production_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_target_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "target"
    sql = """
        SELECT WORK_DT, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               TARGET_QTY AS target
          FROM TARGET_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "PLAN")
    return _execute_sql_dataset("get_target_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_schedule_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "schedule"
    sql = """
        SELECT WORK_DT, SCHD_SEQ, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               LINE, PLAN_INPUT_QTY AS schedule_input_qty,
               PLAN_OUTPUT_QTY AS schedule_output_qty
          FROM SCHD_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "PLAN")
    return _execute_sql_dataset("get_schedule_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_capa_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "capa"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               CAPA_QTY AS capa_qty
          FROM CAPA_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "PLAN")
    return _execute_sql_dataset("get_capa_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_defect_rate(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "defect"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               INSPECTION_QTY AS inspection_qty,
               DEFECT_QTY AS defect_qty,
               DEFECT_RATE AS defect_rate
          FROM DEFECT_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "QMS")
    return _execute_sql_dataset("get_defect_rate", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_equipment_status(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "equipment"
    sql = """
        SELECT WORK_DT, OPER_NAME, EQUIPMENT_ID, LINE,
               PLANNED_HOURS AS planned_hours,
               ACTUAL_HOURS AS actual_hours,
               UTILIZATION_RATE AS utilization_rate
          FROM EQUIPMENT_STATUS_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_equipment_status", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_wip_status(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "wip"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               WIP_QTY AS wip_qty,
               AVG_WAIT_MINUTES AS avg_wait_minutes
          FROM WIP_STATUS_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_wip_status", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_yield_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "yield"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               TESTED_QTY AS tested_qty,
               PASS_QTY AS pass_qty,
               YIELD_RATE AS yield_rate
          FROM YIELD_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "QMS")
    return _execute_sql_dataset("get_yield_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_hold_lot_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "hold"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               HOLD_QTY AS hold_qty,
               HOLD_HOURS AS hold_hours
          FROM HOLD_LOT_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_hold_lot_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_scrap_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "scrap"
    sql = """
        SELECT WORK_DT, OPER_NAME, MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2,
               INPUT_QTY AS input_qty,
               SCRAP_QTY AS scrap_qty,
               SCRAP_RATE AS scrap_rate
          FROM SCRAP_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_scrap_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_recipe_condition_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "recipe"
    sql = """
        SELECT WORK_DT, OPER_NAME, RECIPE_ID, CONDITION_NAME, CONDITION_VALUE,
               LOWER_LIMIT, UPPER_LIMIT
          FROM RECIPE_CONDITION_TABLE
         WHERE WORK_DT = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_recipe_condition_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, DATE_FORMAT_PARAMS, DATE_FORMAT_PARAMS, DATE_PARAM_TRANSFORMS)


def get_lot_trace_data(db_connector: DBConnector, domain: Dict[str, Any], table_catalog: Dict[str, Any], params: Dict[str, Any], fetch_limit: int) -> Dict[str, Any]:
    dataset_key = "lot_trace"
    sql = """
        SELECT WORK_DT, LOT_ID, OPER_NAME, MOVE_IN_TIME, MOVE_OUT_TIME,
               MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2
          FROM LOT_TRACE_TABLE
         WHERE LOT_ID = {0}
    """
    db_key = _resolve_db_key(domain, table_catalog, dataset_key, "MES")
    return _execute_sql_dataset("get_lot_trace_data", dataset_key, db_key, sql, db_connector, params, fetch_limit, LOT_TRACE_FORMAT_PARAMS, LOT_TRACE_FORMAT_PARAMS)


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
    db_connector = None
    if not connection_errors:
        try:
            db_connector = DBConnector(connections, _oracle_module())
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
        if tool is None:
            source_results.append(_error_source_result(job, index, f"Unsupported oracle retrieval tool: {tool_name}"))
            continue
        params = job.get("params") if isinstance(job.get("params"), dict) else {}
        try:
            result = tool(db_connector, domain, table_catalog, params, fetch_limit)
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
    description = "Execute Oracle dataset retrieval tools with internal SQL and thin oracledb connection config."
    icon = "DatabaseZap"
    name = "OracleDBDataRetriever"

    inputs = [
        DataInput(name="retrieval_plan", display_name="Retrieval Plan", info="Output from Retrieval Plan Builder.", input_types=["Data", "JSON"]),
        DataInput(name="main_context", display_name="Main Context", info="Optional direct output from Main Flow Context Builder. Usually propagated by Retrieval Plan.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Legacy direct domain input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="table_catalog_payload", display_name="Table Catalog Payload", info="Output from Table Catalog Loader. Connect directly; table catalog is not propagated through Main Context.", input_types=["Data", "JSON"]),
        MultilineInput(
            name="db_connections_json",
            display_name="Oracle DB Connections JSON",
            info='Example: {"MES": {"id": "...", "pw": "...", "dsn": "host/service"}, "PLAN": {...}, "QMS": {...}, "default": {...}}',
            value="{}",
        ),
        DataInput(name="agent_state", display_name="Agent State", info="Legacy direct state input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        MessageTextInput(name="fetch_limit", display_name="Fetch Limit", value="5000", advanced=True),
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
