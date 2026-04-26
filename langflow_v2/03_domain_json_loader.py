from __future__ import annotations

import ast
import json
from copy import deepcopy
from dataclasses import dataclass
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


def _parse_jsonish(text: Any) -> tuple[Any, list[str]]:
    if isinstance(text, (dict, list)):
        return deepcopy(text), []
    raw = str(text or "").strip()
    if not raw:
        return {}, []
    errors: list[str] = []
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(raw), []
        except Exception as exc:
            errors.append(str(exc))
    return {}, errors


def _empty_domain() -> Dict[str, Any]:
    return {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}


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


def _normalize_domain_payload(raw_value: Any) -> Dict[str, Any]:
    parsed, errors = _parse_jsonish(raw_value)
    if isinstance(parsed, dict) and isinstance(parsed.get("domain"), dict):
        domain = deepcopy(parsed["domain"])
        metadata = deepcopy(parsed.get("metadata", {})) if isinstance(parsed.get("metadata"), dict) else {}
        status = str(parsed.get("status") or "active")
        domain_id = str(parsed.get("domain_id") or metadata.get("domain_id") or "json_domain")
    elif isinstance(parsed, dict) and any(key in parsed for key in ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")):
        domain = deepcopy(parsed)
        metadata = {}
        status = "active"
        domain_id = "json_domain"
    elif isinstance(parsed, dict) and any(key in parsed for key in ("gbn", "category", "payload")):
        domain = _empty_domain()
        _merge_item(domain, parsed)
        metadata = {"document_count": 1}
        status = str(parsed.get("status") or "active")
        domain_id = "json_domain_items"
    elif isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
        domain = _empty_domain()
        for item in parsed["items"]:
            if isinstance(item, dict):
                _merge_item(domain, item)
        metadata = {"document_count": len(parsed["items"])}
        status = str(parsed.get("status") or "active")
        domain_id = "json_domain_items"
    elif isinstance(parsed, list):
        domain = _empty_domain()
        for item in parsed:
            if isinstance(item, dict):
                _merge_item(domain, item)
        metadata = {"document_count": len(parsed)}
        status = "active"
        domain_id = "json_domain_items"
    else:
        domain = _empty_domain()
        metadata = {}
        status = "empty"
        domain_id = "empty"

    for key, default in _empty_domain().items():
        if key not in domain:
            domain[key] = deepcopy(default)

    return {
        "domain_payload": {
            "domain_document": {"domain_id": domain_id, "status": status, "metadata": metadata, "domain": domain},
            "domain": domain,
            "domain_errors": errors,
            "domain_source": "json_input",
        }
    }


class DomainJsonLoader(Component):
    display_name = "Domain JSON Loader"
    description = "Standalone loader for direct JSON domain input."
    icon = "FileJson"
    name = "DomainJsonLoader"

    inputs = [
        MultilineInput(
            name="domain_json",
            display_name="Domain JSON",
            value='{"domain": {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}}',
            info="Direct domain JSON fallback when MongoDB is not used.",
        )
    ]
    outputs = [Output(name="domain_payload", display_name="Domain Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = _normalize_domain_payload(getattr(self, "domain_json", ""))
        domain = payload["domain_payload"]["domain"]
        self.status = {
            "source": "json_input",
            "metrics": len(domain.get("metrics", {})) if isinstance(domain.get("metrics"), dict) else 0,
            "errors": len(payload["domain_payload"].get("domain_errors", [])),
        }
        return _make_data(payload)

