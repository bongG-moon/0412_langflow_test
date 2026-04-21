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
    {"MODE": "DDR5", "DEN": "512G", "TECH": "TSV", "MCP_NO": "HBM-A100", "PKG_TYPE1": "BGA", "PKG_TYPE2": "HBM"},
    {"MODE": "DDR5", "DEN": "256G", "TECH": "TSV", "MCP_NO": "HBM-B200", "PKG_TYPE1": "BGA", "PKG_TYPE2": "HBM"},
    {"MODE": "LPDDR5", "DEN": "128G", "TECH": "FC", "MCP_NO": "MOBILE-C300", "PKG_TYPE1": "FBGA", "PKG_TYPE2": "MOBILE"},
    {"MODE": "AUTO", "DEN": "64G", "TECH": "WB", "MCP_NO": "AUTO-D400", "PKG_TYPE1": "QFP", "PKG_TYPE2": "AUTO"},
]
DEFAULT_DATASET_METRICS = {
    "production": {"production": "number"},
    "target": {"target": "number"},
    "defect": {"inspection_qty": "number", "defect_qty": "number", "defect_rate": "number"},
    "equipment": {"planned_hours": "number", "actual_hours": "number", "utilization_rate": "number"},
    "wip": {"wip_qty": "number", "avg_wait_minutes": "number"},
    "yield": {"tested_qty": "number", "pass_qty": "number", "yield_rate": "number"},
    "hold": {"hold_qty": "number", "hold_hours": "number"},
    "scrap": {"input_qty": "number", "scrap_qty": "number", "scrap_rate": "number"},
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


def _stable_seed(dataset_key: str, params: Dict[str, Any]) -> int:
    text = json.dumps({"dataset_key": dataset_key, "params": params}, ensure_ascii=False, sort_keys=True)
    return sum(ord(ch) for ch in text)


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


def _dataset_columns(dataset_key: str, dataset: Dict[str, Any]) -> list[Dict[str, Any]]:
    columns = [item for item in _as_list(dataset.get("columns")) if isinstance(item, dict) and item.get("name")]
    if columns:
        return columns
    base_columns = [
        {"name": "WORK_DT", "type": "date"},
        {"name": "OPER_NAME", "type": "string"},
        {"name": "MODE", "type": "string"},
        {"name": "DEN", "type": "string"},
        {"name": "TECH", "type": "string"},
        {"name": "MCP_NO", "type": "string"},
        {"name": "PKG_TYPE1", "type": "string"},
        {"name": "PKG_TYPE2", "type": "string"},
    ]
    metrics = DEFAULT_DATASET_METRICS.get(dataset_key, {"value": "number"})
    return [*base_columns, *[{"name": name, "type": typ} for name, typ in metrics.items()]]


def _value_for_column(column: Dict[str, Any], base_row: Dict[str, Any], rng: random.Random, dataset_key: str, row_index: int) -> Any:
    name = str(column.get("name") or "")
    col_type = str(column.get("type") or "string").lower()
    if name in base_row:
        return base_row[name]
    if name == "공정군":
        return str(base_row.get("OPER_NAME", "")).split("/", 1)[0]
    if name in {"production", "qty", "actual_qty"}:
        return int(rng.uniform(1800, 5200))
    if name == "target":
        return int(rng.uniform(2600, 5600))
    if name in {"defect_qty", "scrap_qty"}:
        return int(rng.uniform(10, 180))
    if name in {"inspection_qty", "tested_qty", "input_qty"}:
        return int(rng.uniform(3000, 8000))
    if name in {"pass_qty"}:
        return int(rng.uniform(2800, 7600))
    if name.endswith("_rate") or "rate" in name.lower() or name in {"가동률"}:
        return round(rng.uniform(80.0, 99.8), 2)
    if col_type in {"number", "numeric", "integer", "float"}:
        return round(rng.uniform(1, 5000), 2)
    if col_type in {"date", "datetime"}:
        return base_row.get("WORK_DT")
    if col_type == "boolean":
        return bool(row_index % 2)
    return f"{name}_{dataset_key}_{row_index}"


def _build_rows_for_job(job: Dict[str, Any], domain: Dict[str, Any], row_limit: int) -> list[Dict[str, Any]]:
    dataset_key = str(job.get("dataset_key") or "")
    params = job.get("params") if isinstance(job.get("params"), dict) else {}
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    dataset = datasets.get(dataset_key) if isinstance(datasets.get(dataset_key), dict) else {}
    columns = _dataset_columns(dataset_key, dataset)
    processes = _domain_processes(domain)
    products = _domain_products(domain)
    rng = random.Random(_stable_seed(dataset_key, params))
    work_dt = str(params.get("date") or params.get("WORK_DT") or "2026-04-21")
    rows: list[Dict[str, Any]] = []
    for row_index, process in enumerate(processes, start=1):
        for product in products:
            base_row = {
                "WORK_DT": work_dt,
                "OPER_NAME": process,
                "LINE": f"LINE-{(row_index % 3) + 1}",
                "라인": f"LINE-{(row_index % 3) + 1}",
                **product,
            }
            row = {
                str(column.get("name")): _value_for_column(column, base_row, rng, dataset_key, len(rows) + 1)
                for column in columns
            }
            rows.append(row)
            if len(rows) >= row_limit:
                return rows
    return rows


def _summary_for_rows(dataset_key: str, rows: list[Dict[str, Any]]) -> str:
    if not rows:
        return f"{dataset_key} 더미 데이터 0건"
    numeric_totals: list[str] = []
    for key, value in rows[0].items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total = sum(float(row.get(key) or 0) for row in rows if isinstance(row.get(key), (int, float)))
            numeric_totals.append(f"{key} 합계 {total:,.0f}")
    suffix = ", ".join(numeric_totals[:3])
    return f"{dataset_key} 더미 데이터 {len(rows)}건" + (f", {suffix}" if suffix else "")


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
        rows = _build_rows_for_job(job, domain, row_limit)
        source_results.append(
            {
                "success": True,
                "tool_name": f"dummy_{dataset_key}_data",
                "dataset_key": dataset_key,
                "dataset_label": job.get("dataset_label", dataset_key),
                "data": rows,
                "summary": _summary_for_rows(dataset_key, rows),
                "applied_params": deepcopy(job.get("params", {})),
                "post_filters": deepcopy(job.get("post_filters", {})),
                "filter_expressions": deepcopy(job.get("filter_expressions", [])),
                "source_tag": f"source_{index}",
                "from_dummy": True,
            }
        )

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
    description = "Create deterministic dummy source data for the retrieval jobs."
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
