import os
from typing import Any, Dict

from dotenv import load_dotenv


load_dotenv()


# We keep the routing table very small on purpose.
# Beginners can read this as:
# - fast  : cheap / quick decisions
# - strong: heavier planning or code generation
MODEL_TASK_GROUPS = {
    "fast": {
        "parameter_extract",
        "query_mode_review",
        "response_summary",
    },
    "strong": {
        "retrieval_plan",
        "sufficiency_review",
        "analysis_code",
        "analysis_retry",
        "domain_registry_parse",
    },
}

ACTIVE_LLM_CONFIG: Dict[str, Any] = {}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "get_secret_value"):
        try:
            return str(value.get_secret_value() or "").strip()
        except Exception:
            return ""
    return str(value or "").strip()


def set_active_llm_config(config: Dict[str, Any] | None = None) -> None:
    """Store per-node LLM settings entered in the Langflow component UI."""

    global ACTIVE_LLM_CONFIG
    if not isinstance(config, dict):
        ACTIVE_LLM_CONFIG = {}
        return

    ACTIVE_LLM_CONFIG = {
        "api_key": _clean_text(config.get("api_key")),
        "fast_model": _clean_text(config.get("fast_model")) or "gemini-flash-latest",
        "strong_model": _clean_text(config.get("strong_model")) or _clean_text(config.get("fast_model")) or "gemini-flash-latest",
    }


def get_active_llm_config() -> Dict[str, str]:
    return {
        "api_key": _clean_text(ACTIVE_LLM_CONFIG.get("api_key")) or os.getenv("LLM_API_KEY", "").strip(),
        "fast_model": _clean_text(ACTIVE_LLM_CONFIG.get("fast_model"))
        or os.getenv("LLM_FAST_MODEL", "").strip()
        or "gemini-flash-latest",
        "strong_model": _clean_text(ACTIVE_LLM_CONFIG.get("strong_model"))
        or os.getenv("LLM_STRONG_MODEL", "").strip()
        or _clean_text(ACTIVE_LLM_CONFIG.get("fast_model"))
        or os.getenv("LLM_FAST_MODEL", "").strip()
        or "gemini-flash-latest",
    }


def _resolve_model_name(task: str) -> str:
    """Return the model name that fits the task."""

    config = get_active_llm_config()
    fast_model = config["fast_model"]
    strong_model = config["strong_model"]
    normalized_task = str(task or "").strip().lower()

    if normalized_task in MODEL_TASK_GROUPS["strong"]:
        return strong_model
    return fast_model


def get_llm(task: str = "general", temperature: float = 0.0):
    """Create an LLM client for one task category."""

    api_key = get_active_llm_config()["api_key"]
    if not api_key:
        raise ValueError("LLM API key is not set. Enter it in the Langflow LLM settings input or Global Variables.")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise ImportError("langchain_google_genai package is required to build the LLM client.") from exc

    return ChatGoogleGenerativeAI(
        model=_resolve_model_name(task),
        google_api_key=api_key,
        temperature=temperature,
    )


SYSTEM_PROMPT = """You are an AI assistant for manufacturing data retrieval and follow-up analysis.

Rules:
- First decide whether the user needs fresh source retrieval or a follow-up transformation on current data.
- When retrieval is needed, extract only retrieval-safe parameters and use them to load raw source data.
- When current data is already sufficient, answer through pandas-style follow-up analysis.
- Never invent missing datasets or columns.
- Always explain results based on the current result table.
"""
