"""Shared state initializer for standalone Langflow custom components."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def _coerce_json_field(value: Any, default: Any) -> Any:
    """Convert JSON-like text input into Python objects for initial state creation."""

    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def build_initial_state(
    user_input: str,
    chat_history: List[Dict[str, str]] | str | None = None,
    context: Dict[str, Any] | str | None = None,
    current_data: Dict[str, Any] | str | None = None,
    domain_rules_text: str | None = None,
    domain_registry_payload: Dict[str, Any] | List[Any] | str | None = None,
    llm_config: Dict[str, Any] | str | None = None,
) -> Dict[str, Any]:
    """Build the shared state contract used across standalone Langflow nodes."""

    return {
        "user_input": str(user_input or ""),
        "chat_history": _coerce_json_field(chat_history, []),
        "context": _coerce_json_field(context, {}),
        "current_data": _coerce_json_field(current_data, None),
        "domain_rules_text": str(domain_rules_text or "").strip(),
        "domain_registry_payload": _coerce_json_field(domain_registry_payload, {}),
        "llm_config": _coerce_json_field(llm_config, {}),
    }
