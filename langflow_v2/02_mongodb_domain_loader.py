from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from typing import Any, Dict


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


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _empty_domain() -> Dict[str, Any]:
    return {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return str(value)


def _merge_item(domain: Dict[str, Any], doc: Dict[str, Any]) -> None:
    if isinstance(doc.get("domain"), dict):
        for key, value in doc["domain"].items():
            if key == "join_rules" and isinstance(value, list):
                domain.setdefault("join_rules", []).extend(deepcopy(value))
            elif isinstance(value, dict):
                domain.setdefault(key, {}).update(deepcopy(value))
        return

    gbn = str(doc.get("gbn") or doc.get("category") or "").strip()
    key = str(doc.get("key") or doc.get("name") or "").strip()
    payload = doc.get("payload") if isinstance(doc.get("payload"), dict) else {}
    if not gbn:
        return
    if gbn == "join_rules":
        item = deepcopy(payload)
        if key:
            item.setdefault("name", key)
        domain.setdefault("join_rules", []).append(item)
        return
    if gbn not in domain or not isinstance(domain.get(gbn), dict):
        domain[gbn] = {}
    if key:
        domain[gbn][key] = deepcopy(payload)


def _load_domain_from_mongo(mongo_uri: str, db_name: str, collection_name: str, status: str, limit: int) -> Dict[str, Any]:
    errors: list[str] = []
    domain = _empty_domain()
    docs: list[Dict[str, Any]] = []
    try:
        mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
        client = mongo_client_cls(mongo_uri, serverSelectionTimeoutMS=5000)
        query = {"status": status} if status else {}
        cursor = client[db_name][collection_name].find(query).limit(limit)
        docs = [dict(item) for item in cursor]
        for doc in docs:
            _merge_item(domain, doc)
    except Exception as exc:
        errors.append(str(exc))

    return {
        "domain_payload": {
            "domain_document": {
                "domain_id": f"{db_name}.{collection_name}",
                "status": status or "all",
                "metadata": {"loaded_at": datetime.utcnow().isoformat(), "document_count": len(docs)},
                "domain": domain,
            },
            "domain": domain,
            "domain_errors": errors,
            "domain_source": "mongodb",
            "raw_documents": _json_safe(docs[:20]),
        }
    }


class MongoDBDomainLoader(Component):
    display_name = "MongoDB Domain Loader"
    description = "Standalone MongoDB loader for domain documents or gbn/key/payload item documents."
    icon = "Database"
    name = "MongoDBDomainLoader"

    inputs = [
        MultilineInput(name="mongo_uri", display_name="Mongo URI", value="", info="MongoDB URI. Leave empty to return an empty domain with an error."),
        MessageTextInput(name="db_name", display_name="Database Name", value="datagov"),
        MessageTextInput(name="collection_name", display_name="Collection Name", value="manufacturing_domain_items"),
        MessageTextInput(name="status", display_name="Status Filter", value="active", advanced=True),
        MessageTextInput(name="limit", display_name="Load Limit", value="500", advanced=True),
    ]
    outputs = [Output(name="domain_payload", display_name="Domain Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        try:
            limit = max(1, int(getattr(self, "limit", "500") or 500))
        except Exception:
            limit = 500
        payload = _load_domain_from_mongo(
            str(getattr(self, "mongo_uri", "") or "").strip(),
            str(getattr(self, "db_name", "datagov") or "datagov").strip(),
            str(getattr(self, "collection_name", "manufacturing_domain_items") or "manufacturing_domain_items").strip(),
            str(getattr(self, "status", "active") or "").strip(),
            limit,
        )
        domain = payload["domain_payload"]["domain"]
        self.status = {
            "source": "mongodb",
            "metrics": len(domain.get("metrics", {})) if isinstance(domain.get("metrics"), dict) else 0,
            "errors": len(payload["domain_payload"].get("domain_errors", [])),
        }
        return _make_data(payload)

