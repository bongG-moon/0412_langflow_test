from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


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


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any], text: str | None = None) -> Any:
    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload, text=text)


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


def _get_intent(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    intent = payload.get("intent")
    return intent if isinstance(intent, dict) else payload


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload


def route_request_type(intent_value: Any, state_value: Any) -> Dict[str, Any]:
    intent = _get_intent(intent_value)
    agent_state = _get_state(state_value)
    request_type = str(intent.get("request_type") or "unknown")
    try:
        confidence = float(intent.get("confidence") or 0.0)
    except Exception:
        confidence = 0.0

    if request_type == "process_execution":
        route = "process_execution"
        response = "This request was classified as a process execution request. Phase 1 only supports data questions."
    elif request_type == "data_question":
        route = "data_question"
        response = ""
    elif confidence < 0.25 and not (intent.get("dataset_hints") or intent.get("metric_hints")):
        route = "clarification"
        response = "I could not classify this request as a manufacturing data question. Please include the dataset, metric, date, or process you want to analyze."
    else:
        route = "data_question"
        response = ""

    return {
        "route": route,
        "request_type": request_type,
        "intent": intent,
        "agent_state": agent_state,
        "response": response,
    }


class RequestTypeRouter(Component):
    display_name = "Request Type Router"
    description = "Route normalized intent into data question, process execution, or clarification branches."
    icon = "GitBranch"
    name = "RequestTypeRouter"

    inputs = [
        DataInput(
            name="intent",
            display_name="Intent",
            info="Output from Normalize Intent With Domain.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="agent_state",
            display_name="Agent State",
            info="Output from Session State Loader.",
            input_types=["Data", "JSON"],
        ),
    ]

    outputs = [
        Output(name="route_result", display_name="Route Result", method="build_route", types=["Data"]),
        Output(name="data_question", display_name="Data Question", method="data_question_branch", group_outputs=True, types=["Data"]),
        Output(
            name="process_execution",
            display_name="Process Execution",
            method="process_execution_branch",
            group_outputs=True,
            types=["Data"],
        ),
        Output(name="clarification", display_name="Clarification", method="clarification_branch", group_outputs=True, types=["Data"]),
    ]

    def _payload(self) -> Dict[str, Any]:
        return route_request_type(getattr(self, "intent", None), getattr(self, "agent_state", None))

    def build_route(self) -> Data:
        payload = self._payload()
        return _make_data(payload, text=json.dumps(payload, ensure_ascii=False))

    def data_question_branch(self) -> Data:
        payload = self._payload()
        return _make_data(payload, text=json.dumps(payload, ensure_ascii=False)) if payload["route"] == "data_question" else None

    def process_execution_branch(self) -> Data:
        payload = self._payload()
        return (
            _make_data(payload, text=json.dumps(payload, ensure_ascii=False))
            if payload["route"] == "process_execution"
            else None
        )

    def clarification_branch(self) -> Data:
        payload = self._payload()
        return _make_data(payload, text=json.dumps(payload, ensure_ascii=False)) if payload["route"] == "clarification" else None
