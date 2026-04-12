"""Langflow branch-visible nodes reuse only the shared state initializer here."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from manufacturing_agent.graph.state import AgentGraphState


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
) -> AgentGraphState:
    """Build the shared initial state contract used across Langflow wrappers."""

    return {
        "user_input": str(user_input or ""),
        "chat_history": _coerce_json_field(chat_history, []),
        "context": _coerce_json_field(context, {}),
        "current_data": _coerce_json_field(current_data, None),
    }
