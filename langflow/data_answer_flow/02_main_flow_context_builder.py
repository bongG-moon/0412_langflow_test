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
        "domain_errors": ["Domain payload was empty."],
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
    return domain_payload


def build_main_context(
    user_question_value: Any,
    agent_state_payload: Any,
    domain_payload_value: Any,
    reference_date_value: Any = "",
) -> Dict[str, Any]:
    agent_state = _get_state(agent_state_payload)
    domain_payload = _normalize_domain_payload(domain_payload_value)
    user_question = _extract_text(user_question_value) or str(agent_state.get("pending_user_question") or "").strip()
    reference_date = str(reference_date_value or "").strip()
    main_context = {
        "user_question": user_question,
        "reference_date": reference_date,
        "agent_state": agent_state,
        "domain_payload": domain_payload,
        "domain": domain_payload.get("domain", {}),
        "domain_index": domain_payload.get("domain_index", {}),
        "domain_errors": domain_payload.get("domain_errors", []),
        "mongo_domain_load_status": domain_payload.get("mongo_domain_load_status", {}),
    }
    return {
        "main_context": main_context,
        "user_question": user_question,
        "agent_state": agent_state,
        "domain_payload": domain_payload,
        "domain": main_context["domain"],
        "domain_index": main_context["domain_index"],
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
        )
        domain = payload.get("domain", {}) if isinstance(payload.get("domain"), dict) else {}
        agent_state = payload.get("agent_state", {}) if isinstance(payload.get("agent_state"), dict) else {}
        self.status = {
            "question_chars": len(str(payload.get("user_question", ""))),
            "dataset_count": len(domain.get("datasets", {})) if isinstance(domain.get("datasets"), dict) else 0,
            "turn_id": agent_state.get("turn_id"),
        }
        return _make_data(payload)
