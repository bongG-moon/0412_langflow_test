from __future__ import annotations

import json
import os
import re
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
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


MONGO_URI = "mongodb+srv://bonggeon:qhdrjs123@datagov.5qcxapn.mongodb.net/?retryWrites=true&w=majority&appName=datagov"
DB_NAME = "datagov"
DOMAIN_FRAGMENTS_COLLECTION = "manufacturing_domain_fragments"
VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _empty_domain() -> Dict[str, Any]:
    return {
        "products": {},
        "process_groups": {},
        "terms": {},
        "datasets": {},
        "metrics": {},
        "join_rules": [],
    }


def _normalize_alias(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


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


def _add_alias(index: Dict[str, Dict[str, str]], bucket: str, alias: Any, key: str, errors: list[str]) -> None:
    normalized = _normalize_alias(alias)
    if not normalized:
        return
    existing = index[bucket].get(normalized)
    if existing and existing != key:
        errors.append(f"Alias collision in {bucket}: '{alias}' maps to '{existing}' and '{key}'.")
        return
    index[bucket][normalized] = key


def _normalize_loaded_domain(domain: Dict[str, Any], errors: list[str]) -> Dict[str, Any]:
    domain = _normalize_domain(domain)
    for dataset_key, dataset in list(domain["datasets"].items()):
        if not isinstance(dataset, dict):
            errors.append(f"Dataset '{dataset_key}' must be an object; skipped.")
            domain["datasets"].pop(dataset_key, None)
            continue
        dataset.setdefault("display_name", dataset_key)
        dataset["keywords"] = [str(item) for item in _as_list(dataset.get("keywords")) if str(item).strip()]
        dataset["required_params"] = [
            str(item) for item in _as_list(dataset.get("required_params")) if str(item).strip()
        ]
        columns = []
        for column in _as_list(dataset.get("columns")):
            if not isinstance(column, dict) or not column.get("name"):
                errors.append(f"Dataset '{dataset_key}' has a column without a name; skipped.")
                continue
            item = dict(column)
            item.setdefault("type", "string")
            if item["type"] not in VALID_COLUMN_TYPES:
                errors.append(f"Dataset '{dataset_key}' column '{item['name']}' has unknown type '{item['type']}'.")
            columns.append(item)
        dataset["columns"] = columns

    for metric_key, metric in list(domain["metrics"].items()):
        if not isinstance(metric, dict):
            errors.append(f"Metric '{metric_key}' must be an object; skipped.")
            domain["metrics"].pop(metric_key, None)
            continue
        metric.setdefault("display_name", metric_key)
        metric["aliases"] = [str(item) for item in _as_list(metric.get("aliases")) if str(item).strip()]
        metric["required_datasets"] = [
            str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip()
        ]
    return domain


def _build_domain_index(domain: Dict[str, Any], errors: list[str]) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {
        "term_alias_to_key": {},
        "product_alias_to_key": {},
        "process_alias_to_group": {},
        "metric_alias_to_key": {},
        "dataset_keyword_to_key": {},
    }

    for key, product in domain.get("products", {}).items():
        _add_alias(index, "product_alias_to_key", key, key, errors)
        if isinstance(product, dict):
            _add_alias(index, "product_alias_to_key", product.get("display_name"), key, errors)
            for alias in _as_list(product.get("aliases")):
                _add_alias(index, "product_alias_to_key", alias, key, errors)

    for key, group in domain.get("process_groups", {}).items():
        _add_alias(index, "process_alias_to_group", key, key, errors)
        if isinstance(group, dict):
            _add_alias(index, "process_alias_to_group", group.get("display_name"), key, errors)
            for alias in _as_list(group.get("aliases")):
                _add_alias(index, "process_alias_to_group", alias, key, errors)
            for process in _as_list(group.get("processes")):
                _add_alias(index, "process_alias_to_group", process, key, errors)

    for key, term in domain.get("terms", {}).items():
        _add_alias(index, "term_alias_to_key", key, key, errors)
        if isinstance(term, dict):
            _add_alias(index, "term_alias_to_key", term.get("display_name"), key, errors)
            for alias in _as_list(term.get("aliases")):
                _add_alias(index, "term_alias_to_key", alias, key, errors)

    for key, metric in domain.get("metrics", {}).items():
        _add_alias(index, "metric_alias_to_key", key, key, errors)
        if isinstance(metric, dict):
            _add_alias(index, "metric_alias_to_key", metric.get("display_name"), key, errors)
            for alias in _as_list(metric.get("aliases")):
                _add_alias(index, "metric_alias_to_key", alias, key, errors)

    for key, dataset in domain.get("datasets", {}).items():
        _add_alias(index, "dataset_keyword_to_key", key, key, errors)
        if isinstance(dataset, dict):
            _add_alias(index, "dataset_keyword_to_key", dataset.get("display_name"), key, errors)
            for keyword in _as_list(dataset.get("keywords")):
                _add_alias(index, "dataset_keyword_to_key", keyword, key, errors)

    return index


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


def load_mongodb_domain_payload(
    domain_id_value: Any = None,
    db_name_value: Any = None,
    collection_name_value: Any = None,
) -> Dict[str, Any]:
    domain_id = str(domain_id_value or "manufacturing_default").strip() or "manufacturing_default"
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)
    errors: list[str] = []
    load_errors: list[str] = []
    fragments: list[Dict[str, Any]] = []
    try:
        collection = _get_collection(db_name, collection_name)
        cursor = collection.find(
            {"domain_id": domain_id, "status": "active"},
            {"domain_patch": 1, "fragment_id": 1, "created_at": 1},
        ).sort([("created_at", 1), ("_id", 1)])
        fragments = [fragment for fragment in cursor if isinstance(fragment, dict)]
    except Exception as exc:
        message = f"MongoDB domain load failed: {exc}"
        errors.append(message)
        load_errors.append(message)
    if not load_errors and not fragments:
        message = (
            f"No active domain fragments found for domain_id='{domain_id}' "
            f"in {db_name}.{collection_name}."
        )
        errors.append(message)
        load_errors.append(message)

    domain = _normalize_loaded_domain(_merge_fragments(fragments), errors)
    document = {
        "domain_id": domain_id,
        "status": "active",
        "metadata": {},
        "domain": domain,
    }
    domain_index = _build_domain_index(domain, errors)
    return {
        "domain_document": document,
        "domain": domain,
        "domain_index": domain_index,
        "domain_errors": errors,
        "mongo_domain_load_status": {
            "domain_id": domain_id,
            "database": db_name,
            "collection": collection_name,
            "active_fragment_count": len(fragments),
            "loaded": not load_errors and bool(fragments),
            "errors": load_errors,
            "domain_error_count": len(errors),
            "source": "mongodb_domain_fragments",
        },
    }


class MongoDBDomainPayloadLoader(Component):
    display_name = "MongoDB Domain Payload Loader"
    description = "Load active MongoDB domain fragments and return the domain_payload used by the data answer flow."
    icon = "Database"
    name = "MongoDBDomainPayloadLoader"

    inputs = [
        MessageTextInput(
            name="domain_id",
            display_name="Domain ID",
            info="Optional. Default is manufacturing_default.",
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
        Output(name="domain_payload", display_name="Domain Payload", method="build_domain_payload", types=["Data"]),
    ]

    def build_domain_payload(self) -> Data:
        return _make_data(
            load_mongodb_domain_payload(
                getattr(self, "domain_id", None),
                getattr(self, "db_name", None),
                getattr(self, "collection_name", None),
            )
        )
