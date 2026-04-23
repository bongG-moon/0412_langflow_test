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
#   from lfx.io import DataInput, MessageTextInput, Output, PromptInput
#   from lfx.schema import Data, Message
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
    required: bool = False


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


class _FallbackMessage:
    def __init__(self, text: str | None = None, **kwargs: Any):
        self.text = text or str(kwargs.get("content") or "")
        self.content = self.text


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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
PromptInput = _load_attr(["lfx.io", "langflow.io"], "PromptInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)


DEFAULT_TEMPLATE = """You are a manufacturing data-analysis intent extractor.

Return ONLY one valid JSON object. Do not include markdown fences.

Task:
- Classify the user request as data_question, process_execution, or unknown.
- Extract dataset hints, metric hints, required query parameters, post-retrieval filters, grouping, sorting, top_n, calculations, and follow-up cues.
- Required query parameters are values needed before source data retrieval, such as date when the dataset requires date.
- Post-retrieval filters are values such as product, process, line, and domain term filters that can be applied with pandas after raw data retrieval.
- If the user is asking to run a named operational process or end-to-end workflow, use request_type=process_execution.
- If uncertain, use request_type=unknown and lower confidence.

Output JSON schema:
{schema}

User question:
{user_question}

Recent chat history:
{recent_history}

Previous context:
{context}

Current data summary:
{current_data}

Available manufacturing domain:
{domain_summary}
"""


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _make_message(text: str) -> Any:
    try:
        return Message(text=text)
    except TypeError:
        try:
            return Message(content=text)
        except TypeError:
            try:
                return Message(text)
            except Exception:
                return _FallbackMessage(text=text)


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


def _main_context_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    main_context = payload.get("main_context")
    return main_context if isinstance(main_context, dict) else {}


def _unwrap(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else payload


def _compact_dict(value: Any, limit: int = 4000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... truncated ..."


def _domain_summary(domain: Dict[str, Any], domain_index: Dict[str, Any]) -> Dict[str, Any]:
    datasets = {}
    for key, dataset in domain.get("datasets", {}).items():
        if not isinstance(dataset, dict):
            continue
        datasets[key] = {
            "display_name": dataset.get("display_name", key),
            "description": dataset.get("description", ""),
            "keywords": dataset.get("keywords", []),
            "required_params": dataset.get("required_params", []),
        }

    metrics = {}
    for key, metric in domain.get("metrics", {}).items():
        if not isinstance(metric, dict):
            continue
        metrics[key] = {
            "display_name": metric.get("display_name", key),
            "aliases": metric.get("aliases", []),
            "required_datasets": metric.get("required_datasets", []),
            "formula": metric.get("formula", ""),
        }

    return {
        "alias_index": domain_index,
        "datasets": datasets,
        "metrics": metrics,
        "products": domain.get("products", {}),
        "process_groups": domain.get("process_groups", {}),
        "terms": domain.get("terms", {}),
    }


def build_intent_prompt(
    user_question: str,
    agent_state_payload: Any,
    domain_payload: Any,
    template_value: Any = None,
    main_context_payload: Any = None,
) -> str:
    main_context = _main_context_from_value(main_context_payload)
    if main_context:
        user_question = str(user_question or main_context.get("user_question") or "")
        if agent_state_payload is None:
            agent_state_payload = {"agent_state": main_context.get("agent_state", {})}
        if domain_payload is None:
            domain_payload = main_context.get("domain_payload") or {
                "domain": main_context.get("domain", {}),
                "domain_index": main_context.get("domain_index", {}),
                "domain_errors": main_context.get("domain_errors", []),
            }

    state_payload = _payload_from_value(agent_state_payload)
    agent_state = state_payload.get("agent_state")
    if not isinstance(agent_state, dict):
        agent_state = _unwrap(state_payload, "state")

    domain_full_payload = _payload_from_value(domain_payload)
    domain = domain_full_payload.get("domain")
    if not isinstance(domain, dict):
        domain = domain_full_payload

    domain_index = domain_full_payload.get("domain_index")
    if not isinstance(domain_index, dict):
        domain_index = {}
    domain_prompt_context = {}
    if isinstance(main_context.get("domain_prompt_context"), dict):
        domain_prompt_context = main_context["domain_prompt_context"]
    elif isinstance(domain_full_payload.get("domain_prompt_context"), dict):
        domain_prompt_context = domain_full_payload["domain_prompt_context"]
    context = agent_state.get("context", {}) if isinstance(agent_state, dict) else {}
    chat_history = agent_state.get("chat_history", []) if isinstance(agent_state, dict) else []
    recent_history = chat_history[-6:] if isinstance(chat_history, list) else []
    current_data = agent_state.get("current_data") if isinstance(agent_state, dict) else None

    schema = {
        "request_type": "data_question | process_execution | unknown",
        "query_summary": "",
        "dataset_hints": [],
        "metric_hints": [],
        "required_params": {},
        "filters": {},
        "group_by": [],
        "sort": {"column_or_metric": "", "direction": "desc"},
        "top_n": None,
        "calculation_hints": [],
        "followup_cues": [],
        "confidence": 0.0,
    }

    template = str(template_value or DEFAULT_TEMPLATE).strip()
    values = {
        "schema": json.dumps(schema, ensure_ascii=False, indent=2),
        "user_question": user_question,
        "recent_history": _compact_dict(recent_history),
        "context": _compact_dict(context),
        "current_data": _compact_dict(current_data),
        "domain_summary": _compact_dict(domain_prompt_context or _domain_summary(domain, domain_index), limit=7000),
        "table_catalog_summary": "{}",
    }
    try:
        return template.format(**values)
    except KeyError as exc:
        raise ValueError(f"Template placeholder error: {exc}") from exc


class BuildIntentPrompt(Component):
    display_name = "Build Intent Prompt"
    description = "Create the JSON-only prompt used to extract manufacturing intent from the user question."
    icon = "TextCursorInput"
    name = "BuildIntentPrompt"

    inputs = [
        PromptInput(
            name="template",
            display_name="Template",
            value=DEFAULT_TEMPLATE,
            required=True,
            info="Use {schema}, {user_question}, {recent_history}, {context}, {current_data}, and {domain_summary}.",
        ),
        DataInput(
            name="main_context",
            display_name="Main Context",
            info="Output from Main Flow Context Builder. Preferred input for user question, state, and domain.",
            input_types=["Data", "JSON"],
        ),
        MessageTextInput(name="user_question", display_name="User Question", info="Legacy direct question input.", advanced=True),
        DataInput(
            name="agent_state",
            display_name="Agent State",
            info="Legacy direct state input. Prefer Main Context.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
        DataInput(
            name="domain_payload",
            display_name="Domain Payload",
            info="Legacy direct domain input. Prefer Main Context.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="prompt", display_name="Prompt Message", method="build_prompt", group_outputs=True, types=["Message"]),
        Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt_payload", group_outputs=True, types=["Data"]),
    ]

    def build_prompt_text(self) -> str:
        prompt = build_intent_prompt(
            getattr(self, "user_question", ""),
            getattr(self, "agent_state", None),
            getattr(self, "domain_payload", None) or getattr(self, "domain", None),
            getattr(self, "template", "") or DEFAULT_TEMPLATE,
            getattr(self, "main_context", None),
        )
        self.status = {"prompt_chars": len(prompt)}
        return prompt

    def build_prompt(self) -> Message:
        return _make_message(self.build_prompt_text())

    def build_prompt_payload(self) -> Data:
        prompt = self.build_prompt_text()
        return _make_data({"prompt": prompt, "prompt_type": "intent"})
