from __future__ import annotations

import json
from typing import Any, Dict


def _extract_text_from_response(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content or "")


def extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = str(text or "").strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM response does not contain a JSON object.")
    return json.loads(cleaned[start : end + 1])


def invoke_llm_text(prompt: str, api_key: str, model_name: str, temperature: float = 0.0) -> str:
    if not str(api_key or "").strip():
        raise ValueError("LLM API key is required.")
    if not str(model_name or "").strip():
        raise ValueError("Model name is required.")

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as exc:
        raise RuntimeError(
            "langchain-google-genai and langchain-core are required for LLM calls. "
            "Install project requirements first."
        ) from exc

    llm = ChatGoogleGenerativeAI(
        model=str(model_name).strip(),
        google_api_key=str(api_key).strip(),
        temperature=float(temperature or 0.0),
    )
    response = llm.invoke(
        [
            SystemMessage(content="You are a precise JSON-only manufacturing data assistant."),
            HumanMessage(content=prompt),
        ]
    )
    return _extract_text_from_response(getattr(response, "content", response))


def invoke_llm_json(prompt: str, api_key: str, model_name: str, temperature: float = 0.0) -> Dict[str, Any]:
    text = invoke_llm_text(prompt, api_key, model_name, temperature)
    parsed = extract_json_object(text)
    parsed["_llm_text"] = text
    return parsed
