from __future__ import annotations

import json
import urllib.error
import urllib.request
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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
SecretStrInput = _load_attr(["lfx.io", "langflow.io"], "SecretStrInput", _make_input)
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


def _read_prompt(value: Any) -> str:
    if isinstance(value, str):
        return value
    payload = _payload_from_value(value)
    for key in ("prompt", "intent_prompt", "retrieval_plan_prompt", "pandas_code_prompt", "text"):
        if isinstance(payload.get(key), str):
            return payload[key]
    text = getattr(value, "text", None)
    return str(text or "").strip()


def _endpoint_from_base_url(base_url: str) -> str:
    base = str(base_url or "https://api.openai.com/v1").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def call_openai_compatible_json(
    prompt: Any,
    llm_api_key: Any,
    llm_base_url: str,
    model_name: str,
    temperature: Any,
    timeout_seconds: Any,
) -> Dict[str, Any]:
    prompt_text = _read_prompt(prompt)
    api_key = _read_secret(llm_api_key)
    model = str(model_name or "").strip()
    endpoint = _endpoint_from_base_url(llm_base_url)
    debug: Dict[str, Any] = {
        "endpoint": endpoint,
        "model_name": model,
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
    if not model:
        debug["error"] = "model_name is empty"
        return {"llm_text": "", "llm_debug": debug}

    try:
        temp = float(temperature)
    except Exception:
        temp = 0.0
    try:
        timeout = float(timeout_seconds)
    except Exception:
        timeout = 60.0

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON. Do not include markdown fences."},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": temp,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        debug["error"] = f"HTTP {exc.code}: {detail[:1000]}"
        return {"llm_text": "", "llm_debug": debug}
    except Exception as exc:
        debug["error"] = str(exc)
        return {"llm_text": "", "llm_debug": debug}

    try:
        parsed = json.loads(raw)
        text = parsed["choices"][0]["message"]["content"]
    except Exception:
        text = raw
    debug["ok"] = True
    debug["response_chars"] = len(text or "")
    return {"llm_text": text or "", "llm_debug": debug}


class LLMJsonCaller(Component):
    display_name = "LLM JSON Caller"
    description = "Call an OpenAI-compatible chat completions endpoint and return JSON-oriented text."
    icon = "BrainCircuit"
    name = "LLMJsonCaller"

    inputs = [
        DataInput(name="prompt", display_name="Prompt", info="Prompt payload from a prompt builder.", input_types=["Data"]),
        SecretStrInput(name="llm_api_key", display_name="LLM API Key", advanced=True),
        MessageTextInput(
            name="llm_base_url",
            display_name="LLM Base URL",
            value="https://api.openai.com/v1",
            advanced=True,
        ),
        MessageTextInput(name="model_name", display_name="Model Name", info="Model to use for this LLM node."),
        MessageTextInput(name="temperature", display_name="Temperature", value="0", advanced=True),
        MessageTextInput(name="timeout_seconds", display_name="Timeout Seconds", value="60", advanced=True),
    ]

    outputs = [
        Output(name="llm_result", display_name="LLM Result", method="call_llm", types=["Data"]),
    ]

    def call_llm(self) -> Any:
        payload = call_openai_compatible_json(
            getattr(self, "prompt", None),
            getattr(self, "llm_api_key", None),
            getattr(self, "llm_base_url", "https://api.openai.com/v1"),
            getattr(self, "model_name", ""),
            getattr(self, "temperature", "0"),
            getattr(self, "timeout_seconds", "60"),
        )
        return _make_data(payload, text=payload.get("llm_text", ""))
