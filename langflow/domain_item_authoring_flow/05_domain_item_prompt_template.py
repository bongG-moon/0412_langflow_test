from __future__ import annotations

import json
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
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


class _FallbackMessage:
    def __init__(self, text: str | None = None, **kwargs: Any):
        self.text = text or str(kwargs.get("content") or "")
        self.content = self.text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
PromptInput = _load_attr(["lfx.io", "langflow.io"], "PromptInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)


DEFAULT_TEMPLATE = """You are extracting manufacturing domain items for a data-answering agent.
Return JSON only. Do not include markdown fences.

Selected item categories:
{routes}

Allowed item schemas:
{item_schemas}

Existing items in the selected categories:
{existing_items}

Split source notes:
{raw_notes}

Output schema:
{output_schema}

Rules:
- Extract only facts explicitly supported by RAW_TEXT.
- Do not copy explanations, logs, preview text, or unrelated content into payload.
- If RAW_TEXT contains multiple categories, return multiple items.
- If Split source notes are provided, set source_note_id on each item when the item comes from a specific note.
- Use stable snake_case keys.
- Put uncertainty into item warnings or unmapped_text.

RAW_TEXT:
{raw_text}
"""


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


def build_domain_item_prompt(prompt_context: Any, template_value: Any = None) -> str:
    context = _payload_from_value(prompt_context)
    template_vars = context.get("template_vars") if isinstance(context.get("template_vars"), dict) else {}
    template = str(template_value or DEFAULT_TEMPLATE).strip()
    try:
        return template.format(**template_vars)
    except KeyError as exc:
        raise ValueError(f"Template placeholder error: {exc}") from exc


class DomainItemPromptTemplate(Component):
    display_name = "Domain Item Prompt Template"
    description = "Build the LLM prompt from route context variables. You may replace this with a built-in Prompt Template node."
    icon = "MessageSquare"
    name = "DomainItemPromptTemplate"

    inputs = [
        PromptInput(
            name="template",
            display_name="Template",
            value=DEFAULT_TEMPLATE,
            required=True,
            info="Use {routes}, {item_schemas}, {existing_items}, {raw_notes}, {output_schema}, and {raw_text}.",
        ),
        DataInput(name="prompt_context", display_name="Prompt Context", info="Output from Domain Item Prompt Context Builder.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="prompt", display_name="Prompt Message", method="build_prompt", group_outputs=True, types=["Message"]),
        Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt_payload", group_outputs=True, types=["Data"]),
    ]

    def build_prompt_text(self) -> str:
        context = _payload_from_value(getattr(self, "prompt_context", None))
        prompt = build_domain_item_prompt(getattr(self, "prompt_context", None), getattr(self, "template", "") or DEFAULT_TEMPLATE)
        self.status = {
            "prompt_chars": len(prompt),
            "routes": context.get("routes", []),
        }
        return prompt

    def build_prompt(self) -> Message:
        return _make_message(self.build_prompt_text())

    def build_prompt_payload(self) -> Data:
        prompt = self.build_prompt_text()
        return _make_data({"prompt": prompt, "prompt_type": "domain_item_json"})
