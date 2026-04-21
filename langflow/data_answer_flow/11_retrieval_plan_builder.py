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


def _get_intent(decision_payload: Dict[str, Any]) -> Dict[str, Any]:
    intent = decision_payload.get("intent")
    return deepcopy(intent) if isinstance(intent, dict) else {}


def _metric_required_datasets(intent: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
    datasets: list[str] = []
    metrics = domain.get("metrics") if isinstance(domain.get("metrics"), dict) else {}
    for metric_key in _as_list(intent.get("metric_hints")):
        metric = metrics.get(str(metric_key), {})
        if isinstance(metric, dict):
            datasets.extend(str(item) for item in _as_list(metric.get("required_datasets")))
    return datasets


def _resolve_dataset_keys(decision: Dict[str, Any], intent: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
    datasets = []
    datasets.extend(_as_list(decision.get("needed_datasets")))
    datasets.extend(_as_list(intent.get("required_datasets")))
    datasets.extend(_as_list(intent.get("dataset_hints")))
    datasets.extend(_metric_required_datasets(intent, domain))
    available = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    resolved = [item for item in _unique(datasets) if not available or item in available]
    if resolved:
        return resolved

    # Conservative fallback: if a metric was found but did not declare datasets,
    # keep the flow explainable by picking the first available dataset.
    if intent.get("metric_hints") and available:
        return [next(iter(available.keys()))]
    return []


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
    labels = []
    for item in missing_params:
        labels.append(f"{item.get('dataset_key', '')}.{item.get('param', '')}")
    return "조회에 필요한 필수 조건이 부족합니다: " + ", ".join(labels)


def build_retrieval_plan(
    query_mode_decision: Any,
    domain_payload: Any,
    agent_state_payload: Any = None,
    main_context_payload: Any = None,
) -> Dict[str, Any]:
    decision = _payload_from_value(query_mode_decision)
    main_context = _main_context_from_value(main_context_payload) or _main_context_from_value(decision)
    if domain_payload is None and main_context:
        domain_payload = main_context.get("domain_payload") or {"domain": main_context.get("domain", {})}
    domain = _get_domain(domain_payload)
    agent_state = _get_state(agent_state_payload) or _get_state(decision)
    if not agent_state and isinstance(main_context.get("agent_state"), dict):
        agent_state = main_context["agent_state"]
    intent = _get_intent(decision)
    query_mode = str(decision.get("query_mode") or decision.get("route") or "retrieval")
    user_question = str(agent_state.get("pending_user_question") or intent.get("query_summary") or "")
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}

    if query_mode == "clarification":
        response = str(decision.get("reason") or "질문을 데이터 조회로 처리하기 위한 정보가 부족합니다.")
        return {
            "retrieval_plan": {
                "route": "finish",
                "query_mode": query_mode,
                "reason": response,
                "dataset_keys": [],
                "jobs": [],
            },
            "retrieval_jobs": [],
            "retrieval_route": "finish",
            "early_result": {
                "response": response,
                "tool_results": [],
                "current_data": agent_state.get("current_data"),
                "extracted_params": intent.get("required_params", {}),
                "awaiting_analysis_choice": False,
                "failure_type": "clarification",
            },
            "intent": intent,
            "agent_state": agent_state,
            "main_context": main_context,
        }

    if query_mode == "followup_transform":
        current_data = agent_state.get("current_data")
        has_current = isinstance(current_data, dict) and isinstance(current_data.get("data"), list)
        if not has_current:
            return {
                "retrieval_plan": {
                    "route": "finish",
                    "query_mode": query_mode,
                    "reason": "Follow-up transform was requested but current_data is unavailable.",
                    "dataset_keys": [],
                    "jobs": [],
                },
                "retrieval_jobs": [],
                "retrieval_route": "finish",
                "early_result": {
                    "response": "현재 분석할 데이터가 없습니다. 먼저 데이터를 조회해 주세요.",
                    "tool_results": [],
                    "current_data": current_data,
                    "extracted_params": intent.get("required_params", {}),
                    "awaiting_analysis_choice": False,
                    "failure_type": "missing_current_data",
                },
                "intent": intent,
                "agent_state": agent_state,
                "main_context": main_context,
            }
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

    dataset_keys = _resolve_dataset_keys(decision, intent, domain)
    if not dataset_keys:
        response = "질문에 맞는 조회 대상 데이터를 찾지 못했습니다. 생산량, 목표량, 수율처럼 조회할 데이터를 조금 더 구체적으로 적어 주세요."
        return {
            "retrieval_plan": {
                "route": "finish",
                "query_mode": "retrieval",
                "reason": "No dataset keys were resolved.",
                "dataset_keys": [],
                "jobs": [],
            },
            "retrieval_jobs": [],
            "retrieval_route": "finish",
            "early_result": {
                "response": response,
                "tool_results": [],
                "current_data": agent_state.get("current_data"),
                "extracted_params": intent.get("required_params", {}),
                "awaiting_analysis_choice": bool(agent_state.get("current_data")),
                "failure_type": "unknown_dataset",
            },
            "intent": intent,
            "agent_state": agent_state,
            "main_context": main_context,
        }

    jobs: list[Dict[str, Any]] = []
    missing: list[Dict[str, str]] = []
    filters = intent.get("filters") if isinstance(intent.get("filters"), dict) else {}
    filter_expressions = _as_list(intent.get("filter_expressions"))

    for dataset_key in dataset_keys:
        dataset = datasets.get(dataset_key) if isinstance(datasets.get(dataset_key), dict) else {}
        params = _required_params_for_dataset(dataset_key, dataset, decision, intent)
        for param_name in _as_list(dataset.get("required_params")):
            name = str(param_name or "").strip()
            if name and params.get(name) in (None, "", []):
                missing.append({"dataset_key": dataset_key, "param": name})
        jobs.append(
            {
                "dataset_key": dataset_key,
                "dataset_label": dataset.get("display_name", dataset_key),
                "params": params,
                "post_filters": filters,
                "filter_expressions": filter_expressions,
                "query_template": dataset.get("query_template") or dataset.get("sql") or "",
                "db_key": dataset.get("db_key") or (dataset.get("oracle", {}) if isinstance(dataset.get("oracle"), dict) else {}).get("db_key") or "",
                "result_label": None,
            }
        )

    if missing:
        response = _build_missing_param_response(missing)
        return {
            "retrieval_plan": {
                "route": "finish",
                "query_mode": "retrieval",
                "reason": response,
                "dataset_keys": dataset_keys,
                "jobs": jobs,
                "missing_required_params": missing,
            },
            "retrieval_jobs": jobs,
            "retrieval_route": "finish",
            "early_result": {
                "response": response,
                "tool_results": [],
                "current_data": agent_state.get("current_data"),
                "extracted_params": intent.get("required_params", {}),
                "awaiting_analysis_choice": bool(agent_state.get("current_data")),
                "failure_type": "missing_required_params",
            },
            "intent": intent,
            "agent_state": agent_state,
            "main_context": main_context,
        }

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
    description = "Build retrieval jobs from query mode, normalized intent, and MongoDB domain payload."
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
        )
        route = payload.get("retrieval_route", "")
        jobs = payload.get("retrieval_jobs", [])
        self.status = {"route": route, "job_count": len(jobs) if isinstance(jobs, list) else 0}
        return _make_data(payload)
