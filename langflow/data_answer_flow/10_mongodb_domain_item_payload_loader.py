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
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


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
DOMAIN_ITEMS_COLLECTION = "manufacturing_domain_items"
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


def _add_alias(index: Dict[str, Dict[str, str]], bucket: str, alias: Any, key: str, errors: list[str]) -> None:
    normalized = _normalize_alias(alias)
    if not normalized:
        return
    existing = index[bucket].get(normalized)
    if existing and existing != key:
        errors.append(f"Alias collision in {bucket}: '{alias}' maps to '{existing}' and '{key}'.")
        return
    index[bucket][normalized] = key


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


def _normalize_domain(domain: Dict[str, Any], errors: list[str]) -> Dict[str, Any]:
    normalized = deepcopy(domain)
    for dataset_key, dataset in list(normalized["datasets"].items()):
        if not isinstance(dataset, dict):
            errors.append(f"Dataset '{dataset_key}' must be an object; skipped.")
            normalized["datasets"].pop(dataset_key, None)
            continue
        dataset.setdefault("display_name", dataset_key)
        dataset["keywords"] = [str(item) for item in _as_list(dataset.get("keywords")) if str(item).strip()]
        dataset["required_params"] = [str(item) for item in _as_list(dataset.get("required_params")) if str(item).strip()]
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
    for metric_key, metric in list(normalized["metrics"].items()):
        if not isinstance(metric, dict):
            errors.append(f"Metric '{metric_key}' must be an object; skipped.")
            normalized["metrics"].pop(metric_key, None)
            continue
        metric.setdefault("display_name", metric_key)
        metric["aliases"] = [str(item) for item in _as_list(metric.get("aliases")) if str(item).strip()]
        metric["required_datasets"] = [str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip()]
    return normalized


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


def _item_to_domain(domain: Dict[str, Any], item: Dict[str, Any]) -> None:
    gbn = str(item.get("gbn") or "")
    key = str(item.get("key") or "").strip()
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    if not key or gbn not in domain:
        return
    if gbn == "join_rules":
        rule = deepcopy(payload)
        rule.setdefault("name", key)
        domain["join_rules"].append(rule)
        return
    domain[gbn][key] = deepcopy(payload)


def load_mongodb_domain_item_payload(db_name_value: Any = None, collection_name_value: Any = None) -> Dict[str, Any]:
    db_name = _resolve_db_name(db_name_value)
    collection_name = _resolve_collection_name(collection_name_value)
    errors: list[str] = []
    load_errors: list[str] = []
    items: list[Dict[str, Any]] = []
    try:
        collection = _get_collection(db_name, collection_name)
        cursor = collection.find(
            {"status": "active"},
            {"gbn": 1, "key": 1, "payload": 1, "updated_at": 1, "created_at": 1},
        ).sort([("gbn", 1), ("key", 1)])
        items = [item for item in cursor if isinstance(item, dict)]
    except Exception as exc:
        message = f"MongoDB domain item load failed: {exc}"
        errors.append(message)
        load_errors.append(message)
    if not load_errors and not items:
        message = f"No active domain items found in {db_name}.{collection_name}."
        errors.append(message)
        load_errors.append(message)
    domain = _empty_domain()
    for item in items:
        _item_to_domain(domain, item)
    domain = _normalize_domain(domain, errors)
    domain_index = _build_domain_index(domain, errors)
    gbn_counts = {
        "products": len(domain["products"]),
        "process_groups": len(domain["process_groups"]),
        "terms": len(domain["terms"]),
        "datasets": len(domain["datasets"]),
        "metrics": len(domain["metrics"]),
        "join_rules": len(domain["join_rules"]),
    }
    document = {"domain_id": "mongodb_domain_items", "status": "active", "metadata": {}, "domain": domain}
    return {
        "domain_document": document,
        "domain": domain,
        "domain_index": domain_index,
        "domain_errors": errors,
        "mongo_domain_load_status": {
            "database": db_name,
            "collection": collection_name,
            "active_item_count": len(items),
            "gbn_counts": gbn_counts,
            "loaded": not load_errors and bool(items),
            "errors": load_errors,
            "domain_error_count": len(errors),
            "source": "mongodb_domain_items",
        },
    }


class MongoDBDomainItemPayloadLoader(Component):
    display_name = "MongoDB Domain Item Payload Loader"
    description = "Load active item-level domain documents and return the domain_payload used by the data answer flow."
    icon = "Database"
    name = "MongoDBDomainItemPayloadLoader"

    inputs = [
        MessageTextInput(name="db_name", display_name="Database Name", info="MongoDB database name. Default is datagov.", value=DB_NAME, advanced=True),
        MessageTextInput(name="collection_name", display_name="Collection Name", info="MongoDB item collection. Default is manufacturing_domain_items.", value=DOMAIN_ITEMS_COLLECTION, advanced=True),
    ]

    outputs = [
        Output(name="domain_payload", display_name="Domain Payload", method="build_domain_payload", types=["Data"]),
    ]

    def build_domain_payload(self) -> Data:
        return _make_data(load_mongodb_domain_item_payload(getattr(self, "db_name", None), getattr(self, "collection_name", None)))
