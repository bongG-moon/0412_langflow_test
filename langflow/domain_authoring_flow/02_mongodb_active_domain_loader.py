from __future__ import annotations

import json
import os
from copy import deepcopy
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


def _empty_domain() -> Dict[str, Any]:
    return {
        "products": {},
        "process_groups": {},
        "terms": {},
        "datasets": {},
        "metrics": {},
        "join_rules": [],
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _dedupe_list(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = deepcopy(base)
        for key, value in patch.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(patch, list):
        return _dedupe_list([*base, *patch])
    if patch in (None, "", [], {}):
        return deepcopy(base)
    return deepcopy(patch)


def _normalize_domain(domain: Any) -> Dict[str, Any]:
    normalized = deepcopy(domain) if isinstance(domain, dict) else {}
    for key in ("products", "process_groups", "terms", "datasets", "metrics"):
        if not isinstance(normalized.get(key), dict):
            normalized[key] = {}
    if not isinstance(normalized.get("join_rules"), list):
        normalized["join_rules"] = []
    return normalized


def _patch_from_fragment(fragment: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(fragment.get("domain_patch"), dict):
        return _normalize_domain(fragment["domain_patch"])
    document = fragment.get("domain_document")
    if isinstance(document, dict) and isinstance(document.get("domain"), dict):
        return _normalize_domain(document["domain"])
    if isinstance(fragment.get("domain"), dict):
        return _normalize_domain(fragment["domain"])
    return _empty_domain()


def _merge_fragments(fragments: list[Dict[str, Any]]) -> Dict[str, Any]:
    merged = _empty_domain()
    for fragment in fragments:
        patch = _patch_from_fragment(fragment)
        for key in ("products", "process_groups", "terms", "datasets", "metrics"):
            merged[key] = _deep_merge(merged.get(key, {}), patch.get(key, {}))
        merged["join_rules"] = _dedupe_list([*_as_list(merged.get("join_rules")), *_as_list(patch.get("join_rules"))])
    return merged


def _config_from_value(config_value: Any, domain_id_value: Any = None) -> Dict[str, Any]:
    payload = _payload_from_value(config_value)
    config = payload.get("authoring_config") if isinstance(payload.get("authoring_config"), dict) else payload
    domain_id = str(config.get("domain_id") or domain_id_value or "manufacturing_default").strip()
    metadata = config.get("metadata") if isinstance(config.get("metadata"), dict) else {}
    return {"domain_id": domain_id or "manufacturing_default", "metadata": metadata}


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


def load_active_domain_from_mongodb(
    config_value: Any = None,
    domain_id_value: Any = None,
    db_name_value: Any = None,
    collection_name_value: Any = None,
) -> Dict[str, Any]:
    config = _config_from_value(config_value, domain_id_value)
    domain_id = config["domain_id"]
    errors: list[str] = []
    fragments: list[Dict[str, Any]] = []
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)

    try:
        collection = _get_collection(db_name, collection_name)
        cursor = collection.find(
            {"domain_id": domain_id, "status": "active"},
            {"domain_patch": 1, "metadata": 1, "fragment_id": 1, "created_at": 1},
        ).sort([("created_at", 1), ("_id", 1)])
        fragments = [fragment for fragment in cursor if isinstance(fragment, dict)]
    except Exception as exc:
        errors.append(f"MongoDB active domain load failed: {exc}")

    domain = _merge_fragments(fragments)
    document = {
        "domain_id": domain_id,
        "status": "active",
        "metadata": config["metadata"],
        "domain": domain,
    }
    return {
        "existing_domain_document": document,
        "mongo_domain_load_status": {
            "domain_id": domain_id,
            "database": db_name,
            "collection": collection_name,
            "active_fragment_count": len(fragments),
            "loaded": not errors,
            "errors": errors,
        },
    }


class MongoDBActiveDomainLoader(Component):
    display_name = "MongoDB Active Domain Loader"
    description = "Load active domain fragments from MongoDB and merge them into one existing domain document."
    icon = "Database"
    name = "MongoDBActiveDomainLoader"

    inputs = [
        DataInput(
            name="authoring_config",
            display_name="Authoring Config",
            info="Optional config. Leave disconnected to use manufacturing_default.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
        MessageTextInput(
            name="domain_id",
            display_name="Domain ID",
            info="Optional override. Default is manufacturing_default.",
            value="manufacturing_default",
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
        Output(name="existing_domain", display_name="Existing Domain", method="build_existing_domain", types=["Data"]),
    ]

    def build_existing_domain(self) -> Data:
        return _make_data(
            load_active_domain_from_mongodb(
                getattr(self, "authoring_config", None),
                getattr(self, "domain_id", None),
                getattr(self, "db_name", None),
                getattr(self, "collection_name", None),
            )
        )
