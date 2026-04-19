from __future__ import annotations

import json
import urllib.error
import urllib.parse
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


def _generate_content_endpoint(model_name: str, api_version: str = "v1beta") -> str:
    version = str(api_version or "v1beta").strip().strip("/") or "v1beta"
    model = str(model_name or "").strip()
    if model.startswith("models/"):
        model = model.split("/", 1)[1]
    encoded_model = urllib.parse.quote(model, safe="-_.")
    return f"https://generativelanguage.googleapis.com/{version}/models/{encoded_model}:generateContent"


def _extract_llm_response_text(parsed: Dict[str, Any]) -> str:
    candidates = parsed.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    first = candidates[0] if isinstance(candidates[0], dict) else {}
    content = first.get("content") if isinstance(first, dict) else {}
    parts = content.get("parts") if isinstance(content, dict) else []
    if not isinstance(parts, list):
        return ""

    text_parts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            text_parts.append(part["text"])
    return "".join(text_parts).strip()


def call_llm_json(
    prompt: Any,
    llm_api_key: Any,
    model_name: str,
    temperature: Any,
    timeout_seconds: Any,
    api_version: str = "v1beta",
) -> Dict[str, Any]:
    prompt_text = _read_prompt(prompt)
    api_key = _read_secret(llm_api_key)
    model = str(model_name or "").strip() or "gemini-flash-latest"
    endpoint = _generate_content_endpoint(model, api_version)
    debug: Dict[str, Any] = {
        "provider": "llm_api",
        "endpoint": endpoint,
        "model_name": model,
        "api_version": str(api_version or "v1beta"),
        "response_mime_type": "application/json",
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

    try:
        temp = float(temperature)
    except Exception:
        temp = 0.0
    try:
        timeout = float(timeout_seconds)
    except Exception:
        timeout = 60.0

    body = {
        "system_instruction": {
            "parts": [{"text": "Return only valid JSON. Do not include markdown fences."}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_text}],
            }
        ],
        "generationConfig": {
            "temperature": temp,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
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
        text = _extract_llm_response_text(parsed)
        if not text:
            prompt_feedback = parsed.get("promptFeedback") or parsed.get("prompt_feedback")
            finish_reason = None
            candidates = parsed.get("candidates")
            if isinstance(candidates, list) and candidates and isinstance(candidates[0], dict):
                finish_reason = candidates[0].get("finishReason") or candidates[0].get("finish_reason")
            debug["error"] = f"empty LLM response text; finish_reason={finish_reason}; prompt_feedback={prompt_feedback}"
            return {"llm_text": "", "llm_debug": debug}
    except Exception:
        text = raw
    debug["ok"] = True
    debug["response_chars"] = len(text or "")
    return {"llm_text": text or "", "llm_debug": debug}


class LLMJsonCaller(Component):
    display_name = "LLM JSON Caller"
    description = "Call an LLM API and return JSON-oriented text."
    icon = "BrainCircuit"
    name = "LLMJsonCaller"

    inputs = [
        DataInput(
            name="prompt",
            display_name="Prompt",
            info="Prompt payload from a prompt builder.",
            input_types=["Data", "JSON"],
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
        MessageTextInput(name="api_version", display_name="LLM API Version", value="v1beta", advanced=True),
        MessageTextInput(name="temperature", display_name="Temperature", value="0", advanced=True),
        MessageTextInput(name="timeout_seconds", display_name="Timeout Seconds", value="60", advanced=True),
    ]

    outputs = [
        Output(name="llm_result", display_name="LLM Result", method="call_llm", types=["Data"]),
    ]

    def call_llm(self) -> Data:
        payload = call_llm_json(
            getattr(self, "prompt", None),
            getattr(self, "llm_api_key", None),
            getattr(self, "model_name", ""),
            getattr(self, "temperature", "0"),
            getattr(self, "timeout_seconds", "60"),
            getattr(self, "api_version", "v1beta"),
        )
        return _make_data(payload, text=payload.get("llm_text", ""))
