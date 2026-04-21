from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# Compatibility scaffolding for local tests. In lfx Langflow this can be
# replaced with direct imports from lfx.custom, lfx.io, and lfx.schema.
def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback


class _FallbackComponent:
    display_name = ""
    description = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""


@dataclass
class _FallbackInput:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    advanced: bool = False
    tool_mode: bool = False
    input_types: list[str] | None = None


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


MONGO_URI = "mongodb+srv://bonggeon:qhdrjs123@datagov.5qcxapn.mongodb.net/?retryWrites=true&w=majority&appName=datagov"
DB_NAME = "datagov"
DOMAIN_ITEMS_COLLECTION = "manufacturing_domain_items"


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    text = getattr(value, "text", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _resolve_db_name(value: Any = None) -> str:
    return str(value or os.getenv("MONGO_DB_NAME") or DB_NAME).strip() or DB_NAME


def _resolve_collection_name(value: Any = None) -> str:
    return str(value or os.getenv("MONGO_DOMAIN_ITEMS_COLLECTION") or DOMAIN_ITEMS_COLLECTION).strip() or DOMAIN_ITEMS_COLLECTION


def _get_collection(db_name_value: Any = None, collection_name_value: Any = None) -> Any:
    try:
        mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
    except Exception as exc:
        raise RuntimeError(f"pymongo import failed: {exc}") from exc
    mongo_uri = os.getenv("MONGO_URI") or MONGO_URI
    client = mongo_client_cls(mongo_uri, serverSelectionTimeoutMS=5000)
    return client[_resolve_db_name(db_name_value)][_resolve_collection_name(collection_name_value)]


def _status_by_identity(conflict_payload: Dict[str, Any]) -> Dict[str, str]:
    report = conflict_payload.get("conflict_report") if isinstance(conflict_payload.get("conflict_report"), dict) else {}
    result: Dict[str, str] = {}
    for item in _as_list(report.get("item_results")):
        if not isinstance(item, dict):
            continue
        identity = f"{item.get('gbn')}:{item.get('key')}"
        result[identity] = str(item.get("recommended_status") or "active")
    return result


def save_domain_items(conflict_value: Any, db_name_value: Any = None, collection_name_value: Any = None) -> Dict[str, Any]:
    conflict_payload = _payload_from_value(conflict_value)
    items = [item for item in _as_list(conflict_payload.get("normalized_domain_items")) if isinstance(item, dict)]
    status_by_identity = _status_by_identity(conflict_payload)
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)
    now = datetime.now(timezone.utc).isoformat()
    results: list[Dict[str, Any]] = []
    errors: list[str] = []
    try:
        collection = _get_collection(db_name, collection_name)
        collection.create_index([("gbn", 1), ("key", 1)], unique=True)
        collection.create_index([("status", 1), ("gbn", 1)])
        collection.create_index([("normalized_aliases", 1)])
        collection.create_index([("normalized_keywords", 1)])
    except Exception as exc:
        return {
            "saved_items": [],
            "save_status": {
                "saved": False,
                "database": db_name,
                "collection": collection_name,
                "saved_count": 0,
                "errors": [f"MongoDB item collection prepare failed: {exc}"],
            },
        }

    for item in items:
        document = deepcopy(item)
        identity = f"{document.get('gbn')}:{document.get('key')}"
        document["status"] = status_by_identity.get(identity, document.get("status") or "active")
        document["updated_at"] = now
        try:
            result = collection.update_one(
                {"gbn": document["gbn"], "key": document["key"]},
                {
                    "$set": document,
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
            results.append(
                {
                    "gbn": document["gbn"],
                    "key": document["key"],
                    "status": document["status"],
                    "upserted_id": str(result.upserted_id) if result.upserted_id else "",
                    "matched_count": int(result.matched_count),
                    "modified_count": int(result.modified_count),
                    "used_in_main_flow": document["status"] == "active",
                }
            )
        except Exception as exc:
            errors.append(f"{identity}: {exc}")

    return {
        "saved_items": results,
        "save_status": {
            "saved": not errors,
            "database": db_name,
            "collection": collection_name,
            "saved_count": len(results),
            "errors": errors,
        },
    }


class MongoDBDomainItemSaver(Component):
    display_name = "MongoDB Domain Item Saver"
    description = "Save normalized domain items one-by-one for web-friendly domain management."
    icon = "DatabaseZap"
    name = "MongoDBDomainItemSaver"

    inputs = [
        DataInput(name="conflict_report", display_name="Conflict Report", info="Output from Domain Item Conflict Checker.", input_types=["Data", "JSON"]),
        MessageTextInput(name="db_name", display_name="Database Name", info="MongoDB database name.", value=DB_NAME, advanced=True),
        MessageTextInput(name="collection_name", display_name="Collection Name", info="MongoDB domain item collection.", value=DOMAIN_ITEMS_COLLECTION, advanced=True),
    ]

    outputs = [
        Output(name="saved_items", display_name="Saved Items", method="save_items", types=["Data"]),
    ]

    def save_items(self) -> Data:
        return _make_data(
            save_domain_items(
                getattr(self, "conflict_report", None),
                getattr(self, "db_name", None),
                getattr(self, "collection_name", None),
            )
        )
