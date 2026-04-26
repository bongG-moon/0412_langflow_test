from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, MultilineInput, Output
from lfx.schema.data import Data

DEFAULT_COLLECTION = "manufacturing_agent_data_refs"

def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return deepcopy(data)
    text = getattr(value, "text", None) or getattr(value, "content", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"", "0", "false", "no", "off", "none", "null"}


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return str(value)


def _rows_columns(rows: list[Dict[str, Any]]) -> list[str]:
    return [str(key) for key in rows[0].keys()] if rows and isinstance(rows[0], dict) else []


def _is_row_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(row, dict) for row in value)


def _find_session_id(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("session_id"):
            return str(value["session_id"])
        for key in ("state", "current_data", "analysis_result", "retrieval_payload"):
            nested = value.get(key)
            session_id = _find_session_id(nested)
            if session_id:
                return session_id
        for nested in value.values():
            session_id = _find_session_id(nested)
            if session_id:
                return session_id
    if isinstance(value, list):
        for item in value:
            session_id = _find_session_id(item)
            if session_id:
                return session_id
    return ""


def _connect_collection(mongo_uri: str, db_name: str, collection_name: str) -> tuple[Any, Any]:
    mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
    client = mongo_client_cls(mongo_uri, serverSelectionTimeoutMS=5000)
    return client, client[db_name][collection_name]


def _store_rows(collection: Any, rows: list[Dict[str, Any]], session_id: str, path: str, db_name: str, collection_name: str) -> Dict[str, Any]:
    ref_id = uuid.uuid4().hex
    safe_rows = _json_safe(rows)
    doc = {
        "ref_id": ref_id,
        "session_id": session_id or "default",
        "path": path,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "columns": _rows_columns(rows),
        "rows": safe_rows,
    }
    collection.replace_one({"ref_id": ref_id}, doc, upsert=True)
    return {
        "store": "mongodb",
        "ref_id": ref_id,
        "db_name": db_name,
        "collection_name": collection_name,
        "row_count": len(rows),
        "columns": _rows_columns(rows),
        "path": path,
    }


def _compact_with_refs(value: Any, collection: Any, session_id: str, db_name: str, collection_name: str, preview_limit: int, min_rows: int, path: str, refs: list[Dict[str, Any]]) -> Any:
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        already_ref = isinstance(value.get("data_ref"), dict)
        for key, item in value.items():
            current_path = f"{path}.{key}" if path else key
            if key == "data" and not already_ref and _is_row_list(item) and len(item) >= min_rows:
                data_ref = _store_rows(collection, item, session_id, current_path, db_name, collection_name)
                refs.append(data_ref)
                result["data"] = deepcopy(item[:preview_limit])
                result["data_ref"] = data_ref
                result["data_is_reference"] = True
                result["data_is_preview"] = len(item) > preview_limit
                result["row_count"] = len(item)
                continue
            result[key] = _compact_with_refs(item, collection, session_id, db_name, collection_name, preview_limit, min_rows, current_path, refs)
        return result
    if isinstance(value, list):
        return [_compact_with_refs(item, collection, session_id, db_name, collection_name, preview_limit, min_rows, f"{path}[{index}]", refs) for index, item in enumerate(value)]
    return value


def store_payload_in_mongo(payload_value: Any, mongo_uri_value: Any = "", db_name_value: Any = "datagov", collection_name_value: Any = DEFAULT_COLLECTION, enabled_value: Any = "true", preview_row_limit_value: Any = "20", min_rows_value: Any = "1") -> Dict[str, Any]:
    payload = _payload_from_value(payload_value)
    if not payload:
        return {"mongo_data_store": {"enabled": False, "stored": False, "ref_count": 0, "errors": ["empty payload"]}}

    try:
        preview_limit = max(0, int(preview_row_limit_value or 20))
    except Exception:
        preview_limit = 20
    try:
        min_rows = max(1, int(min_rows_value or 1))
    except Exception:
        min_rows = 1

    if not _truthy(enabled_value):
        return {**payload, "mongo_data_store": {"enabled": False, "stored": False, "ref_count": 0, "errors": []}}

    mongo_uri = str(mongo_uri_value or "").strip()
    db_name = str(db_name_value or "datagov").strip() or "datagov"
    collection_name = str(collection_name_value or DEFAULT_COLLECTION).strip() or DEFAULT_COLLECTION
    if not mongo_uri:
        return {**payload, "mongo_data_store": {"enabled": True, "stored": False, "ref_count": 0, "errors": ["Mongo URI is empty."]}}

    client = None
    refs: list[Dict[str, Any]] = []
    try:
        client, collection = _connect_collection(mongo_uri, db_name, collection_name)
        session_id = _find_session_id(payload) or "default"
        compacted = _compact_with_refs(payload, collection, session_id, db_name, collection_name, preview_limit, min_rows, "", refs)
        compacted["mongo_data_refs"] = refs
        compacted["mongo_data_store"] = {"enabled": True, "stored": bool(refs), "ref_count": len(refs), "errors": []}
        return compacted
    except Exception as exc:
        return {**payload, "mongo_data_store": {"enabled": True, "stored": False, "ref_count": 0, "errors": [str(exc)]}}
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


class MongoDBDataStore(Component):
    display_name = "MongoDB Data Store"
    description = "Store large row lists in MongoDB and keep compact data_ref pointers in the flow payload."
    icon = "Database"
    name = "MongoDBDataStore"

    inputs = [
        DataInput(name="payload", display_name="Payload", info="Any row-bearing payload, usually Analysis Result Merger.analysis_result.", input_types=["Data", "JSON"]),
        MultilineInput(name="mongo_uri", display_name="Mongo URI", value="", info="MongoDB URI for storing row data references."),
        MessageTextInput(name="db_name", display_name="Database Name", value="datagov"),
        MessageTextInput(name="collection_name", display_name="Collection Name", value=DEFAULT_COLLECTION),
        MessageTextInput(name="enabled", display_name="Enabled", value="true", advanced=True),
        MessageTextInput(name="preview_row_limit", display_name="Preview Row Limit", value="20", advanced=True),
        MessageTextInput(name="min_rows", display_name="Min Rows To Store", value="1", advanced=True),
    ]
    outputs = [Output(name="stored_payload", display_name="Stored Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = store_payload_in_mongo(
            getattr(self, "payload", None),
            getattr(self, "mongo_uri", ""),
            getattr(self, "db_name", "datagov"),
            getattr(self, "collection_name", DEFAULT_COLLECTION),
            getattr(self, "enabled", "true"),
            getattr(self, "preview_row_limit", "20"),
            getattr(self, "min_rows", "1"),
        )
        meta = payload.get("mongo_data_store", {}) if isinstance(payload, dict) else {}
        self.status = {"stored": meta.get("stored", False), "ref_count": meta.get("ref_count", 0), "errors": len(meta.get("errors", [])) if isinstance(meta.get("errors"), list) else 0}
        return _make_data(payload)

