from __future__ import annotations

import json
from copy import deepcopy
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


def _connect_collection(mongo_uri: str, db_name: str, collection_name: str) -> tuple[Any, Any]:
    mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
    client = mongo_client_cls(mongo_uri, serverSelectionTimeoutMS=5000)
    return client, client[db_name][collection_name]


def _load_rows(collection: Any, data_ref: Dict[str, Any]) -> list[Dict[str, Any]]:
    ref_id = str(data_ref.get("ref_id") or data_ref.get("id") or "").strip()
    if not ref_id:
        return []
    doc = collection.find_one({"ref_id": ref_id})
    if not isinstance(doc, dict):
        return []
    rows = doc.get("rows") if isinstance(doc.get("rows"), list) else doc.get("data")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _hydrate_refs(value: Any, collection: Any, loaded: list[Dict[str, Any]], path: str) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            current_path = f"{path}.{key}" if path else key
            result[key] = _hydrate_refs(item, collection, loaded, current_path)
        data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
        if data_ref:
            rows = _load_rows(collection, data_ref)
            if rows:
                result["data"] = _json_safe(rows)
                result["row_count"] = len(rows)
                result["data_ref_loaded"] = True
                result["data_is_preview"] = False
                loaded.append({"path": path, "ref_id": data_ref.get("ref_id"), "row_count": len(rows)})
        return result
    if isinstance(value, list):
        return [_hydrate_refs(item, collection, loaded, f"{path}[{index}]") for index, item in enumerate(value)]
    return value


def load_payload_from_mongo(payload_value: Any, mongo_uri_value: Any = "", db_name_value: Any = "datagov", collection_name_value: Any = DEFAULT_COLLECTION, enabled_value: Any = "true") -> Dict[str, Any]:
    payload = _payload_from_value(payload_value)
    if not payload:
        return {"mongo_data_load": {"enabled": False, "loaded": False, "ref_count": 0, "errors": ["empty payload"]}}
    if not _truthy(enabled_value):
        return {**payload, "mongo_data_load": {"enabled": False, "loaded": False, "ref_count": 0, "errors": []}}

    mongo_uri = str(mongo_uri_value or "").strip()
    db_name = str(db_name_value or "datagov").strip() or "datagov"
    collection_name = str(collection_name_value or DEFAULT_COLLECTION).strip() or DEFAULT_COLLECTION
    if not mongo_uri:
        return {**payload, "mongo_data_load": {"enabled": True, "loaded": False, "ref_count": 0, "errors": ["Mongo URI is empty."]}}

    client = None
    loaded: list[Dict[str, Any]] = []
    try:
        client, collection = _connect_collection(mongo_uri, db_name, collection_name)
        hydrated = _hydrate_refs(payload, collection, loaded, "")
        hydrated["mongo_data_load"] = {"enabled": True, "loaded": bool(loaded), "ref_count": len(loaded), "loaded_refs": loaded, "errors": []}
        return hydrated
    except Exception as exc:
        return {**payload, "mongo_data_load": {"enabled": True, "loaded": False, "ref_count": 0, "errors": [str(exc)]}}
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


class MongoDBDataLoader(Component):
    display_name = "MongoDB Data Loader"
    description = "Load row lists from MongoDB data_ref pointers before follow-up or pandas processing."
    icon = "DatabaseZap"
    name = "MongoDBDataLoader"

    inputs = [
        DataInput(name="payload", display_name="Payload", info="Payload containing data_ref pointers.", input_types=["Data", "JSON"]),
        MultilineInput(name="mongo_uri", display_name="Mongo URI", value="", info="MongoDB URI used by MongoDB Data Store."),
        MessageTextInput(name="db_name", display_name="Database Name", value="datagov"),
        MessageTextInput(name="collection_name", display_name="Collection Name", value=DEFAULT_COLLECTION),
        MessageTextInput(name="enabled", display_name="Enabled", value="true", advanced=True),
    ]
    outputs = [Output(name="loaded_payload", display_name="Loaded Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = load_payload_from_mongo(
            getattr(self, "payload", None),
            getattr(self, "mongo_uri", ""),
            getattr(self, "db_name", "datagov"),
            getattr(self, "collection_name", DEFAULT_COLLECTION),
            getattr(self, "enabled", "true"),
        )
        meta = payload.get("mongo_data_load", {}) if isinstance(payload, dict) else {}
        self.status = {"loaded": meta.get("loaded", False), "ref_count": meta.get("ref_count", 0), "errors": len(meta.get("errors", [])) if isinstance(meta.get("errors"), list) else 0}
        return _make_data(payload)

