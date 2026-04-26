from __future__ import annotations

import json
from copy import deepcopy
from importlib import import_module
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, MultilineInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    return deepcopy(data) if isinstance(data, dict) else {}


def _load_llm(llm_api_key: str, model_name: str, temperature: float):
    module = import_module("langchain_google_genai")
    return module.ChatGoogleGenerativeAI(api_key=llm_api_key, model=model_name, temperature=temperature, convert_system_message_to_human=True)

    # OpenAI-compatible deployment example:
    # from langchain_openai import ChatOpenAI
    # return ChatOpenAI(api_key=llm_api_key, model=model_name, temperature=temperature)


def call_llm_json(prompt_payload_value: Any, llm_api_key: str = "", model_name: str = "", temperature: Any = "0") -> Dict[str, Any]:
    payload = _payload_from_value(prompt_payload_value)
    prompt_payload = payload.get("prompt_payload") if isinstance(payload.get("prompt_payload"), dict) else payload
    if prompt_payload.get("skipped"):
        return {"llm_result": {"skipped": True, "skip_reason": prompt_payload.get("skip_reason", "route skipped"), "llm_text": "", "errors": [], "prompt_payload": prompt_payload, "model_name": model_name}}
    prompt = str(prompt_payload.get("prompt") or "")
    errors: list[str] = []
    llm_text = ""
    if str(llm_api_key or "").strip():
        try:
            temp = float(temperature or 0)
            selected_model = str(model_name or "").strip()
            if not selected_model:
                errors.append("Model Name is required when LLM API Key is set.")
            else:
                llm = _load_llm(str(llm_api_key).strip(), selected_model, temp)
                response = llm.invoke(prompt)
                llm_text = str(getattr(response, "content", response))
        except Exception as exc:
            errors.append(str(exc))
    return {"llm_result": {"llm_text": llm_text, "errors": errors, "prompt_payload": prompt_payload, "model_name": model_name}}


class LLMJsonCaller(Component):
    display_name = "LLM JSON Caller"
    description = "Standalone JSON-oriented LLM caller. Normalization happens in a later node."
    icon = "Sparkles"
    name = "LLMJsonCaller"

    inputs = [
        DataInput(name="prompt_payload", display_name="Prompt Payload", input_types=["Data", "JSON"]),
        MultilineInput(name="llm_api_key", display_name="LLM API Key", value="", advanced=True),
        MessageTextInput(name="model_name", display_name="Model Name", value="", advanced=True),
        MessageTextInput(name="temperature", display_name="Temperature", value="0", advanced=True),
    ]
    outputs = [Output(name="llm_result", display_name="LLM Result", method="build_result", types=["Data"])]

    def build_result(self):
        payload = call_llm_json(getattr(self, "prompt_payload", None), getattr(self, "llm_api_key", ""), getattr(self, "model_name", ""), getattr(self, "temperature", "0"))
        self.status = {"text_chars": len(payload["llm_result"].get("llm_text", "")), "errors": len(payload["llm_result"].get("errors", []))}
        return _make_data(payload)

