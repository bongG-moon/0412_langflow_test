from __future__ import annotations

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


DEFAULT_TOOL_BY_DATASET = {
    "production": "get_production_data",
    "target": "get_target_data",
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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


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


def _get_intent(decision_payload: Dict[str, Any]) -> Dict[str, Any]:
    intent = decision_payload.get("intent")
    return deepcopy(intent) if isinstance(intent, dict) else {}


def _metric_required_datasets(intent: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
    datasets: list[str] = []
    metrics = domain.get("metrics") if isinstance(domain.get("metrics"), dict) else {}
    for metric_key in _as_list(intent.get("metric_hints")):
        metric = metrics.get(str(metric_key), {})
        if isinstance(metric, dict):
            datasets.extend(str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip())
    return datasets


def _catalog_datasets(table_catalog: Dict[str, Any]) -> Dict[str, Any]:
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    return datasets if isinstance(datasets, dict) else {}


def _domain_datasets(domain: Dict[str, Any]) -> Dict[str, Any]:
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    return datasets if isinstance(datasets, dict) else {}


def _resolve_dataset_keys(decision: Dict[str, Any], intent: Dict[str, Any], domain: Dict[str, Any], table_catalog: Dict[str, Any]) -> list[str]:
    candidates: list[Any] = []
    candidates.extend(_as_list(decision.get("needed_datasets")))
    candidates.extend(_as_list(intent.get("required_datasets")))
    candidates.extend(_as_list(intent.get("dataset_hints")))
    candidates.extend(_metric_required_datasets(intent, domain))

    available = _catalog_datasets(table_catalog) or _domain_datasets(domain)
    resolved = [item for item in _unique(candidates) if not available or item in available]
    if resolved:
        return resolved

    if intent.get("metric_hints") and available:
        return [next(iter(available.keys()))]
    return []


def _dataset_config(dataset_key: str, domain: Dict[str, Any], table_catalog: Dict[str, Any]) -> Dict[str, Any]:
    domain_dataset = _domain_datasets(domain).get(dataset_key)
    catalog_dataset = _catalog_datasets(table_catalog).get(dataset_key)
    config: Dict[str, Any] = {}
    if isinstance(domain_dataset, dict):
        config.update(deepcopy(domain_dataset))
    if isinstance(catalog_dataset, dict):
        config.update(deepcopy(catalog_dataset))
    return config


def _source_type_for_dataset(dataset: Dict[str, Any]) -> str:
    source = dataset.get("source") if isinstance(dataset.get("source"), dict) else {}
    return str(dataset.get("source_type") or source.get("type") or "auto").strip() or "auto"


def _required_params_for_dataset(dataset_key: str, dataset: Dict[str, Any], decision: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    requested = intent.get("required_params") if isinstance(intent.get("required_params"), dict) else {}
    effective_by_dataset = (
        decision.get("effective_required_params")
        if isinstance(decision.get("effective_required_params"), dict)
        else {}
    )
    effective = effective_by_dataset.get(dataset_key) if isinstance(effective_by_dataset.get(dataset_key), dict) else {}

    params: Dict[str, Any] = {}
    for param_name in _as_list(dataset.get("required_params")):
        name = str(param_name or "").strip()
        if not name:
            continue
        if requested.get(name) not in (None, "", []):
            params[name] = requested.get(name)
        elif effective.get(name) not in (None, "", []):
            params[name] = effective.get(name)
    return params


def _build_missing_param_response(missing_params: list[Dict[str, str]]) -> str:
    if not missing_params:
        return ""
    labels = [f"{item.get('dataset_key', '')}.{item.get('param', '')}" for item in missing_params]
    return "데이터 조회에 필요한 필수 조건이 부족합니다: " + ", ".join(labels)


def _tool_name_for_dataset(dataset_key: str, dataset: Dict[str, Any]) -> str:
    tool = dataset.get("tool") if isinstance(dataset.get("tool"), dict) else {}
    return str(
        dataset.get("tool_name")
        or tool.get("name")
        or DEFAULT_TOOL_BY_DATASET.get(dataset_key)
        or f"get_{dataset_key}_data"
    ).strip()


def _early_finish_payload(
    response: str,
    failure_type: str,
    query_mode: str,
    intent: Dict[str, Any],
    agent_state: Dict[str, Any],
    main_context: Dict[str, Any],
    dataset_keys: list[str] | None = None,
    jobs: list[Dict[str, Any]] | None = None,
    extra_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    plan = {
        "route": "finish",
        "query_mode": query_mode,
        "reason": response,
        "dataset_keys": dataset_keys or [],
        "jobs": jobs or [],
    }
    if extra_plan:
        plan.update(extra_plan)
    return {
        "retrieval_plan": plan,
        "retrieval_jobs": jobs or [],
        "retrieval_route": "finish",
        "early_result": {
            "response": response,
            "tool_results": [],
            "current_data": agent_state.get("current_data"),
            "extracted_params": intent.get("required_params", {}),
            "awaiting_analysis_choice": bool(agent_state.get("current_data")) if failure_type != "clarification" else False,
            "failure_type": failure_type,
        },
        "intent": intent,
        "agent_state": agent_state,
        "main_context": main_context,
    }


def build_retrieval_plan(
    query_mode_decision: Any,
    domain_payload: Any,
    agent_state_payload: Any = None,
    main_context_payload: Any = None,
    table_catalog_payload: Any = None,
) -> Dict[str, Any]:
    decision = _payload_from_value(query_mode_decision)
    if isinstance(decision.get("query_mode_decision"), dict):
        nested = deepcopy(decision["query_mode_decision"])
        nested.update({key: value for key, value in decision.items() if key not in nested})
        decision = nested

    main_context = _main_context_from_value(main_context_payload) or _main_context_from_value(decision)
    if domain_payload is None and main_context:
        domain_payload = main_context.get("domain_payload") or {"domain": main_context.get("domain", {})}
    domain = _get_domain(domain_payload)
    if table_catalog_payload is None and main_context:
        table_catalog_payload = main_context.get("table_catalog_payload") or {"table_catalog": main_context.get("table_catalog", {})}
    table_catalog = _get_table_catalog(table_catalog_payload)

    agent_state = _get_state(agent_state_payload) or _get_state(decision)
    if not agent_state and isinstance(main_context.get("agent_state"), dict):
        agent_state = main_context["agent_state"]

    intent = _get_intent(decision)
    query_mode = str(decision.get("query_mode") or decision.get("route") or "retrieval")
    user_question = str(agent_state.get("pending_user_question") or intent.get("query_summary") or "")

    if query_mode == "clarification":
        response = str(decision.get("reason") or "질문을 데이터 조회로 처리하기 위한 정보가 부족합니다.")
        return _early_finish_payload(response, "clarification", query_mode, intent, agent_state, main_context)

    if query_mode == "followup_transform":
        current_data = agent_state.get("current_data")
        has_current = isinstance(current_data, dict) and isinstance(current_data.get("data"), list)
        if not has_current:
            return _early_finish_payload(
                "현재 분석할 데이터가 없습니다. 먼저 데이터를 조회해 주세요.",
                "missing_current_data",
                query_mode,
                intent,
                agent_state,
                main_context,
            )
        return {
            "retrieval_plan": {
                "route": "followup_transform",
                "query_mode": query_mode,
                "reason": decision.get("reason", ""),
                "dataset_keys": decision.get("reuse_candidates", []),
                "jobs": [],
                "needs_post_processing": True,
            },
            "retrieval_jobs": [],
            "retrieval_route": "followup_transform",
            "intent": intent,
            "agent_state": agent_state,
            "main_context": main_context,
        }

    dataset_keys = _resolve_dataset_keys(decision, intent, domain, table_catalog)
    if not dataset_keys:
        response = "질문에 맞는 조회 대상 데이터를 찾지 못했습니다. 생산량, 목표량, 수율처럼 조회할 데이터를 조금 더 구체적으로 적어 주세요."
        return _early_finish_payload(response, "unknown_dataset", "retrieval", intent, agent_state, main_context)

    jobs: list[Dict[str, Any]] = []
    missing: list[Dict[str, str]] = []
    filters = intent.get("filters") if isinstance(intent.get("filters"), dict) else {}
    filter_expressions = _as_list(intent.get("filter_expressions"))

    for dataset_key in dataset_keys:
        dataset = _dataset_config(dataset_key, domain, table_catalog)
        params = _required_params_for_dataset(dataset_key, dataset, decision, intent)
        for param_name in _as_list(dataset.get("required_params")):
            name = str(param_name or "").strip()
            if name and params.get(name) in (None, "", []):
                missing.append({"dataset_key": dataset_key, "param": name})
        jobs.append(
            {
                "dataset_key": dataset_key,
                "dataset_label": dataset.get("display_name", dataset_key),
                "tool_name": _tool_name_for_dataset(dataset_key, dataset),
                "source_type": _source_type_for_dataset(dataset),
                "params": params,
                "post_filters": filters,
                "filter_expressions": filter_expressions,
                "result_label": None,
            }
        )

    if missing:
        response = _build_missing_param_response(missing)
        return _early_finish_payload(
            response,
            "missing_required_params",
            "retrieval",
            intent,
            agent_state,
            main_context,
            dataset_keys=dataset_keys,
            jobs=jobs,
            extra_plan={"missing_required_params": missing},
        )

    route = "multi_retrieval" if len(jobs) > 1 else "single_retrieval"
    return {
        "retrieval_plan": {
            "route": route,
            "query_mode": "retrieval",
            "reason": decision.get("reason", ""),
            "dataset_keys": dataset_keys,
            "jobs": jobs,
            "needs_post_processing": True,
            "analysis_goal": intent.get("query_summary", user_question),
            "metric_hints": intent.get("metric_hints", []),
            "group_by": intent.get("group_by", []),
            "sort": intent.get("sort"),
            "top_n": intent.get("top_n"),
        },
        "retrieval_jobs": jobs,
        "retrieval_route": route,
        "intent": intent,
        "agent_state": agent_state,
        "main_context": main_context,
    }


class RetrievalPlanBuilder(Component):
    display_name = "Retrieval Plan Builder"
    description = "Build dataset tool jobs from query mode, normalized intent, and domain payload."
    icon = "ListChecks"
    name = "RetrievalPlanBuilder"

    inputs = [
        DataInput(
            name="query_mode_decision",
            display_name="Query Mode Decision",
            info="Output from Query Mode Decider.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="main_context",
            display_name="Main Context",
            info="Optional direct output from Main Flow Context Builder. Usually propagated by Query Mode Decider.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
        DataInput(
            name="domain_payload",
            display_name="Domain Payload",
            info="Legacy direct domain input. Prefer propagated Main Context.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
        DataInput(
            name="agent_state",
            display_name="Agent State",
            info="Legacy direct state input. Prefer propagated Main Context.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
        DataInput(
            name="table_catalog_payload",
            display_name="Table Catalog Payload",
            info="Output from Table Catalog Loader. Connect directly; table catalog is not propagated through Main Context.",
            input_types=["Data", "JSON"],
        ),
    ]

    outputs = [
        Output(name="retrieval_plan", display_name="Retrieval Plan", method="build_plan", types=["Data"]),
    ]

    def build_plan(self) -> Data:
        payload = build_retrieval_plan(
            getattr(self, "query_mode_decision", None),
            getattr(self, "domain_payload", None),
            getattr(self, "agent_state", None),
            getattr(self, "main_context", None),
            getattr(self, "table_catalog_payload", None),
        )
        route = payload.get("retrieval_route", "")
        jobs = payload.get("retrieval_jobs", [])
        self.status = {"route": route, "job_count": len(jobs) if isinstance(jobs, list) else 0}
        return _make_data(payload)
