import os

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


def _resolve_model_name(task: str) -> str:
    """Return the model name that fits the task."""

    fast_model = os.getenv("LLM_FAST_MODEL", "").strip() or "gemini-flash-latest"
    strong_model = os.getenv("LLM_STRONG_MODEL", "").strip() or fast_model
    normalized_task = str(task or "").strip().lower()

    if normalized_task in MODEL_TASK_GROUPS["strong"]:
        return strong_model
    return fast_model


def get_llm(task: str = "general", temperature: float = 0.0):
    """Create an LLM client for one task category."""

    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is not set.")

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
