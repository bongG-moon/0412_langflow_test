"""Langflow custom component: Manufacturing Session Memory."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, MessageTextInput, Output


def _ensure_repo_root() -> Path:
    def _is_repo_root(path: Path) -> bool:
        return (path / "langflow_version").is_dir() and (path / "manufacturing_agent").is_dir()

    candidates: list[Path] = []

    explicit_root = os.environ.get("MANUFACTURING_AGENT_PROJECT_ROOT")
    if explicit_root:
        candidates.append(Path(explicit_root).expanduser())

    components_path = os.environ.get("LANGFLOW_COMPONENTS_PATH")
    if components_path:
        candidates.append(Path(components_path).expanduser().resolve().parent)

    cwd = Path.cwd().resolve()
    candidates.append(cwd)
    candidates.extend(cwd.parents)

    for candidate in candidates:
        candidate = candidate.resolve()
        if not _is_repo_root(candidate):
            continue
        candidate_text = str(candidate)
        if candidate_text not in sys.path:
            sys.path.insert(0, candidate_text)
        return candidate

    raise ModuleNotFoundError(
        "Could not locate the project root for custom components. "
        "Set MANUFACTURING_AGENT_PROJECT_ROOT or LANGFLOW_COMPONENTS_PATH."
    )


def _coerce_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _coerce_chat_history(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip()
        content = str(item.get("content", "")).strip()
        if not role or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def _append_history(history: List[Dict[str, str]], role: str, content: str) -> List[Dict[str, str]]:
    cleaned = str(content or "").strip()
    if not cleaned:
        return history
    if history and history[-1].get("role") == role and history[-1].get("content") == cleaned:
        return history
    history.append({"role": role, "content": cleaned})
    return history


class ManufacturingSessionMemoryComponent(Component):
    display_name = "Manufacturing Session Memory"
    description = "Load or save chat_history, context, and current_data for multi-turn manufacturing flows."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Database"
    name = "manufacturing_session_memory"

    inputs = [
        MessageInput(name="message", display_name="Chat Message", info="Incoming Chat Input message with text and session_id"),
        DataInput(name="result", display_name="Result", info="Merged final result payload to save back into the session"),
        MessageTextInput(
            name="session_id_override",
            display_name="Session ID Override",
            info="Optional fixed session id. Leave empty to reuse the chat session id.",
            advanced=True,
        ),
        MessageTextInput(
            name="storage_subdir",
            display_name="Storage Subdir",
            value=".langflow_session_store",
            info="Folder used under the project root to persist session JSON files.",
            advanced=True,
        ),
    ]
    outputs = [
        Output(name="session_state", display_name="Session State", method="session_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="saved_result", display_name="Saved Result", method="saved_result", group_outputs=True, types=["Data"], selected="Data"),
    ]

    def _message_text(self) -> str:
        message = getattr(self, "message", None)
        if message is None:
            return ""
        text = getattr(message, "text", None)
        if text is None and isinstance(message, dict):
            text = message.get("text")
        return str(text or "")

    def _resolve_session_id(self) -> str:
        override = str(getattr(self, "session_id_override", "") or "").strip()
        if override:
            return override

        message = getattr(self, "message", None)
        message_session_id = getattr(message, "session_id", None)
        if not message_session_id and isinstance(message, dict):
            message_session_id = message.get("session_id")
        if message_session_id:
            return str(message_session_id)

        graph = getattr(self, "graph", None)
        graph_session_id = getattr(graph, "session_id", None)
        if graph_session_id:
            return str(graph_session_id)

        return "default"

    def _session_file(self) -> Path:
        repo_root = _ensure_repo_root()
        subdir = str(getattr(self, "storage_subdir", "") or ".langflow_session_store").strip() or ".langflow_session_store"
        safe_session_id = re.sub(r"[^a-zA-Z0-9._-]", "_", self._resolve_session_id())
        storage_dir = (repo_root / subdir).resolve()
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / f"{safe_session_id}.json"

    def _load_snapshot(self) -> Dict[str, Any]:
        session_file = self._session_file()
        if not session_file.exists():
            return {
                "session_id": self._resolve_session_id(),
                "chat_history": [],
                "context": {},
                "current_data": None,
            }

        try:
            payload = json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            payload = {}

        return {
            "session_id": self._resolve_session_id(),
            "chat_history": _coerce_chat_history(payload.get("chat_history")),
            "context": _coerce_dict(payload.get("context")),
            "current_data": payload.get("current_data") if isinstance(payload.get("current_data"), dict) else None,
        }

    @staticmethod
    def _unwrap_result_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        if "response" in payload or "tool_results" in payload or "current_data" in payload:
            return payload
        nested_result = payload.get("result")
        if isinstance(nested_result, dict):
            return nested_result
        state = payload.get("state")
        if isinstance(state, dict) and isinstance(state.get("result"), dict):
            return state["result"]
        return {}

    def session_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data
        from langflow_version.workflow import build_initial_state

        user_input = self._message_text()
        if not user_input.strip():
            self.status = "No chat message; session load skipped"
            return None

        snapshot = self._load_snapshot()
        state = build_initial_state(
            user_input=user_input,
            chat_history=snapshot.get("chat_history", []),
            context=snapshot.get("context", {}),
            current_data=snapshot.get("current_data"),
        )
        state["session_id"] = snapshot.get("session_id", self._resolve_session_id())
        self.status = f"Session loaded: {state.get('session_id', 'default')}"
        return make_data({"state": state})

    def saved_result(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload

        result_payload = self._unwrap_result_payload(read_data_payload(getattr(self, "result", None)))
        if not result_payload:
            self.status = "No result payload; session save skipped"
            return None

        snapshot = self._load_snapshot()
        history = list(snapshot.get("chat_history", []))
        history = _append_history(history, "user", self._message_text())
        history = _append_history(history, "assistant", str(result_payload.get("response", "") or ""))

        extracted_params = result_payload.get("extracted_params")
        current_data = result_payload.get("current_data")

        updated_snapshot = {
            "session_id": snapshot.get("session_id", self._resolve_session_id()),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "chat_history": history,
            "context": extracted_params if isinstance(extracted_params, dict) else snapshot.get("context", {}),
            "current_data": current_data if isinstance(current_data, dict) else snapshot.get("current_data"),
        }

        session_file = self._session_file()
        session_file.write_text(
            json.dumps(updated_snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        saved_payload = {
            **result_payload,
            "session_id": updated_snapshot["session_id"],
            "session_memory_path": str(session_file),
        }
        self.status = f"Session saved: {updated_snapshot['session_id']}"
        return make_data(saved_payload)
