from __future__ import annotations

import hashlib
import json
import os
import uuid
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
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text


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
DOMAIN_FRAGMENTS_COLLECTION = "manufacturing_domain_fragments"
ROOT_KEYS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")


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


def _compact_keys(value: Any) -> Dict[str, list[str]]:
    domain = value if isinstance(value, dict) else {}
    summary: Dict[str, list[str]] = {}
    for key in ("products", "process_groups", "terms", "datasets", "metrics"):
        bucket = domain.get(key)
        summary[key] = list(bucket.keys()) if isinstance(bucket, dict) else []
    rules = domain.get("join_rules")
    summary["join_rules"] = [
        str(rule.get("name") or "") for rule in rules if isinstance(rule, dict) and str(rule.get("name") or "").strip()
    ] if isinstance(rules, list) else []
    return summary


def _first_non_empty_bucket(summary: Dict[str, list[str]]) -> str:
    for bucket, keys in summary.items():
        if keys:
            return f"{bucket}:{keys[0]}"
    return "empty_patch"


def _config_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    config = payload.get("authoring_config") if isinstance(payload.get("authoring_config"), dict) else payload
    metadata = config.get("metadata") if isinstance(config.get("metadata"), dict) else {}
    return {
        "domain_id": str(config.get("domain_id") or "manufacturing_default").strip() or "manufacturing_default",
        "authoring_mode": str(config.get("authoring_mode") or "append").strip().lower() or "append",
        "metadata": metadata,
    }


def _patch_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    patch = payload.get("normalized_domain_patch") if isinstance(payload.get("normalized_domain_patch"), dict) else {}
    if not patch and isinstance(payload.get("domain_patch"), dict):
        patch = payload["domain_patch"]
    return deepcopy(patch) if isinstance(patch, dict) else {}


def _decision_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    decision = payload.get("save_decision") if isinstance(payload.get("save_decision"), dict) else payload
    return decision if isinstance(decision, dict) else {}


def _validation_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    return validation


def _resolve_db_name(value: Any = None) -> str:
    return str(value or os.getenv("MONGO_DB_NAME") or DB_NAME).strip() or DB_NAME


def _resolve_collection_name(value: Any = None) -> str:
    return str(value or os.getenv("MONGO_DOMAIN_FRAGMENTS_COLLECTION") or DOMAIN_FRAGMENTS_COLLECTION).strip() or DOMAIN_FRAGMENTS_COLLECTION


def _get_collection(db_name_value: Any = None, collection_name_value: Any = None) -> Any:
    try:
        mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
    except Exception as exc:
        raise RuntimeError(f"pymongo import failed: {exc}") from exc
    mongo_uri = os.getenv("MONGO_URI") or MONGO_URI
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)
    client = mongo_client_cls(mongo_uri, serverSelectionTimeoutMS=5000)
    return client[db_name][collection_name]


def build_domain_fragment_document(
    patch_value: Any,
    save_decision_value: Any,
    validated_value: Any = None,
    authoring_config_value: Any = None,
) -> Dict[str, Any]:
    patch = _patch_from_value(patch_value)
    decision = _decision_from_value(save_decision_value)
    validation = _validation_from_value(validated_value)
    config = _config_from_value(authoring_config_value)
    now = datetime.now(timezone.utc).isoformat()
    patch_summary = _compact_keys(patch)
    patch_hash = hashlib.sha256(json.dumps(patch, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    fragment_id = f"{config['domain_id']}_{patch_hash[:12]}_{uuid.uuid4().hex[:8]}"
    status = str(decision.get("target_status") or "active").strip() or "active"

    return {
        "domain_id": config["domain_id"],
        "fragment_id": fragment_id,
        "status": status,
        "title": _first_non_empty_bucket(patch_summary),
        "domain_patch": patch,
        "patch_summary": patch_summary,
        "patch_hash": patch_hash,
        "validation": validation,
        "save_decision": decision,
        "metadata": config["metadata"],
        "authoring_mode": config["authoring_mode"],
        "created_at": now,
        "updated_at": now,
    }


def save_domain_fragment_to_mongodb(
    patch_value: Any,
    save_decision_value: Any,
    validated_value: Any = None,
    authoring_config_value: Any = None,
    db_name_value: Any = None,
    collection_name_value: Any = None,
) -> Dict[str, Any]:
    decision = _decision_from_value(save_decision_value)
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)
    should_save = bool(decision.get("should_save"))
    document = build_domain_fragment_document(patch_value, save_decision_value, validated_value, authoring_config_value)
    if not should_save:
        return {
            "saved_fragment": {
                "saved": False,
                "domain_id": document["domain_id"],
                "fragment_id": document["fragment_id"],
                "status": document["status"],
                "database": db_name,
                "collection": collection_name,
                "reason": decision.get("reason") or "save_decision.should_save is false",
            }
        }

    try:
        collection = _get_collection(db_name, collection_name)
        collection.create_index([("domain_id", 1), ("status", 1), ("created_at", 1)])
        collection.create_index([("domain_id", 1), ("patch_hash", 1)])
        set_payload = deepcopy(document)
        set_payload.pop("created_at", None)
        set_payload.pop("fragment_id", None)
        result = collection.update_one(
            {"domain_id": document["domain_id"], "patch_hash": document["patch_hash"]},
            {
                "$set": set_payload,
                "$setOnInsert": {
                    "created_at": document["created_at"],
                    "fragment_id": document["fragment_id"],
                },
            },
            upsert=True,
        )
        upserted_id = str(result.upserted_id) if result.upserted_id else ""
        stored = collection.find_one(
            {"domain_id": document["domain_id"], "patch_hash": document["patch_hash"]},
            {"fragment_id": 1},
        )
        stored_fragment_id = str(stored.get("fragment_id") or document["fragment_id"]) if isinstance(stored, dict) else document["fragment_id"]
        saved = True
        error = ""
    except Exception as exc:
        upserted_id = ""
        result = None
        stored_fragment_id = document["fragment_id"]
        saved = False
        error = str(exc)

    return {
        "saved_fragment": {
            "saved": saved,
            "domain_id": document["domain_id"],
            "fragment_id": stored_fragment_id,
            "status": document["status"],
            "database": db_name,
            "collection": collection_name,
            "upserted_id": upserted_id,
            "matched_count": int(result.matched_count) if result is not None else 0,
            "modified_count": int(result.modified_count) if result is not None else 0,
            "error": error,
            "used_in_main_flow": document["status"] == "active" and saved,
        }
    }


class MongoDBDomainFragmentSaver(Component):
    display_name = "MongoDB Domain Fragment Saver"
    description = "Save the normalized domain patch as a MongoDB fragment after conflict and schema validation."
    icon = "DatabaseZap"
    name = "MongoDBDomainFragmentSaver"

    inputs = [
        DataInput(name="normalized_domain_patch", display_name="Normalized Domain Patch", info="Output from Normalize Domain Patch.", input_types=["Data", "JSON"]),
        DataInput(name="save_decision", display_name="Save Decision", info="Output from Domain Save Decision.", input_types=["Data", "JSON"]),
        DataInput(name="validated_domain", display_name="Validated Domain", info="Output from Domain Schema Validator.", input_types=["Data", "JSON"]),
        DataInput(
            name="authoring_config",
            display_name="Authoring Config",
            info="Optional config. Leave disconnected to use manufacturing_default.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
        MessageTextInput(
            name="db_name",
            display_name="Database Name",
            info="MongoDB database name. Default is datagov.",
            value=DB_NAME,
            advanced=True,
        ),
        MessageTextInput(
            name="collection_name",
            display_name="Collection Name",
            info="MongoDB collection for domain fragments.",
            value=DOMAIN_FRAGMENTS_COLLECTION,
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="saved_fragment", display_name="Saved Fragment", method="save_fragment", types=["Data"]),
    ]

    def save_fragment(self) -> Data:
        return _make_data(
            save_domain_fragment_to_mongodb(
                getattr(self, "normalized_domain_patch", None),
                getattr(self, "save_decision", None),
                getattr(self, "validated_domain", None),
                getattr(self, "authoring_config", None),
                getattr(self, "db_name", None),
                getattr(self, "collection_name", None),
            )
        )
