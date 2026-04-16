"""Reusable Langflow inputs for nodes that call an LLM."""

from __future__ import annotations

from typing import Any

from langflow_custom_component.component_base import MessageTextInput, SecretStrInput


def read_secret_text(value: Any) -> str:
    """Read plain or SecretStr-like values from Langflow inputs."""

    if value is None:
        return ""
    if hasattr(value, "get_secret_value"):
        try:
            return str(value.get_secret_value() or "").strip()
        except Exception:
            return ""
    return str(value or "").strip()


def llm_settings_inputs() -> list[Any]:
    """Return reusable LLM inputs for nodes that actually call the model."""

    return [
        SecretStrInput(
            name="llm_api_key",
            display_name="LLM API Key",
            info="Gemini API key. Bind this to a Langflow Global Variable if desired.",
            advanced=True,
        ),
        MessageTextInput(
            name="llm_fast_model",
            display_name="Fast Model",
            value="gemini-flash-latest",
            info="Model used for parameter extraction, routing, and response summaries.",
            advanced=True,
        ),
        MessageTextInput(
            name="llm_strong_model",
            display_name="Strong Model",
            value="gemini-flash-latest",
            info="Model used for dataset planning and pandas analysis code generation.",
            advanced=True,
        ),
    ]


def apply_llm_settings_from_component(component: Any, set_active_llm_config: Any) -> None:
    """Apply LLM settings from one Langflow node before invoking runtime code."""

    fast_model = str(getattr(component, "llm_fast_model", "") or "gemini-flash-latest").strip()
    strong_model = str(getattr(component, "llm_strong_model", "") or fast_model).strip()
    set_active_llm_config(
        {
            "api_key": read_secret_text(getattr(component, "llm_api_key", None)),
            "fast_model": fast_model or "gemini-flash-latest",
            "strong_model": strong_model or fast_model or "gemini-flash-latest",
        }
    )
