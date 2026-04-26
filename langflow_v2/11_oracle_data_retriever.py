from __future__ import annotations

import ast
import json
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, MultilineInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


def _normalize_triple_quoted_json(text: str) -> str:
    import re

    def replace(match: re.Match[str]) -> str:
        return json.dumps(match.group(2))

    return re.sub(r'("""|\'\'\')(.*?)(\1)', replace, str(text or ""), flags=re.DOTALL)


def parse_jsonish(value: Any) -> tuple[Any, list[str]]:
    if value is None:
        return {}, []
    if isinstance(value, (dict, list)):
        return deepcopy(value), []
    text = str(value or "").strip()
    if not text:
        return {}, []
    errors: list[str] = []
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text), []
        except Exception as exc:
            errors.append(str(exc))
    normalized = _normalize_triple_quoted_json(text)
    if normalized != text:
        for parser in (json.loads, ast.literal_eval):
            try:
                return parser(normalized), []
            except Exception as exc:
                errors.append(str(exc))
    return {}, errors


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
        parsed, _errors = parse_jsonish(text)
        return parsed if isinstance(parsed, dict) else {"text": text}
    return {}


def _text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("text", "content", "db_config", "db_connections_json"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    return str(getattr(value, "text", "") or getattr(value, "content", "") or "").strip()


def _db_config_from_value(value: Any) -> tuple[Dict[str, Any], list[str]]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("db_config"), dict):
        return payload["db_config"], []
    if isinstance(payload.get("DB_CONFIG"), dict):
        return payload["DB_CONFIG"], []
    if payload and not any(key in payload for key in ("text", "content")):
        return payload, []
    parsed, errors = parse_jsonish(_text_from_value(value))
    return (parsed if isinstance(parsed, dict) else {}), errors


def _normalize_yyyymmdd(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return str(value or "").strip()


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


class DBConnector:
    def __init__(self, config: Dict[str, Any], oracle_module: Any | None = None):
        self.config = config
        self.oracle_module = oracle_module

    def _oracledb(self) -> Any:
        if self.oracle_module is not None:
            return self.oracle_module
        try:
            self.oracle_module = import_module("oracledb")
        except Exception as exc:
            raise RuntimeError(f"oracledb import failed: {exc}") from exc
        return self.oracle_module

    def get_connection(self, target_db: str) -> Any:
        if target_db not in self.config:
            raise ValueError(f"Unknown Target DB: {target_db}")
        db_conf = self.config[target_db]
        user = str(db_conf.get("user") or db_conf.get("username") or db_conf.get("id") or "").strip()
        password = str(db_conf.get("password") or db_conf.get("pw") or "").strip()
        dsn = str(db_conf.get("dsn") or db_conf.get("tns") or db_conf.get("tns_name") or db_conf.get("tns_alias") or "").strip()
        if not (user and password and dsn):
            raise ValueError(f"DB config for {target_db} must include user, password, and dsn.")
        try:
            return self._oracledb().connect(user=user, password=password, dsn=dsn)
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to {target_db}: {exc}") from exc

    def execute_query(self, target_db: str, sql: str, fetch_limit: int | None = None) -> list[Dict[str, Any]]:
        conn = None
        cursor = None
        try:
            conn = self.get_connection(target_db)
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchmany(fetch_limit) if fetch_limit else cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query_df(self, target_db: str, sql: str, fetch_limit: int | None = None) -> list[Dict[str, Any]]:
        pd = import_module("pandas")
        conn = None
        try:
            conn = self.get_connection(target_db)
            frame = pd.read_sql(sql, conn)
            if fetch_limit:
                frame = frame.head(fetch_limit)
            return frame.to_dict(orient="records")
        finally:
            if conn:
                conn.close()


def _oracle_result(tool_name: str, dataset_key: str, rows: list[Dict[str, Any]], params: Dict[str, Any], db_key: str) -> Dict[str, Any]:
    return {"success": True, "tool_name": tool_name, "dataset_key": dataset_key, "dataset_label": dataset_key, "data": rows, "summary": f"Oracle {dataset_key} query complete: {len(rows)} rows", "applied_params": deepcopy(params), "db_key": db_key, "from_oracle": True}


def _execute_oracle_sql(tool_name: str, dataset_key: str, db_key: str, sql: str, params: Dict[str, Any], connector: DBConnector, fetch_limit: int) -> Dict[str, Any]:
    rows = connector.execute_query(db_key, sql, fetch_limit=fetch_limit)
    return _oracle_result(tool_name, dataset_key, rows, params, db_key)


def get_production_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_MONTH, A.FACTORY, A.AA, A.BB, A.CC, A.production
          FROM AAA_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_production_data", "production", db_key, sql, params, connector, fetch_limit)


def get_target_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.FACTORY, A.MODE, A.DEN, A.TECH, A.TARGET_QTY AS target
          FROM TARGET_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_target_data", "target", db_key, sql, params, connector, fetch_limit)


def get_wip_status(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.OPER_NAME, A.MODE, A.DEN, A.TECH, A.WIP_QTY AS wip_qty
          FROM WIP_STATUS_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_wip_status", "wip", db_key, sql, params, connector, fetch_limit)


def get_equipment_status(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.OPER_NAME, A.EQUIPMENT_ID, A.UTILIZATION_RATE AS utilization_rate
          FROM EQUIPMENT_STATUS_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_equipment_status", "equipment", db_key, sql, params, connector, fetch_limit)


def get_defect_rate(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.OPER_NAME, A.INSPECTION_QTY AS inspection_qty,
               A.DEFECT_QTY AS defect_qty, A.DEFECT_RATE AS defect_rate
          FROM DEFECT_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_defect_rate", "defect", db_key, sql, params, connector, fetch_limit)


def get_yield_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.OPER_NAME, A.TESTED_QTY AS tested_qty,
               A.PASS_QTY AS pass_qty, A.YIELD_RATE AS yield_rate
          FROM YIELD_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_yield_data", "yield", db_key, sql, params, connector, fetch_limit)


def get_hold_lot_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.LOT_ID, A.OPER_NAME, A.HOLD_QTY AS hold_qty, A.HOLD_REASON AS hold_reason
          FROM HOLD_LOT_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_hold_lot_data", "hold", db_key, sql, params, connector, fetch_limit)


def get_scrap_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.OPER_NAME, A.INPUT_QTY AS input_qty,
               A.SCRAP_QTY AS scrap_qty, A.SCRAP_RATE AS scrap_rate
          FROM SCRAP_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_scrap_data", "scrap", db_key, sql, params, connector, fetch_limit)


def get_recipe_condition_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    date_text = _normalize_yyyymmdd(params["date"])
    sql = r"""
        SELECT A.WORK_DATE, A.OPER_NAME, A.RECIPE_ID, A.CONDITION_NAME, A.CONDITION_VALUE
          FROM RECIPE_CONDITION_TABLE A
         WHERE A.WORK_DATE >= {0}
           AND A.WORK_DATE <= {0}
    """.format(_sql_literal(date_text))
    return _execute_oracle_sql("get_recipe_condition_data", "recipe", db_key, sql, params, connector, fetch_limit)


def get_lot_trace_data(params: Dict[str, Any], connector: DBConnector, db_key: str = "PKG_RPT", fetch_limit: int = 5000) -> Dict[str, Any]:
    lot_id = str(params["lot_id"]).strip()
    sql = r"""
        SELECT A.LOT_ID, A.OPER_NAME, A.MOVE_IN_TIME, A.MOVE_OUT_TIME, A.CURRENT_STATUS
          FROM LOT_TRACE_TABLE A
         WHERE A.LOT_ID = {0}
    """.format(_sql_literal(lot_id))
    return _execute_oracle_sql("get_lot_trace_data", "lot_trace", db_key, sql, params, connector, fetch_limit)


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
        snapshots.append({"dataset_key": result.get("dataset_key", job.get("dataset_key", f"source_{index + 1}")), "dataset_label": result.get("dataset_label", job.get("dataset_label", "")), "tool_name": result.get("tool_name", job.get("tool_name", "")), "summary": result.get("summary", ""), "row_count": len(rows), "columns": _rows_columns(rows), "required_params": deepcopy(job.get("params", {})), "filters": deepcopy(job.get("filters", {})), "column_filters": deepcopy(job.get("column_filters", {})), "filter_plan": deepcopy(job.get("filter_plan", [])), "data": deepcopy(rows)})
    return snapshots


def _source_result_from_current_data(current_data: Dict[str, Any]) -> Dict[str, Any]:
    rows = [row for row in current_data.get("data", []) if isinstance(row, dict)] if isinstance(current_data.get("data"), list) else []
    dataset_keys = current_data.get("source_dataset_keys") if isinstance(current_data.get("source_dataset_keys"), list) else []
    return {"success": True, "tool_name": current_data.get("tool_name") or current_data.get("original_tool_name") or "current_data", "dataset_key": dataset_keys[0] if dataset_keys else current_data.get("dataset_key", "current_data"), "dataset_label": current_data.get("dataset_label", "Current Data"), "data": deepcopy(rows), "summary": current_data.get("summary", f"current data {len(rows)} rows reused"), "applied_params": deepcopy(current_data.get("source_required_params", current_data.get("retrieval_applied_params", {}))), "applied_filters": deepcopy(current_data.get("source_filters", {})), "applied_column_filters": deepcopy(current_data.get("source_column_filters", {})), "reused_current_data": True}


def _error_result(job: Dict[str, Any], message: str, failure_type: str = "retrieval_failed") -> Dict[str, Any]:
    dataset_key = str(job.get("dataset_key") or "unknown")
    return {"success": False, "tool_name": job.get("tool_name", dataset_key), "dataset_key": dataset_key, "dataset_label": job.get("dataset_label", dataset_key), "data": [], "summary": "", "error_message": message, "failure_type": failure_type, "applied_params": deepcopy(job.get("params", {}))}


def _missing_required_params(params: Dict[str, Any], required_params: list[Any]) -> list[str]:
    return [str(item) for item in required_params if str(item).strip() and params.get(str(item)) in (None, "", [])]


def _run_job(job: Dict[str, Any], connector: DBConnector, fetch_limit: int) -> Dict[str, Any]:
    tool_name = str(job.get("tool_name") or job.get("dataset_key") or "")
    tool = TOOL_REGISTRY.get(tool_name) or TOOL_REGISTRY.get(str(job.get("dataset_key") or ""))
    if tool is None:
        return _error_result(job, f"Unsupported oracle retrieval tool: {tool_name}", "unsupported_tool")
    params = deepcopy(job.get("params", {}))
    missing = _missing_required_params(params, job.get("required_params", []))
    if missing:
        return _error_result(job, f"Missing required parameter(s): {', '.join(missing)}", "missing_required_params")
    try:
        params.update({key: value for key, value in (job.get("filters") or {}).items() if value not in (None, "", [])})
        params.update({key: value for key, value in (job.get("column_filters") or {}).items() if value not in (None, "", [])})
        result = tool(params, connector=connector, db_key=str(job.get("db_key") or "PKG_RPT"), fetch_limit=fetch_limit)
        result["dataset_key"] = job.get("dataset_key", result.get("dataset_key"))
        result["dataset_label"] = job.get("dataset_label", result.get("dataset_label", result.get("dataset_key")))
        result["applied_filters"] = deepcopy(job.get("filters", {}))
        result["applied_column_filters"] = deepcopy(job.get("column_filters", {}))
        result["filter_plan"] = deepcopy(job.get("filter_plan", []))
        return result
    except Exception as exc:
        return _error_result(job, f"Oracle query failed for {job.get('dataset_key')}: {exc}", "retrieval_failed")


def retrieve_oracle_data(intent_plan_value: Any, db_config_value: Any = None, fetch_limit_value: Any = "5000") -> Dict[str, Any]:
    payload = _payload_from_value(intent_plan_value)
    plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    if payload.get("skipped"):
        return {"retrieval_payload": {"skipped": True, "skip_reason": payload.get("skip_reason", "route skipped"), "route": payload.get("branch", plan.get("route", "")) if isinstance(plan, dict) else payload.get("branch", ""), "source_results": [], "intent_plan": plan, "state": state}, "intent_plan": plan, "state": state}

    if plan.get("route") == "finish" or plan.get("query_mode") == "finish":
        early_result = {"response": plan.get("response", ""), "tool_results": [], "current_data": state.get("current_data"), "extracted_params": plan.get("required_params", {}), "awaiting_analysis_choice": bool(state.get("current_data")), "failure_type": plan.get("failure_type", "early_finish")}
        return {"retrieval_payload": {"route": "finish", "early_result": early_result, "source_results": [], "intent_plan": plan, "state": state, "used_oracle_data": False}, "intent_plan": plan, "state": state}

    if plan.get("route") == "followup_transform":
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
        source_results = [_source_result_from_current_data(current_data)] if current_data else []
        return {"retrieval_payload": {"route": "followup_transform", "source_results": source_results, "current_datasets": _build_current_datasets(source_results), "source_snapshots": deepcopy(current_data.get("source_snapshots", [])) if isinstance(current_data, dict) else [], "intent_plan": plan, "state": state, "used_oracle_data": False}, "intent_plan": plan, "state": state}

    try:
        fetch_limit = max(1, int(fetch_limit_value or 5000))
    except Exception:
        fetch_limit = 5000

    jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
    config, config_errors = _db_config_from_value(db_config_value)
    if config_errors:
        source_results = [_error_result(job, "DB config parse failed: " + "; ".join(config_errors), "db_config_parse_failed") for job in jobs]
    elif not config:
        source_results = [_error_result(job, "DB config is empty. Provide strict JSON or JSON-ish text with triple-quoted dsn.", "missing_db_config") for job in jobs]
    else:
        connector = DBConnector(config=config)
        source_results = [_run_job(job, connector, fetch_limit) for job in jobs if isinstance(job, dict)]

    return {"retrieval_payload": {"route": plan.get("route", "single_retrieval"), "source_results": source_results, "current_datasets": _build_current_datasets(source_results), "source_snapshots": _build_source_snapshots(source_results, jobs), "intent_plan": plan, "state": state, "used_oracle_data": True}, "intent_plan": plan, "state": state}


class OracleDataRetriever(Component):
    display_name = "Oracle Data Retriever"
    description = "Standalone Oracle retriever. Executes every planned job with internal SQL tool functions."
    icon = "DatabaseZap"
    name = "OracleDataRetriever"

    inputs = [
        DataInput(name="intent_plan", display_name="Intent Plan", info="Output from Intent Route Router.single_retrieval or multi_retrieval.", input_types=["Data", "JSON"]),
        MultilineInput(name="db_config", display_name="DB Config JSON", value="{}", info='Strict JSON or JSON-ish text with triple-quoted dsn is accepted.'),
        MessageTextInput(name="fetch_limit", display_name="Fetch Limit", value="5000", advanced=True),
    ]

    outputs = [Output(name="retrieval_payload", display_name="Retrieval Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = retrieve_oracle_data(getattr(self, "intent_plan", None), getattr(self, "db_config", "{}"), getattr(self, "fetch_limit", "5000"))
        retrieval = payload.get("retrieval_payload", {})
        source_results = retrieval.get("source_results", []) if isinstance(retrieval.get("source_results"), list) else []
        self.status = {"route": retrieval.get("route"), "source_count": len(source_results), "success_count": sum(1 for item in source_results if isinstance(item, dict) and item.get("success"))}
        return _make_data(payload)

