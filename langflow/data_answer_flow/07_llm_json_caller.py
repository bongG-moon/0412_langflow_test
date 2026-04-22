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
#   from lfx.io import DataInput, MessageTextInput, Output, SecretStrInput
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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
SecretStrInput = _load_attr(["lfx.io", "langflow.io"], "SecretStrInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
ChatGoogleGenerativeAI = _load_attr(
    ["langchain_google_genai"],
    "ChatGoogleGenerativeAI",
    None,
)


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
        return {"text": text}
    return {}


def _read_secret(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "get_secret_value"):
        try:
            return str(value.get_secret_value() or "").strip()
        except Exception:
            return ""
    return str(value or "").strip()


def _read_prompt_payload(value: Any) -> Dict[str, Any]:
    if isinstance(value, str):
        return {"prompt": value}
    return _payload_from_value(value)


def _read_prompt(value: Any) -> str:
    if isinstance(value, str):
        return value
    payload = _read_prompt_payload(value)
    for key in ("prompt", "intent_prompt", "retrieval_plan_prompt", "pandas_code_prompt", "text"):
        if isinstance(payload.get(key), str):
            return payload[key]
    text = getattr(value, "text", None)
    return str(text or "").strip()


def _extract_text_from_response(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif hasattr(item, "text"):
                parts.append(str(getattr(item, "text") or ""))
        return "".join(parts).strip()
    return str(content or "").strip()


def _resolve_response_mode(prompt_payload: Dict[str, Any], response_mode: Any) -> str:
    mode = str(response_mode or "auto").strip().lower()
    if mode in {"json", "text"}:
        return mode
    prompt_type = str(prompt_payload.get("prompt_type") or "").strip().lower()
    if prompt_type in {"intent", "pandas_analysis", "json"}:
        return "json"
    prompt_text = str(prompt_payload.get("prompt") or "")
    if "return json" in prompt_text.lower() or "return only one valid json" in prompt_text.lower():
        return "json"
    return "text"


def _resolve_system_instruction(system_instruction: Any, mode: str) -> str:
    explicit = str(system_instruction or "").strip()
    if explicit:
        return explicit
    if mode == "json":
        return "Return only valid JSON. Do not include markdown fences."
    return "Follow the user prompt and answer in the requested format."


def call_llm_api(
    prompt: Any,
    llm_api_key: Any,
    model_name: str,
    temperature: Any,
    timeout_seconds: Any,
    response_mode: Any = "auto",
    system_instruction: Any = "",
) -> Dict[str, Any]:
    prompt_payload = _read_prompt_payload(prompt)
    prompt_text = _read_prompt(prompt)
    api_key = _read_secret(llm_api_key)
    model = str(model_name or "").strip() or "gemini-flash-latest"
    mode = _resolve_response_mode(prompt_payload, response_mode)
    system_text = _resolve_system_instruction(system_instruction, mode)
    debug: Dict[str, Any] = {
        "provider": "langchain_google_genai",
        "model_name": model,
        "response_mode": mode,
        "prompt_chars": len(prompt_text),
        "ok": False,
        "error": None,
    }

    if not prompt_text:
        debug["error"] = "prompt is empty"
        return {"llm_text": "", "llm_debug": debug}
    if not api_key:
        debug["error"] = "llm_api_key is empty"
        return {"llm_text": "", "llm_debug": debug}
    if ChatGoogleGenerativeAI is None:
        debug["error"] = "langchain_google_genai is not installed"
        return {"llm_text": "", "llm_debug": debug}

    try:
        temp = float(temperature)
    except Exception:
        temp = 0.0
    try:
        timeout = float(timeout_seconds)
    except Exception:
        timeout = 60.0

    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temp,
            timeout=timeout,
        )
        response = llm.invoke(
            [
                ("system", system_text),
                ("human", prompt_text),
            ]
        )
        text = _extract_text_from_response(getattr(response, "content", response))
        if not text:
            debug["error"] = "empty LLM response text"
            return {"llm_text": "", "llm_debug": debug}
    except Exception:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=temp,
            )
            response = llm.invoke(
                [
                    ("system", system_text),
                    ("human", prompt_text),
                ]
            )
            text = _extract_text_from_response(getattr(response, "content", response))
        except Exception as exc:
            debug["error"] = str(exc)
            return {"llm_text": "", "llm_debug": debug}
    debug["ok"] = True
    debug["response_chars"] = len(text or "")
    return {"llm_text": text or "", "llm_debug": debug}


class LLMAPICaller(Component):
    display_name = "LLM API Caller"
    description = "Call an LLM API with per-node API key/model settings and return text for downstream parsers."
    icon = "BrainCircuit"
    name = "LLMAPICaller"

    inputs = [
        DataInput(
            name="prompt",
            display_name="Prompt Payload",
            info="Prompt payload from a prompt builder.",
            input_types=["Data", "JSON", "Message", "Text"],
        ),
        SecretStrInput(
            name="llm_api_key",
            display_name="LLM API Key",
            info="API key used by this LLM node.",
            advanced=True,
        ),
        MessageTextInput(
            name="model_name",
            display_name="Model Name",
            info="Model to use for this LLM node.",
            value="gemini-flash-latest",
        ),
        MessageTextInput(name="temperature", display_name="Temperature", value="0", advanced=True),
        MessageTextInput(name="timeout_seconds", display_name="Timeout Seconds", value="60", advanced=True),
        MessageTextInput(
            name="response_mode",
            display_name="Response Mode",
            info="auto, json, or text. auto uses prompt_type when available.",
            value="auto",
            advanced=True,
        ),
        MessageTextInput(
            name="system_instruction",
            display_name="System Instruction",
            info="Optional. Leave empty to use a safe default based on Response Mode.",
            value="",
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="llm_result", display_name="LLM Result", method="call_llm", types=["Data"]),
    ]

    def call_llm(self) -> Data:
        payload = call_llm_api(
            getattr(self, "prompt", None),
            getattr(self, "llm_api_key", None),
            getattr(self, "model_name", ""),
            getattr(self, "temperature", "0"),
            getattr(self, "timeout_seconds", "60"),
            getattr(self, "response_mode", "auto"),
            getattr(self, "system_instruction", ""),
        )
        return _make_data(payload)
