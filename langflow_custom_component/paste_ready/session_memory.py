from __future__ import annotations

# VISIBLE_STANDALONE_RUNTIME: visible per-node standalone code with no hidden source bundle.

# ---- visible runtime: component_base ----
"""Helpers shared by standalone Langflow custom components.

This package is meant to be copied into a Langflow custom-component folder, so
the wrappers below keep the nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""
import dataclasses as lf_component_base_import_dataclasses
lf_component_base_dataclass = lf_component_base_import_dataclasses.dataclass
import importlib as lf_component_base_import_importlib
lf_component_base_import_module = lf_component_base_import_importlib.import_module
import typing as lf_component_base_import_typing
lf_component_base_Any = lf_component_base_import_typing.Any
lf_component_base_Dict = lf_component_base_import_typing.Dict

def lf_component_base__load_attr(module_names: list[str], attr_name: str, fallback: lf_component_base_Any) -> lf_component_base_Any:
    """Load a Langflow class while keeping direct-paste validation friendly."""
    for module_name in module_names:
        try:
            return getattr(lf_component_base_import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback

class lf_component_base__FallbackComponent:
    display_name = ''
    description = ''
    documentation = ''
    icon = ''
    name = ''
    inputs = []
    outputs = []
    status = ''

@lf_component_base_dataclass
class lf_component_base__Input:
    name: str
    display_name: str
    info: str = ''
    value: lf_component_base_Any = None
    tool_mode: bool = False
    advanced: bool = False

@lf_component_base_dataclass
class lf_component_base__FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None

class lf_component_base__FallbackData:

    def __init__(self, data: lf_component_base_Dict[str, lf_component_base_Any] | None=None, text: str | None=None):
        self.data = data or {}
        self.text = text

def lf_component_base__make_input(**kwargs):
    return lf_component_base__Input(**kwargs)

def lf_component_base__build_simple_data(payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):

    @lf_component_base_dataclass
    class SimpleData:
        data: lf_component_base_Dict[str, lf_component_base_Any]
        text: str | None = None
    return SimpleData(data=payload, text=text)
lf_component_base_Component = lf_component_base__load_attr(['lfx.custom.custom_component.component', 'lfx.custom', 'langflow.custom'], 'Component', lf_component_base__FallbackComponent)
lf_component_base_DataInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'DataInput', lf_component_base__make_input)
lf_component_base_MessageInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MessageInput', lf_component_base__make_input)
lf_component_base_MessageTextInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MessageTextInput', lf_component_base__make_input)
lf_component_base_MultilineInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MultilineInput', lf_component_base__make_input)
lf_component_base_SecretStrInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'SecretStrInput', lf_component_base__make_input)
lf_component_base_Output = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'Output', lf_component_base__FallbackOutput)
lf_component_base_Data = lf_component_base__load_attr(['lfx.schema.data', 'lfx.schema', 'langflow.schema'], 'Data', lf_component_base__FallbackData)

def lf_component_base_make_data(payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):
    """Return a Data-like object in both Langflow and local test environments."""
    try:
        return lf_component_base_Data(data=payload, text=text)
    except TypeError:
        try:
            return lf_component_base_Data(payload)
        except Exception:
            return lf_component_base__build_simple_data(payload, text=text)

def lf_component_base_make_branch_data(active: bool, payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):
    """Emit data only for the active branch output."""
    if not active:
        return None
    return lf_component_base_make_data(payload, text=text)

def lf_component_base_read_data_payload(value: lf_component_base_Any) -> lf_component_base_Dict[str, lf_component_base_Any]:
    """Normalize Langflow Data, plain dict, or None into a regular dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, 'data', None)
    if isinstance(data, dict):
        return data
    if hasattr(value, 'dict'):
        try:
            result = value.dict()
            if isinstance(result, dict):
                return result
        except Exception:
            return {}
    return {}

def lf_component_base_read_state_payload(value: lf_component_base_Any) -> lf_component_base_Dict[str, lf_component_base_Any]:
    """Read a Langflow payload and unwrap the nested ``state`` field when present."""
    payload = lf_component_base_read_data_payload(value)
    state = payload.get('state')
    if isinstance(state, dict):
        return state
    return payload if isinstance(payload, dict) else {}

# ---- visible runtime: workflow ----
"""Shared state initializer for standalone Langflow custom components."""
import json as lf_workflow_json
import typing as lf_workflow_import_typing
lf_workflow_Any = lf_workflow_import_typing.Any
lf_workflow_Dict = lf_workflow_import_typing.Dict
lf_workflow_List = lf_workflow_import_typing.List

def lf_workflow__coerce_json_field(value: lf_workflow_Any, default: lf_workflow_Any) -> lf_workflow_Any:
    """Convert JSON-like text input into Python objects for initial state creation."""
    if value is None or value == '':
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return lf_workflow_json.loads(str(value))
    except Exception:
        return default

def lf_workflow_build_initial_state(user_input: str, chat_history: lf_workflow_List[lf_workflow_Dict[str, str]] | str | None=None, context: lf_workflow_Dict[str, lf_workflow_Any] | str | None=None, current_data: lf_workflow_Dict[str, lf_workflow_Any] | str | None=None, domain_rules_text: str | None=None, domain_registry_payload: lf_workflow_Dict[str, lf_workflow_Any] | lf_workflow_List[lf_workflow_Any] | str | None=None) -> lf_workflow_Dict[str, lf_workflow_Any]:
    """Build the shared state contract used across standalone Langflow nodes."""
    return {'user_input': str(user_input or ''), 'chat_history': lf_workflow__coerce_json_field(chat_history, []), 'context': lf_workflow__coerce_json_field(context, {}), 'current_data': lf_workflow__coerce_json_field(current_data, None), 'domain_rules_text': str(domain_rules_text or '').strip(), 'domain_registry_payload': lf_workflow__coerce_json_field(domain_registry_payload, {})}

# ---- node component ----
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

Component = lf_component_base_Component
DataInput = lf_component_base_DataInput
MessageInput = lf_component_base_MessageInput
MessageTextInput = lf_component_base_MessageTextInput
Output = lf_component_base_Output
make_data = lf_component_base_make_data
read_data_payload = lf_component_base_read_data_payload
build_initial_state = lf_workflow_build_initial_state


def append_history(history: List[Dict[str, str]], role: str, content: str) -> List[Dict[str, str]]:
    cleaned = str(content or "").strip()
    if not cleaned:
        return history
    if history and history[-1].get("role") == role and history[-1].get("content") == cleaned:
        return history
    history.append({"role": role, "content": cleaned})
    return history


def read_message_text(message: Any) -> str:
    if message is None:
        return ""
    text = getattr(message, "text", None)
    if text is None and isinstance(message, dict):
        text = message.get("text")
    return str(text or "")


def _coerce_json_field(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def read_domain_text_payload(value: Any) -> str:
    payload = read_data_payload(value)
    text = payload.get("domain_rules_text")
    return str(text or "").strip()


def read_domain_registry_payload(value: Any) -> Dict[str, Any] | List[Any]:
    payload = read_data_payload(value)
    registry_payload = payload.get("domain_registry_payload")
    if isinstance(registry_payload, (dict, list)):
        return registry_payload
    return _coerce_json_field(registry_payload, {})


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
        if role and content:
            normalized.append({"role": role, "content": content})
    return normalized


class SessionMemoryComponent(Component):
    display_name = "Session Memory"
    description = "Load and save multi-turn chat history, context, current data, and domain inputs."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Database"
    name = "session_memory"

    inputs = [
        MessageInput(name="message", display_name="Chat Message", info="Incoming Chat Input message with text and optional session_id"),
        DataInput(name="domain_rules", display_name="Domain Rules", info="Optional free-text domain rules payload"),
        DataInput(name="domain_registry", display_name="Domain Registry", info="Optional registry JSON payload"),
        DataInput(name="result", display_name="Result", info="Merged final result payload to save back into the session"),
        MessageTextInput(name="session_id_override", display_name="Session ID", info="Optional fixed session id.", advanced=True),
        MessageTextInput(name="storage_subdir", display_name="Storage Subdir", value=".langflow_session_store", info="Folder used to persist session JSON files.", advanced=True),
    ]
    outputs = [
        Output(name="state_out", display_name="State", method="session_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="saved_out", display_name="Saved", method="saved_result", group_outputs=True, types=["Data"], selected="Data"),
    ]

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
        base_dir = Path.cwd().resolve()
        subdir = str(getattr(self, "storage_subdir", "") or ".langflow_session_store").strip() or ".langflow_session_store"
        safe_session_id = re.sub(r"[^a-zA-Z0-9._-]", "_", self._resolve_session_id())
        storage_dir = (base_dir / subdir).resolve()
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
                "domain_rules_text": "",
                "domain_registry_payload": {},
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
            "domain_rules_text": str(payload.get("domain_rules_text", "") or "").strip(),
            "domain_registry_payload": payload.get("domain_registry_payload") if isinstance(payload.get("domain_registry_payload"), (dict, list)) else {},
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
        user_input = read_message_text(getattr(self, "message", None))
        if not user_input.strip():
            self.status = "No chat message; session load skipped"
            return None

        snapshot = self._load_snapshot()
        domain_rules_text = read_domain_text_payload(getattr(self, "domain_rules", None)) or snapshot.get("domain_rules_text", "")
        domain_registry_payload = read_domain_registry_payload(getattr(self, "domain_registry", None)) or snapshot.get("domain_registry_payload", {})

        state = build_initial_state(
            user_input=user_input,
            chat_history=snapshot.get("chat_history", []),
            context=snapshot.get("context", {}),
            current_data=snapshot.get("current_data"),
            domain_rules_text=domain_rules_text,
            domain_registry_payload=domain_registry_payload,
        )
        state["session_id"] = snapshot.get("session_id", self._resolve_session_id())
        self.status = f"Session loaded: {state.get('session_id', 'default')}"
        return make_data({"state": state})

    def saved_result(self):
        result_payload = self._unwrap_result_payload(read_data_payload(getattr(self, "result", None)))
        if not result_payload:
            self.status = "No result payload; session save skipped"
            return None

        snapshot = self._load_snapshot()
        history = list(snapshot.get("chat_history", []))
        history = append_history(history, "user", read_message_text(getattr(self, "message", None)))
        history = append_history(history, "assistant", str(result_payload.get("response", "") or ""))

        extracted_params = result_payload.get("extracted_params")
        current_data = result_payload.get("current_data")
        domain_rules_text = read_domain_text_payload(getattr(self, "domain_rules", None)) or snapshot.get("domain_rules_text", "")
        domain_registry_payload = read_domain_registry_payload(getattr(self, "domain_registry", None)) or snapshot.get("domain_registry_payload", {})

        updated_snapshot = {
            "session_id": snapshot.get("session_id", self._resolve_session_id()),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "chat_history": history,
            "context": extracted_params if isinstance(extracted_params, dict) else snapshot.get("context", {}),
            "current_data": current_data if isinstance(current_data, dict) else snapshot.get("current_data"),
            "domain_rules_text": domain_rules_text,
            "domain_registry_payload": domain_registry_payload,
        }

        session_file = self._session_file()
        session_file.write_text(json.dumps(updated_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        self.status = f"Session saved: {updated_snapshot['session_id']}"
        response_text = str(result_payload.get("response", "") or "")
        return make_data(
            {**result_payload, "session_id": updated_snapshot["session_id"], "session_memory_path": str(session_file)},
            text=response_text,
        )
