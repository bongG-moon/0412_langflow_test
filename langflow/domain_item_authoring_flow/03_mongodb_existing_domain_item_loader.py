from __future__ import annotations

import json
import os
from dataclasses import dataclass
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
VALID_GBNS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")


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


def _routes_from_payload(route_value: Any) -> list[str]:
    payload = _payload_from_value(route_value)
    routes = [str(item) for item in _as_list(payload.get("routes")) if str(item) in VALID_GBNS]
    primary = str(payload.get("primary_gbn") or "")
    if primary in VALID_GBNS:
        routes.append(primary)
    return list(dict.fromkeys(routes)) or list(VALID_GBNS)


def _summarize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    summary = {
        "gbn": item.get("gbn"),
        "key": item.get("key"),
        "status": item.get("status"),
        "display_name": payload.get("display_name") or payload.get("name") or item.get("key"),
        "normalized_aliases": item.get("normalized_aliases") if isinstance(item.get("normalized_aliases"), list) else [],
        "normalized_keywords": item.get("normalized_keywords") if isinstance(item.get("normalized_keywords"), list) else [],
    }
    for field in ("aliases", "keywords", "processes", "required_datasets", "formula", "base_dataset", "join_dataset", "join_keys"):
        if payload.get(field) not in (None, "", [], {}):
            summary[field] = payload.get(field)
    return summary


def load_existing_domain_items(route_value: Any = None, db_name_value: Any = None, collection_name_value: Any = None) -> Dict[str, Any]:
    routes = _routes_from_payload(route_value)
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)
    errors: list[str] = []
    items: list[Dict[str, Any]] = []
    try:
        collection = _get_collection(db_name, collection_name)
        cursor = collection.find(
            {"gbn": {"$in": routes}, "status": {"$in": ["active", "review_required"]}},
            {"gbn": 1, "key": 1, "status": 1, "payload": 1, "normalized_aliases": 1, "normalized_keywords": 1},
        ).sort([("gbn", 1), ("key", 1)])
        items = [item for item in cursor if isinstance(item, dict)]
    except Exception as exc:
        errors.append(f"MongoDB existing item load failed: {exc}")

    grouped: Dict[str, list[Dict[str, Any]]] = {gbn: [] for gbn in routes}
    for item in items:
        gbn = str(item.get("gbn") or "")
        if gbn in grouped:
            grouped[gbn].append(_summarize_item(item))

    return {
        "routes": routes,
        "existing_items": grouped,
        "existing_item_count": len(items),
        "mongo_existing_item_status": {
            "database": db_name,
            "collection": collection_name,
            "routes": routes,
            "loaded": not errors,
            "errors": errors,
        },
    }


class MongoDBExistingDomainItemLoader(Component):
    display_name = "MongoDB Existing Domain Item Loader"
    description = "Load existing active/review domain items for the routed gbn values only."
    icon = "Database"
    name = "MongoDBExistingDomainItemLoader"

    inputs = [
        DataInput(name="route_payload", display_name="Route Payload", info="Output from Domain Item Router or Smart Router wrapper.", input_types=["Data", "JSON"]),
        MessageTextInput(name="db_name", display_name="Database Name", info="MongoDB database name.", value=DB_NAME, advanced=True),
        MessageTextInput(name="collection_name", display_name="Collection Name", info="MongoDB domain item collection.", value=DOMAIN_ITEMS_COLLECTION, advanced=True),
    ]

    outputs = [
        Output(name="existing_items", display_name="Existing Items", method="build_existing_items", types=["Data"]),
    ]

    def build_existing_items(self) -> Data:
        return _make_data(
            load_existing_domain_items(
                getattr(self, "route_payload", None),
                getattr(self, "db_name", None),
                getattr(self, "collection_name", None),
            )
        )
