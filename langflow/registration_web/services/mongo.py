from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from .config import (
    DEFAULT_DB_NAME,
    DOMAIN_ITEMS_COLLECTION,
    MONGO_URI,
    TABLE_CATALOG_ITEMS_COLLECTION,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _string_id(document: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(document)
    if "_id" in item:
        item["_id"] = str(item["_id"])
    return item


def get_client(mongo_uri: str | None = None) -> Any:
    try:
        from pymongo import MongoClient
    except Exception as exc:
        raise RuntimeError("pymongo is required for MongoDB registration features.") from exc
    return MongoClient(str(mongo_uri or MONGO_URI), serverSelectionTimeoutMS=5000)


def get_collection(
    collection_name: str,
    db_name: str | None = None,
    mongo_uri: str | None = None,
) -> Any:
    client = get_client(mongo_uri)
    return client[str(db_name or DEFAULT_DB_NAME)][collection_name]


def test_connection(db_name: str, mongo_uri: str | None = None) -> Dict[str, Any]:
    try:
        client = get_client(mongo_uri)
        client.admin.command("ping")
        return {"ok": True, "database": db_name, "message": "MongoDB connection is available."}
    except Exception as exc:
        return {"ok": False, "database": db_name, "message": str(exc)}


def list_domain_items(
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    status: str | None = None,
    mongo_uri: str | None = None,
) -> list[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if status and status != "all":
        query["status"] = status
    collection = get_collection(collection_name, db_name, mongo_uri)
    cursor = collection.find(query).sort([("gbn", 1), ("key", 1)])
    return [_string_id(item) for item in cursor if isinstance(item, dict)]


def list_table_items(
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    status: str | None = None,
    mongo_uri: str | None = None,
) -> list[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if status and status != "all":
        query["status"] = status
    collection = get_collection(collection_name, db_name, mongo_uri)
    cursor = collection.find(query).sort([("dataset_key", 1)])
    return [_string_id(item) for item in cursor if isinstance(item, dict)]


def soft_delete_domain_item(
    gbn: str,
    key: str,
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    collection = get_collection(collection_name, db_name, mongo_uri)
    now = _utc_now()
    result = collection.update_one(
        {"gbn": str(gbn), "key": str(key)},
        {"$set": {"status": "deleted", "deleted_at": now, "updated_at": now}},
    )
    return {
        "deleted": result.matched_count > 0,
        "matched_count": int(result.matched_count),
        "modified_count": int(result.modified_count),
        "gbn": str(gbn),
        "key": str(key),
    }


def soft_delete_table_item(
    dataset_key: str,
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    collection = get_collection(collection_name, db_name, mongo_uri)
    now = _utc_now()
    result = collection.update_one(
        {"dataset_key": str(dataset_key)},
        {"$set": {"status": "deleted", "deleted_at": now, "updated_at": now}},
    )
    return {
        "deleted": result.matched_count > 0,
        "matched_count": int(result.matched_count),
        "modified_count": int(result.modified_count),
        "dataset_key": str(dataset_key),
    }


def prepare_domain_indexes(collection: Any) -> None:
    collection.create_index([("gbn", 1), ("key", 1)], unique=True)
    collection.create_index([("status", 1), ("gbn", 1)])
    collection.create_index([("normalized_aliases", 1)])
    collection.create_index([("normalized_keywords", 1)])


def save_domain_items(
    items: Iterable[Dict[str, Any]],
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    collection = get_collection(collection_name, db_name, mongo_uri)
    prepare_domain_indexes(collection)
    now = _utc_now()
    results: list[Dict[str, Any]] = []
    errors: list[str] = []

    for item in items:
        document = deepcopy(item)
        gbn = str(document.get("gbn") or "").strip()
        key = str(document.get("key") or "").strip()
        if not gbn or not key:
            errors.append(f"Skipped item without gbn/key: {document}")
            continue
        document["gbn"] = gbn
        document["key"] = key
        document["status"] = str(document.get("status") or "active")
        document["updated_at"] = now
        try:
            result = collection.update_one(
                {"gbn": gbn, "key": key},
                {"$set": document, "$setOnInsert": {"created_at": now}},
                upsert=True,
            )
            results.append(
                {
                    "gbn": gbn,
                    "key": key,
                    "status": document["status"],
                    "upserted_id": str(result.upserted_id) if result.upserted_id else "",
                    "matched_count": int(result.matched_count),
                    "modified_count": int(result.modified_count),
                }
            )
        except Exception as exc:
            errors.append(f"{gbn}:{key}: {exc}")

    return {
        "saved": not errors,
        "database": db_name,
        "collection": collection_name,
        "saved_count": len(results),
        "items": results,
        "errors": errors,
    }


def prepare_table_indexes(collection: Any) -> None:
    collection.create_index([("dataset_key", 1)], unique=True)
    collection.create_index([("status", 1)])
    collection.create_index([("keywords", 1)])
    collection.create_index([("tool_name", 1)])


def save_table_catalog(
    table_catalog: Dict[str, Any],
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    collection = get_collection(collection_name, db_name, mongo_uri)
    prepare_table_indexes(collection)
    now = _utc_now()
    results: list[Dict[str, Any]] = []
    errors: list[str] = []

    for dataset_key, dataset in datasets.items():
        if not isinstance(dataset, dict):
            errors.append(f"{dataset_key}: dataset must be an object.")
            continue
        document = deepcopy(dataset)
        document["dataset_key"] = str(dataset_key)
        document["status"] = str(document.get("status") or table_catalog.get("status") or "active")
        document["updated_at"] = now
        try:
            result = collection.update_one(
                {"dataset_key": str(dataset_key)},
                {"$set": document, "$setOnInsert": {"created_at": now}},
                upsert=True,
            )
            results.append(
                {
                    "dataset_key": str(dataset_key),
                    "status": document["status"],
                    "upserted_id": str(result.upserted_id) if result.upserted_id else "",
                    "matched_count": int(result.matched_count),
                    "modified_count": int(result.modified_count),
                }
            )
        except Exception as exc:
            errors.append(f"{dataset_key}: {exc}")

    return {
        "saved": not errors,
        "database": db_name,
        "collection": collection_name,
        "saved_count": len(results),
        "items": results,
        "errors": errors,
    }
