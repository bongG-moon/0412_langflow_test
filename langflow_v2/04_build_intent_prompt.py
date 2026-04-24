from __future__ import annotations

import json
from copy import deepcopy
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
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
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
        return deepcopy(value)
    data = getattr(value, "data", None)
    return deepcopy(data) if isinstance(data, dict) else {}


def _unwrap_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("state") if isinstance(payload.get("state"), dict) else {}


def _unwrap_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("domain_payload"), dict):
        payload = payload["domain_payload"]
    return payload.get("domain") if isinstance(payload.get("domain"), dict) else {}


def _unwrap_catalog(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("table_catalog_payload"), dict):
        payload = payload["table_catalog_payload"]
    return payload.get("table_catalog") if isinstance(payload.get("table_catalog"), dict) else payload


def build_intent_prompt(state_payload: Any, domain_payload: Any, table_catalog_payload: Any, reference_date: str = "") -> Dict[str, Any]:
    state = _unwrap_state(state_payload)
    question = str(_payload_from_value(state_payload).get("user_question") or state.get("pending_user_question") or "")
    domain = _unwrap_domain(domain_payload)
    table_catalog = _unwrap_catalog(table_catalog_payload)
    current = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    rows = current.get("data") if isinstance(current.get("data"), list) else []
    current_columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    prompt = f"""You are the intent planner for a manufacturing data-analysis Langflow.
Return JSON only.

Decide:
- query_mode: retrieval or followup_transform
- needed_datasets for retrieval
- required_params such as date as YYYYMMDD
- filters such as process_name, mode, product_name
- needs_pandas
- group_by, sort, top_n when requested

Rules:
- Use only dataset keys in the table catalog.
- Treat table catalog entries like tool descriptions. Do not create SQL.
- If a metric requires several datasets, include all of them.
- If the user asks to transform "that/current result", use followup_transform when current_data is available.
- If date or dataset scope changed, use retrieval.

Table catalog:
{json.dumps(datasets, ensure_ascii=False, default=str, indent=2)}

Domain/metric hints:
{json.dumps(domain, ensure_ascii=False, default=str, indent=2)}

Current state:
{json.dumps({
    "has_current_data": bool(rows),
    "current_columns": current_columns,
    "current_source_dataset_keys": current.get("source_dataset_keys", []),
    "last_intent": state.get("last_intent", {}),
    "last_retrieval_plan": state.get("last_retrieval_plan", {}),
}, ensure_ascii=False, default=str, indent=2)}

Reference date:
{reference_date or "(runtime Asia/Seoul today)"}

User question:
{question}

Return only:
{{
  "request_type": "data_question",
  "query_mode": "retrieval",
  "needed_datasets": ["production"],
  "required_params": {{"date": "YYYYMMDD"}},
  "filters": {{"process_name": ["D/A3"], "mode": ["DDR5"]}},
  "group_by": [],
  "sort": null,
  "top_n": null,
  "needs_pandas": true,
  "analysis_goal": "short goal",
  "reason": "short reason"
}}"""
    return {"prompt_payload": {"prompt_type": "intent", "prompt": prompt, "state": state, "domain": domain, "table_catalog": table_catalog, "user_question": question, "reference_date": reference_date}}


class BuildIntentPrompt(Component):
    display_name = "V2 Build Intent Prompt"
    description = "Build the intent-planning prompt from state, domain, and table catalog."
    icon = "FileText"
    name = "V2BuildIntentPrompt"

    inputs = [
        DataInput(name="state_payload", display_name="State Payload", input_types=["Data", "JSON"]),
        DataInput(name="domain_payload", display_name="Domain Payload", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="table_catalog_payload", display_name="Table Catalog Payload", input_types=["Data", "JSON"]),
        MessageTextInput(name="reference_date", display_name="Reference Date", value="", advanced=True),
    ]
    outputs = [Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt", types=["Data"])]

    def build_prompt(self):
        payload = build_intent_prompt(getattr(self, "state_payload", None), getattr(self, "domain_payload", None), getattr(self, "table_catalog_payload", None), getattr(self, "reference_date", ""))
        self.status = {"prompt_type": "intent", "chars": len(payload["prompt_payload"]["prompt"])}
        return _make_data(payload)
