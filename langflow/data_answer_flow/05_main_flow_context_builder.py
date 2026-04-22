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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
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
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return {"text": content}
    return {}


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("user_question", "question", "text", "content", "message"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return text.strip()
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content.strip()
    return str(value or "").strip()


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return deepcopy(state) if isinstance(state, dict) else deepcopy(payload)


def _empty_domain_payload() -> Dict[str, Any]:
    domain = {
        "products": {},
        "process_groups": {},
        "terms": {},
        "datasets": {},
        "metrics": {},
        "join_rules": [],
    }
    return {
        "domain_document": {
            "domain_id": "empty",
            "status": "empty",
            "metadata": {},
            "domain": domain,
        },
        "domain": domain,
        "domain_index": {},
        "domain_prompt_context": {},
        "domain_errors": ["Domain payload was empty."],
    }


def _empty_table_catalog_payload() -> Dict[str, Any]:
    return {
        "table_catalog": {"catalog_id": "empty", "datasets": {}},
        "table_catalog_prompt_context": {"datasets": {}},
        "table_catalog_errors": ["Table catalog payload was empty."],
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _short_item(value: Any, keys: tuple[str, ...]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    item: Dict[str, Any] = {}
    for key in keys:
        current = value.get(key)
        if current not in (None, "", [], {}):
            item[key] = deepcopy(current)
    return item


def _dataset_tool_name(dataset_key: str, dataset: Dict[str, Any]) -> str:
    tool = dataset.get("tool") if isinstance(dataset.get("tool"), dict) else {}
    return str(dataset.get("tool_name") or tool.get("name") or DEFAULT_TOOL_BY_DATASET.get(dataset_key) or f"get_{dataset_key}_data").strip()


def _build_domain_prompt_context(domain: Dict[str, Any], domain_index: Dict[str, Any]) -> Dict[str, Any]:
    datasets = {}
    for key, dataset in domain.get("datasets", {}).items():
        if not isinstance(dataset, dict):
            continue
        datasets[key] = {
            "display_name": dataset.get("display_name", key),
            "keywords": _as_list(dataset.get("keywords")),
            "required_params": _as_list(dataset.get("required_params")),
            "tool_name": _dataset_tool_name(key, dataset),
        }
    metrics = {}
    for key, metric in domain.get("metrics", {}).items():
        if isinstance(metric, dict):
            metrics[key] = _short_item(
                {**metric, "display_name": metric.get("display_name", key)},
                ("display_name", "aliases", "required_datasets", "formula", "description"),
            )
    return {
        "alias_index": domain_index,
        "datasets": datasets,
        "metrics": metrics,
        "products": {
            key: _short_item(value, ("display_name", "aliases"))
            for key, value in domain.get("products", {}).items()
            if isinstance(value, dict)
        },
        "process_groups": {
            key: _short_item(value, ("display_name", "aliases", "processes"))
            for key, value in domain.get("process_groups", {}).items()
            if isinstance(value, dict)
        },
        "terms": {
            key: _short_item(value, ("display_name", "aliases", "meaning", "description", "filter", "value"))
            for key, value in domain.get("terms", {}).items()
            if isinstance(value, dict)
        },
    }


def _normalize_domain_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if not payload:
        return _empty_domain_payload()
    if isinstance(payload.get("domain_payload"), dict):
        payload = payload["domain_payload"]
    domain = payload.get("domain")
    if not isinstance(domain, dict):
        domain = {
            key: payload.get(key)
            for key in ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
            if key in payload
        }
    if not isinstance(domain, dict):
        domain = {}
    domain_payload = deepcopy(payload)
    domain_payload["domain"] = domain
    domain_payload.setdefault("domain_index", {})
    domain_payload.setdefault("domain_errors", [])
    domain_payload.setdefault(
        "domain_document",
        {
            "domain_id": domain_payload.get("domain_id", "domain_payload"),
            "status": domain_payload.get("status", "active"),
            "metadata": domain_payload.get("metadata", {}),
            "domain": domain,
        },
    )
    if not isinstance(domain_payload.get("domain_prompt_context"), dict):
        domain_payload["domain_prompt_context"] = _build_domain_prompt_context(
            domain,
            domain_payload.get("domain_index", {}) if isinstance(domain_payload.get("domain_index"), dict) else {},
        )
    return domain_payload


def _normalize_table_catalog_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if not payload:
        return _empty_table_catalog_payload()
    if isinstance(payload.get("table_catalog_payload"), dict):
        payload = payload["table_catalog_payload"]
    table_catalog = payload.get("table_catalog")
    if not isinstance(table_catalog, dict):
        table_catalog = {
            "catalog_id": payload.get("catalog_id", "table_catalog_payload"),
            "datasets": payload.get("datasets") if isinstance(payload.get("datasets"), dict) else {},
        }
    table_catalog_payload = deepcopy(payload)
    table_catalog_payload["table_catalog"] = table_catalog
    table_catalog_payload.setdefault("table_catalog_prompt_context", {"datasets": {}})
    table_catalog_payload.setdefault("table_catalog_errors", [])
    return table_catalog_payload


def build_main_context(
    user_question_value: Any,
    agent_state_payload: Any,
    domain_payload_value: Any,
    reference_date_value: Any = "",
    table_catalog_payload_value: Any = None,
) -> Dict[str, Any]:
    agent_state = _get_state(agent_state_payload)
    domain_payload = _normalize_domain_payload(domain_payload_value)
    table_catalog_payload = _normalize_table_catalog_payload(table_catalog_payload_value)
    user_question = _extract_text(user_question_value) or str(agent_state.get("pending_user_question") or "").strip()
    reference_date = str(reference_date_value or "").strip()
    main_context = {
        "user_question": user_question,
        "reference_date": reference_date,
        "agent_state": agent_state,
        "domain_payload": domain_payload,
        "domain": domain_payload.get("domain", {}),
        "domain_index": domain_payload.get("domain_index", {}),
        "domain_prompt_context": domain_payload.get("domain_prompt_context", {}),
        "domain_errors": domain_payload.get("domain_errors", []),
        "mongo_domain_load_status": domain_payload.get("mongo_domain_load_status", {}),
        "table_catalog_payload": table_catalog_payload,
        "table_catalog": table_catalog_payload.get("table_catalog", {}),
        "table_catalog_prompt_context": table_catalog_payload.get("table_catalog_prompt_context", {}),
        "table_catalog_errors": table_catalog_payload.get("table_catalog_errors", []),
    }
    return {
        "main_context": main_context,
        "user_question": user_question,
        "agent_state": agent_state,
        "domain_payload": domain_payload,
        "domain": main_context["domain"],
        "domain_index": main_context["domain_index"],
        "domain_prompt_context": main_context["domain_prompt_context"],
        "table_catalog_payload": table_catalog_payload,
        "table_catalog": main_context["table_catalog"],
        "table_catalog_prompt_context": main_context["table_catalog_prompt_context"],
    }


class MainFlowContextBuilder(Component):
    display_name = "Main Flow Context Builder"
    description = "Bundle user question, session state, and MongoDB domain payload into one reusable main_context."
    icon = "Package"
    name = "MainFlowContextBuilder"

    inputs = [
        MessageTextInput(name="user_question", display_name="User Question", info="Current user question."),
        DataInput(
            name="agent_state",
            display_name="Agent State",
            info="Output from Session State Loader.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="domain_payload",
            display_name="Domain Payload",
            info="Output from MongoDB Domain Item Payload Loader, legacy MongoDB Domain Payload Loader, or Domain JSON Loader.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="table_catalog_payload",
            display_name="Table Catalog Payload",
            info="Output from Table Catalog Loader. Keeps table/query metadata separate from domain knowledge.",
            input_types=["Data", "JSON"],
        ),
        MessageTextInput(
            name="reference_date",
            display_name="Reference Date",
            value="",
            info="Optional YYYY-MM-DD date used for today/yesterday resolution.",
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="main_context", display_name="Main Context", method="build_context", types=["Data"]),
    ]

    def build_context(self) -> Data:
        payload = build_main_context(
            getattr(self, "user_question", ""),
            getattr(self, "agent_state", None),
            getattr(self, "domain_payload", None),
            getattr(self, "reference_date", ""),
            getattr(self, "table_catalog_payload", None),
        )
        domain = payload.get("domain", {}) if isinstance(payload.get("domain"), dict) else {}
        table_catalog = payload.get("table_catalog", {}) if isinstance(payload.get("table_catalog"), dict) else {}
        table_datasets = table_catalog.get("datasets", {}) if isinstance(table_catalog.get("datasets"), dict) else {}
        agent_state = payload.get("agent_state", {}) if isinstance(payload.get("agent_state"), dict) else {}
        self.status = {
            "question_chars": len(str(payload.get("user_question", ""))),
            "dataset_count": len(domain.get("datasets", {})) if isinstance(domain.get("datasets"), dict) else 0,
            "table_dataset_count": len(table_datasets),
            "turn_id": agent_state.get("turn_id"),
        }
        return _make_data(payload)
