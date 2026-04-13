"""Portable Langflow node: save manufacturing session and emit final response message."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageInput, MessageTextInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


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
        if role and content:
            normalized.append({"role": role, "content": content})
    return normalized


class PortableManufacturingSessionSaveComponent(Component):
    display_name = "Portable Manufacturing Session Save"
    description = "Persist the merged result and emit a Chat Output compatible Message."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Save"
    name = "portable_manufacturing_session_save"

    inputs = [
        MessageInput(name="message", display_name="Message", info="Original Chat Input message"),
        DataInput(name="result", display_name="Result", info="Merged result payload"),
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
    ]

    outputs = [
        Output(name="saved_result", display_name="Saved Result", method="saved_result", types=["Data"], selected="Data"),
        Output(name="response_message", display_name="Response Message", method="response_message", types=["Message"], selected="Message"),
    ]

    _cached_result: dict[str, Any] | None = None

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

    def _load_existing_history(self) -> list[dict[str, str]]:
        session_file = self._session_file()
        if not session_file.exists():
            return []
        try:
            payload = json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            return []
        return _normalize_chat_history(payload.get("chat_history"))

    def _save(self) -> dict[str, Any]:
        if self._cached_result is not None:
            return self._cached_result

        result_payload = _as_payload(getattr(self, "result", None))
        if not result_payload:
            self.status = "No result payload"
            self._cached_result = {}
            return self._cached_result

        session_id = self._resolve_session_id()
        history = self._load_existing_history()
        user_text = _message_text(getattr(self, "message", None)).strip()
        response_text = str(result_payload.get("response") or "").strip()
        if user_text:
            history.append({"role": "user", "content": user_text})
        if response_text:
            history.append({"role": "assistant", "content": response_text})

        session_payload = {
            "session_id": session_id,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "chat_history": history,
            "context": result_payload.get("extracted_params") if isinstance(result_payload.get("extracted_params"), dict) else {},
            "current_data": result_payload.get("current_data") if isinstance(result_payload.get("current_data"), dict) else None,
        }
        session_file = self._session_file()
        session_file.write_text(json.dumps(session_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        saved = {**result_payload, "session_id": session_id, "session_memory_path": str(session_file)}
        self._cached_result = saved
        self.status = f"Saved session: {session_id}"
        return saved

    def saved_result(self) -> Data | None:
        payload = self._save()
        return Data(data=payload) if payload else None

    def response_message(self) -> Message | None:
        payload = self._save()
        if not payload:
            return None
        return Message(text=str(payload.get("response") or ""), data=payload, session_id=str(payload.get("session_id") or ""))
