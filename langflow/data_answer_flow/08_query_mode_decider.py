from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# The `_load_attr` function, `_Fallback*` classes, and `_make_input` helper below
# are compatibility scaffolding for standalone local tests or mixed Langflow
# versions. In the actual lfx-based Langflow environment, this block is not
# required and can be replaced with direct imports such as:
#   from lfx.custom import Component
#   from lfx.io import DataInput, Output
#   from lfx.schema import Data
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
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


# In the actual lfx Langflow runtime, these resolve to real Langflow classes.
# The fallback argument is only used outside Langflow or when import paths differ.
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
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        value = str(value or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _get_intent(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("intent"), dict):
        return payload["intent"]
    return payload


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload


def _get_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else payload


def _source_dataset_keys(agent_state: Dict[str, Any]) -> list[str]:
    snapshots = agent_state.get("source_snapshots")
    if isinstance(snapshots, dict) and snapshots:
        return list(snapshots.keys())
    current_data = agent_state.get("current_data")
    if isinstance(current_data, dict):
        return [str(item) for item in _as_list(current_data.get("source_dataset_keys"))]
    return []


def _snapshot_required_params(agent_state: Dict[str, Any], dataset_key: str) -> Dict[str, Any]:
    snapshots = agent_state.get("source_snapshots")
    if isinstance(snapshots, dict):
        snapshot = snapshots.get(dataset_key)
        if isinstance(snapshot, dict) and isinstance(snapshot.get("required_params"), dict):
            return snapshot["required_params"]
    context = agent_state.get("context")
    if isinstance(context, dict):
        last_required = context.get("last_required_params")
        if isinstance(last_required, dict) and isinstance(last_required.get(dataset_key), dict):
            return last_required[dataset_key]
    return {}


def _metric_required_datasets(intent: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
    datasets: list[str] = []
    for metric_key in _as_list(intent.get("metric_hints")):
        metric = domain.get("metrics", {}).get(str(metric_key), {})
        if isinstance(metric, dict):
            datasets.extend([str(item) for item in _as_list(metric.get("required_datasets"))])
    return datasets


def _needed_datasets(intent: Dict[str, Any], domain: Dict[str, Any], agent_state: Dict[str, Any]) -> list[str]:
    datasets = []
    datasets.extend([str(item) for item in _as_list(intent.get("required_datasets"))])
    datasets.extend([str(item) for item in _as_list(intent.get("dataset_hints"))])
    datasets.extend(_metric_required_datasets(intent, domain))
    datasets = _unique([item for item in datasets if item in domain.get("datasets", {})])
    if not datasets and intent.get("followup_cues"):
        datasets = _source_dataset_keys(agent_state)
    return datasets


def _has_post_processing_change(intent: Dict[str, Any]) -> bool:
    return bool(
        intent.get("filters")
        or intent.get("filter_expressions")
        or intent.get("group_by")
        or intent.get("sort")
        or intent.get("top_n")
        or intent.get("calculation_hints")
        or intent.get("followup_cues")
    )


def _explicit_fresh_request(intent: Dict[str, Any]) -> bool:
    summary = " ".join(
        [
            str(intent.get("query_summary") or ""),
            " ".join([str(item) for item in _as_list(intent.get("raw_terms"))]),
        ]
    )
    fresh_tokens = ("새로 조회", "다시 조회", "fresh retrieval", "reload")
    return any(token in summary.lower() for token in fresh_tokens)


def decide_query_mode(intent_value: Any, state_value: Any, domain_value: Any) -> Dict[str, Any]:
    intent_payload = _payload_from_value(intent_value)
    intent = _get_intent(intent_value)
    agent_state = _get_state(state_value)
    if not agent_state and isinstance(intent_payload.get("agent_state"), dict):
        agent_state = intent_payload["agent_state"]
    elif not agent_state and isinstance(intent_payload.get("state"), dict):
        agent_state = intent_payload["state"]
    domain = _get_domain(domain_value)
    snapshots = agent_state.get("source_snapshots") if isinstance(agent_state.get("source_snapshots"), dict) else {}
    current_data = agent_state.get("current_data")
    available_sources = _source_dataset_keys(agent_state)
    needed = _needed_datasets(intent, domain, agent_state)
    requested_params = intent.get("required_params") if isinstance(intent.get("required_params"), dict) else {}
    context = agent_state.get("context") if isinstance(agent_state.get("context"), dict) else {}
    reasons: list[str] = []
    changes: list[Dict[str, Any]] = []
    missing: list[Dict[str, str]] = []
    effective_required_params: Dict[str, Dict[str, Any]] = {}
    reuse_candidates: list[str] = []

    if intent.get("request_type") == "process_execution":
        return {
            "query_mode": "clarification",
            "reason": "Request was classified as process_execution; data query mode is not applicable in Phase 1.",
            "needed_datasets": needed,
            "reuse_candidates": [],
            "required_param_changes": [],
            "missing_required_params": [],
            "effective_required_params": {},
        }

    if _explicit_fresh_request(intent):
        reasons.append("User explicitly requested a fresh retrieval.")
        return {
            "query_mode": "retrieval",
            "reason": "; ".join(reasons),
            "needed_datasets": needed,
            "reuse_candidates": [],
            "required_param_changes": [],
            "missing_required_params": [],
            "effective_required_params": {},
        }

    if not snapshots and not current_data:
        reasons.append("No source snapshot or current data is available.")
        if not needed:
            reasons.append("No dataset has been identified yet; retrieval planning should decide the dataset.")
        return {
            "query_mode": "retrieval",
            "reason": "; ".join(reasons),
            "needed_datasets": needed,
            "reuse_candidates": [],
            "required_param_changes": [],
            "missing_required_params": [],
            "effective_required_params": {},
        }

    unavailable = [dataset for dataset in needed if dataset not in available_sources]
    if unavailable:
        reasons.append(f"Needed dataset(s) not available in current source snapshots: {', '.join(unavailable)}.")
        return {
            "query_mode": "retrieval",
            "reason": "; ".join(reasons),
            "needed_datasets": needed,
            "reuse_candidates": [dataset for dataset in needed if dataset in available_sources],
            "required_param_changes": [],
            "missing_required_params": [],
            "effective_required_params": {},
        }

    for dataset_key in needed or available_sources:
        dataset = domain.get("datasets", {}).get(dataset_key, {})
        required_names = [str(item) for item in _as_list(dataset.get("required_params"))] if isinstance(dataset, dict) else []
        previous_params = _snapshot_required_params(agent_state, dataset_key)
        effective_required_params[dataset_key] = {}
        for param_name in required_names:
            requested_has_param = param_name in requested_params and requested_params.get(param_name) not in (None, "")
            if requested_has_param:
                desired_value = requested_params.get(param_name)
            elif previous_params.get(param_name) not in (None, ""):
                desired_value = previous_params.get(param_name)
            else:
                last_required = context.get("last_required_params") if isinstance(context.get("last_required_params"), dict) else {}
                desired_value = (
                    last_required.get(dataset_key, {}).get(param_name)
                    if isinstance(last_required.get(dataset_key), dict)
                    else None
                )

            if desired_value in (None, ""):
                missing.append({"dataset_key": dataset_key, "param": param_name})
                continue

            effective_required_params[dataset_key][param_name] = desired_value
            previous_value = previous_params.get(param_name)
            if requested_has_param and previous_value not in (None, "") and str(previous_value) != str(desired_value):
                changes.append(
                    {
                        "dataset_key": dataset_key,
                        "param": param_name,
                        "previous": previous_value,
                        "current": desired_value,
                    }
                )

        if dataset_key in available_sources and not changes:
            reuse_candidates.append(dataset_key)

    if changes:
        reasons.append("At least one required retrieval parameter changed.")
        return {
            "query_mode": "retrieval",
            "reason": "; ".join(reasons),
            "needed_datasets": needed,
            "reuse_candidates": _unique(reuse_candidates),
            "required_param_changes": changes,
            "missing_required_params": missing,
            "effective_required_params": effective_required_params,
        }

    if missing and not reuse_candidates:
        reasons.append("Required retrieval parameter(s) are missing and no reusable source exists.")
        return {
            "query_mode": "clarification",
            "reason": "; ".join(reasons),
            "needed_datasets": needed,
            "reuse_candidates": [],
            "required_param_changes": [],
            "missing_required_params": missing,
            "effective_required_params": effective_required_params,
        }

    if _has_post_processing_change(intent):
        reasons.append("Required retrieval parameters are unchanged; only post-processing intent changed.")
        return {
            "query_mode": "followup_transform",
            "reason": "; ".join(reasons),
            "needed_datasets": needed or available_sources,
            "reuse_candidates": _unique(reuse_candidates or available_sources),
            "required_param_changes": [],
            "missing_required_params": missing,
            "effective_required_params": effective_required_params,
        }

    reasons.append("Reusable source data exists and no required retrieval parameter changed.")
    return {
        "query_mode": "followup_transform",
        "reason": "; ".join(reasons),
        "needed_datasets": needed or available_sources,
        "reuse_candidates": _unique(reuse_candidates or available_sources),
        "required_param_changes": [],
        "missing_required_params": missing,
        "effective_required_params": effective_required_params,
    }


class QueryModeDecider(Component):
    display_name = "Query Mode Decider"
    description = "Decide whether to retrieve new source data or transform reusable current data."
    icon = "Split"
    name = "QueryModeDecider"

    inputs = [
        DataInput(
            name="intent",
            display_name="Intent or Data Question Branch",
            info="Output from Normalize Intent With Domain or Data Question branch from Request Type Router.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="agent_state",
            display_name="Agent State",
            info="Output from Session State Loader. Optional when router branch payload already contains agent_state.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="domain_payload",
            display_name="Domain Payload",
            info="Domain Payload output from Domain JSON Loader.",
            input_types=["Data", "JSON"],
        ),
    ]

    outputs = [
        Output(name="query_mode_decision", display_name="Query Mode Decision", method="build_decision", types=["Data"]),
    ]

    def build_decision(self) -> Data:
        decision = decide_query_mode(
            getattr(self, "intent", None),
            getattr(self, "agent_state", None),
            getattr(self, "domain_payload", None) or getattr(self, "domain", None),
        )
        intent_payload = _payload_from_value(getattr(self, "intent", None))
        agent_state = _get_state(getattr(self, "agent_state", None))
        if not agent_state and isinstance(intent_payload.get("agent_state"), dict):
            agent_state = intent_payload["agent_state"]
        output = {
            "query_mode_decision": decision,
            "intent": _get_intent(getattr(self, "intent", None)),
            "agent_state": agent_state,
            **decision,
        }
        return _make_data(output)
