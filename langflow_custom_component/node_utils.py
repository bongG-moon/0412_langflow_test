"""Local helpers shared by standalone Langflow component nodes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from langflow_custom_component.component_base import read_data_payload


def ensure_component_root() -> Path:
    """Ensure the package parent is importable when Langflow loads nodes by file path."""

    repo_root = Path(__file__).resolve().parent.parent
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
    return repo_root


def coerce_json_field(value: Any, default: Any) -> Any:
    """Parse dict/list JSON-like input when the source passes plain text."""

    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def append_history(history: List[Dict[str, str]], role: str, content: str) -> List[Dict[str, str]]:
    """Append one chat turn without duplicating the latest identical entry."""

    cleaned = str(content or "").strip()
    if not cleaned:
        return history
    if history and history[-1].get("role") == role and history[-1].get("content") == cleaned:
        return history
    history.append({"role": role, "content": cleaned})
    return history


def read_message_text(message: Any) -> str:
    """Extract the visible user text from a Langflow Chat Input style payload."""

    if message is None:
        return ""
    text = getattr(message, "text", None)
    if text is None and isinstance(message, dict):
        text = message.get("text")
    return str(text or "")


def read_domain_text_payload(value: Any) -> str:
    """Extract raw domain-rules text from a node payload."""

    payload = read_data_payload(value)
    text = payload.get("domain_rules_text")
    return str(text or "").strip()


def read_domain_registry_payload(value: Any) -> Dict[str, Any] | List[Any]:
    """Extract parsed domain-registry JSON from a node payload."""

    payload = read_data_payload(value)
    registry_payload = payload.get("domain_registry_payload")
    if isinstance(registry_payload, (dict, list)):
        return registry_payload
    return coerce_json_field(registry_payload, {})


def activate_domain_context_from_state(state: Dict[str, Any]) -> None:
    """Push the current state's domain inputs into the runtime registry layer."""

    from langflow_custom_component._runtime.domain.registry import set_active_domain_context

    set_active_domain_context(
        domain_rules_text=state.get("domain_rules_text", ""),
        domain_registry_payload=state.get("domain_registry_payload", {}),
    )

