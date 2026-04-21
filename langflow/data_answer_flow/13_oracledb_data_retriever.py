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


def _dataset_config(domain: Dict[str, Any], dataset_key: str) -> Dict[str, Any]:
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    dataset = datasets.get(dataset_key) if isinstance(datasets.get(dataset_key), dict) else {}
    oracle = dataset.get("oracle") if isinstance(dataset.get("oracle"), dict) else {}
    source = dataset.get("source") if isinstance(dataset.get("source"), dict) else {}
    return {"dataset": dataset, "oracle": oracle, "source": source}


def _resolve_db_key(config: Dict[str, Any], job: Dict[str, Any]) -> str:
    dataset = config.get("dataset", {})
    oracle = config.get("oracle", {})
    source = config.get("source", {})
    return str(
        job.get("db_key")
        or oracle.get("db_key")
        or source.get("db_key")
        or dataset.get("db_key")
        or "default"
    ).strip()


def _resolve_sql(config: Dict[str, Any], job: Dict[str, Any]) -> str:
    dataset = config.get("dataset", {})
    oracle = config.get("oracle", {})
    source = config.get("source", {})
    return str(
        job.get("query_template")
        or oracle.get("query_template")
        or oracle.get("sql")
        or source.get("query_template")
        or source.get("sql")
        or dataset.get("query_template")
        or dataset.get("sql")
        or ""
    ).strip()


def _safe_connection_info(connections: Dict[str, Any], db_key: str) -> Dict[str, Any]:
    info = connections.get(db_key)
    if not isinstance(info, dict) and db_key != "default":
        info = connections.get("default")
    return info if isinstance(info, dict) else {}


def _oracle_module(client_lib_dir: str = "") -> Any:
    try:
        module = import_module("oracledb")
    except Exception as exc:
        raise RuntimeError(f"oracledb import failed: {exc}") from exc
    if client_lib_dir:
        try:
            module.init_oracle_client(lib_dir=client_lib_dir)
        except Exception:
            # init_oracle_client can be called only once in a process. Ignore the
            # duplicate-init error and let connect decide whether the runtime is usable.
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


def _source_result_from_current_data(current_data: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(current_data)
    result.setdefault("success", True)
    result.setdefault("tool_name", result.get("original_tool_name") or result.get("tool_name") or "current_data")
    result.setdefault("dataset_key", (result.get("source_dataset_keys") or ["current_data"])[0] if isinstance(result.get("source_dataset_keys"), list) else "current_data")
    result.setdefault("dataset_label", result.get("dataset_key", "current_data"))
    result.setdefault("summary", f"현재 데이터 {len(result.get('data', [])) if isinstance(result.get('data'), list) else 0}건 재사용")
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


def retrieve_oracle_data(
    retrieval_plan_payload: Any,
    domain_payload: Any,
    db_connections_json: Any,
    agent_state_payload: Any = None,
    fetch_limit_value: Any = None,
    tns_admin: str = "",
    client_lib_dir: str = "",
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

    connections, connection_errors = _parse_db_connections(db_connections_json)
    jobs = payload.get("retrieval_jobs") if isinstance(payload.get("retrieval_jobs"), list) else plan.get("jobs", [])
    source_results: list[Dict[str, Any]] = []
    errors: list[str] = list(connection_errors)
    oracle_module = None
    if not connection_errors:
        try:
            oracle_module = _oracle_module(client_lib_dir)
        except Exception as exc:
            errors.append(str(exc))

    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            continue
        dataset_key = str(job.get("dataset_key") or f"dataset_{index}")
        config = _dataset_config(domain, dataset_key)
        db_key = _resolve_db_key(config, job)
        sql = _resolve_sql(config, job)
        params = job.get("params") if isinstance(job.get("params"), dict) else {}
        if errors:
            source_results.append(
                {
                    "success": False,
                    "tool_name": f"oracle_{dataset_key}_data",
                    "dataset_key": dataset_key,
                    "dataset_label": job.get("dataset_label", dataset_key),
                    "data": [],
                    "summary": "",
                    "error_message": "; ".join(errors),
                    "applied_params": deepcopy(params),
                    "source_tag": f"source_{index}",
                }
            )
            continue
        if not sql:
            source_results.append(
                {
                    "success": False,
                    "tool_name": f"oracle_{dataset_key}_data",
                    "dataset_key": dataset_key,
                    "dataset_label": job.get("dataset_label", dataset_key),
                    "data": [],
                    "summary": "",
                    "error_message": f"Dataset '{dataset_key}' has no query_template/sql.",
                    "applied_params": deepcopy(params),
                    "source_tag": f"source_{index}",
                }
            )
            continue
        try:
            info = _safe_connection_info(connections, db_key)
            connection = _connect(oracle_module, info, tns_admin)
            try:
                rows = _fetch_rows(connection, sql, params, fetch_limit)
            finally:
                try:
                    connection.close()
                except Exception:
                    pass
            source_results.append(
                {
                    "success": True,
                    "tool_name": f"oracle_{dataset_key}_data",
                    "dataset_key": dataset_key,
                    "dataset_label": job.get("dataset_label", dataset_key),
                    "data": rows,
                    "summary": f"Oracle {dataset_key} 조회 완료: {len(rows)}건",
                    "applied_params": deepcopy(params),
                    "post_filters": deepcopy(job.get("post_filters", {})),
                    "filter_expressions": deepcopy(job.get("filter_expressions", [])),
                    "source_tag": f"source_{index}",
                    "db_key": db_key,
                    "from_oracle": True,
                }
            )
        except Exception as exc:
            source_results.append(
                {
                    "success": False,
                    "tool_name": f"oracle_{dataset_key}_data",
                    "dataset_key": dataset_key,
                    "dataset_label": job.get("dataset_label", dataset_key),
                    "data": [],
                    "summary": "",
                    "error_message": f"Oracle query failed for {dataset_key}: {exc}",
                    "applied_params": deepcopy(params),
                    "source_tag": f"source_{index}",
                    "db_key": db_key,
                }
            )

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
    description = "Execute retrieval jobs with oracledb using dataset SQL and selected DB connection info."
    icon = "DatabaseZap"
    name = "OracleDBDataRetriever"

    inputs = [
        DataInput(name="retrieval_plan", display_name="Retrieval Plan", info="Output from Retrieval Plan Builder.", input_types=["Data", "JSON"]),
        DataInput(name="main_context", display_name="Main Context", info="Optional direct output from Main Flow Context Builder. Usually propagated by Retrieval Plan.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Legacy direct domain input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        MultilineInput(
            name="db_connections_json",
            display_name="Oracle TNS Connections JSON",
            info='Example: {"MES": {"id": "...", "pw": "...", "tns": "MES_TNS_ALIAS"}, "default": {...}}',
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
        )
        result = payload.get("retrieval_result", {})
        source_results = result.get("source_results", []) if isinstance(result.get("source_results"), list) else []
        self.status = {
            "route": result.get("route", ""),
            "source_count": len(source_results),
            "success_count": sum(1 for item in source_results if isinstance(item, dict) and item.get("success")),
        }
        return _make_data(payload)
