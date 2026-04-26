from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Dict

from .config import DEFAULT_DB_NAME, DOMAIN_ITEMS_COLLECTION, MONGO_URI, TABLE_CATALOG_ITEMS_COLLECTION


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _client(mongo_uri: str | None = None) -> Any:
    uri = str(mongo_uri if mongo_uri is not None else MONGO_URI).strip()
    if not uri:
        raise ValueError("Mongo URI is empty.")
    mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
    return mongo_client_cls(uri, serverSelectionTimeoutMS=5000)


def ping(mongo_uri: str | None = None, db_name: str = DEFAULT_DB_NAME) -> Dict[str, Any]:
    client = None
    try:
        client = _client(mongo_uri)
        client[db_name].command("ping")
        return {"ok": True, "message": f"Connected to {db_name}."}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
    finally:
        if client is not None:
            client.close()


def _list(collection_name: str, db_name: str, status: str, mongo_uri: str | None) -> list[Dict[str, Any]]:
    client = None
    try:
        client = _client(mongo_uri)
        query = {} if status == "all" else {"status": status}
        docs = list(client[db_name][collection_name].find(query, {"_id": 0}).sort([("gbn", 1), ("key", 1), ("dataset_key", 1)]))
        return [dict(doc) for doc in docs]
    finally:
        if client is not None:
            client.close()


def list_domain_items(
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    status: str = "active",
    mongo_uri: str | None = None,
) -> list[Dict[str, Any]]:
    return _list(collection_name, db_name, status, mongo_uri)


def list_table_items(
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    status: str = "active",
    mongo_uri: str | None = None,
) -> list[Dict[str, Any]]:
    return _list(collection_name, db_name, status, mongo_uri)


def save_domain_items(
    items: list[Dict[str, Any]],
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    client = None
    errors: list[str] = []
    saved_count = 0
    try:
        client = _client(mongo_uri)
        collection = client[db_name][collection_name]
        for item in items:
            gbn = str(item.get("gbn") or "").strip()
            key = str(item.get("key") or "").strip()
            if not gbn or not key:
                errors.append(f"Skipped item without gbn/key: {item}")
                continue
            doc = deepcopy(item)
            now = _utc_now()
            existing = collection.find_one({"gbn": gbn, "key": key}, {"_id": 0})
            doc["created_at"] = existing.get("created_at", now) if isinstance(existing, dict) else now
            doc["updated_at"] = now
            collection.replace_one({"gbn": gbn, "key": key}, doc, upsert=True)
            saved_count += 1
        return {"saved": saved_count > 0 and not errors, "saved_count": saved_count, "errors": errors}
    except Exception as exc:
        return {"saved": False, "saved_count": saved_count, "errors": [str(exc), *errors]}
    finally:
        if client is not None:
            client.close()


def save_table_items(
    items: list[Dict[str, Any]],
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    client = None
    errors: list[str] = []
    saved_count = 0
    try:
        client = _client(mongo_uri)
        collection = client[db_name][collection_name]
        for item in items:
            dataset_key = str(item.get("dataset_key") or "").strip()
            if not dataset_key:
                errors.append(f"Skipped table item without dataset_key: {item}")
                continue
            doc = deepcopy(item)
            now = _utc_now()
            existing = collection.find_one({"dataset_key": dataset_key}, {"_id": 0})
            doc["created_at"] = existing.get("created_at", now) if isinstance(existing, dict) else now
            doc["updated_at"] = now
            collection.replace_one({"dataset_key": dataset_key}, doc, upsert=True)
            saved_count += 1
        return {"saved": saved_count > 0 and not errors, "saved_count": saved_count, "errors": errors}
    except Exception as exc:
        return {"saved": False, "saved_count": saved_count, "errors": [str(exc), *errors]}
    finally:
        if client is not None:
            client.close()


def soft_delete_domain_item(
    gbn: str,
    key: str,
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    client = None
    try:
        client = _client(mongo_uri)
        result = client[db_name][collection_name].update_one({"gbn": gbn, "key": key}, {"$set": {"status": "deleted", "updated_at": _utc_now()}})
        return {"deleted": result.modified_count > 0}
    finally:
        if client is not None:
            client.close()


def soft_delete_table_item(
    dataset_key: str,
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    client = None
    try:
        client = _client(mongo_uri)
        result = client[db_name][collection_name].update_one({"dataset_key": dataset_key}, {"$set": {"status": "deleted", "updated_at": _utc_now()}})
        return {"deleted": result.modified_count > 0}
    finally:
        if client is not None:
            client.close()
