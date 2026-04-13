"""Portable Langflow node: load manufacturing session state."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, MessageInput, MessageTextInput, Output
from lfx.schema.data import Data


def _message_text(value: Any) -> str:
    if value is None:
        return ""
    text = getattr(value, "text", None)
    if text is not None:
        return str(text)
    if isinstance(value, dict):
        return str(value.get("text") or "")
    return str(value)


def _message_session_id(value: Any) -> str:
    if value is None:
        return ""
    session_id = getattr(value, "session_id", None)
    if session_id is not None:
        return str(session_id or "")
    if isinstance(value, dict):
        return str(value.get("session_id") or "")
    return ""


def _safe_session_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", str(raw or "").strip())
    return cleaned or "default"


def _storage_dir(subdir: str) -> Path:
    candidate = Path.cwd() / (subdir.strip() or ".portable_langflow_sessions")
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except Exception:
        fallback = Path.home() / (subdir.strip() or ".portable_langflow_sessions")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _normalize_chat_history(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "").strip()
        if not role or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


class PortableManufacturingSessionStateComponent(Component):
    display_name = "Portable Manufacturing Session State"
    description = "Load chat history, context, and current data from a local session file."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Database"
    name = "portable_manufacturing_session_state"

    inputs = [
        MessageInput(name="message", display_name="Message", info="Chat Input message"),
        MessageInput(
            name="message_history",
            display_name="Message History",
            advanced=True,
            info="Optional Message History node output",
        ),
        MessageTextInput(
            name="session_id_override",
            display_name="Session ID Override",
            advanced=True,
            info="Optional fixed session id",
        ),
        MessageTextInput(
            name="storage_subdir",
            display_name="Storage Subdir",
            value=".portable_langflow_sessions",
            advanced=True,
            info="Folder used to persist session JSON files",
        ),
        BoolInput(
            name="reset_session",
            display_name="Reset Session",
            value=False,
            advanced=True,
            info="If True, delete the existing session snapshot before loading",
        ),
    ]

    outputs = [
        Output(name="session_state", display_name="Session State", method="session_state", types=["Data"], selected="Data"),
    ]

    def _resolve_session_id(self) -> str:
        override = _message_text(getattr(self, "session_id_override", "")).strip()
        if override:
            return _safe_session_id(override)
        message_session_id = _message_session_id(getattr(self, "message", None))
        if message_session_id:
            return _safe_session_id(message_session_id)
        graph = getattr(self, "graph", None)
        graph_session_id = getattr(graph, "session_id", "")
        if graph_session_id:
            return _safe_session_id(graph_session_id)
        return "default"

    def _session_file(self) -> Path:
        subdir = _message_text(getattr(self, "storage_subdir", "")).strip() or ".portable_langflow_sessions"
        return _storage_dir(subdir) / f"{self._resolve_session_id()}.json"

    def _load_snapshot(self) -> dict[str, Any]:
        session_file = self._session_file()
        if bool(getattr(self, "reset_session", False)) and session_file.exists():
            session_file.unlink(missing_ok=True)
        if not session_file.exists():
            return {
                "chat_history": [],
                "context": {},
                "current_data": None,
            }
        try:
            payload = json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        return {
            "chat_history": _normalize_chat_history(payload.get("chat_history")),
            "context": payload.get("context") if isinstance(payload.get("context"), dict) else {},
            "current_data": payload.get("current_data") if isinstance(payload.get("current_data"), dict) else None,
        }

    def session_state(self) -> Data | None:
        user_input = _message_text(getattr(self, "message", None)).strip()
        if not user_input:
            self.status = "No input message"
            return None

        snapshot = self._load_snapshot()
        session_id = self._resolve_session_id()
        history_text = _message_text(getattr(self, "message_history", None)).strip()

        state = {
            "session_id": session_id,
            "user_input": user_input,
            "chat_history": snapshot.get("chat_history", []),
            "history_text": history_text,
            "context": snapshot.get("context", {}),
            "current_data": snapshot.get("current_data"),
            "runtime": {"source": "portable_langflow_1_8_bundle"},
        }
        self.status = f"Loaded session: {session_id}"
        return Data(data=state)
