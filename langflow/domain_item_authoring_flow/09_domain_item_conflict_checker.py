from __future__ import annotations

import json
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


def _existing_map(existing_items_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    grouped = existing_items_payload.get("existing_items") if isinstance(existing_items_payload.get("existing_items"), dict) else {}
    result: Dict[str, Dict[str, Any]] = {}
    for gbn, items in grouped.items():
        for item in _as_list(items):
            if isinstance(item, dict) and item.get("key"):
                result[f"{gbn}:{item['key']}"] = item
    return result


def check_domain_item_conflicts(normalized_value: Any, existing_value: Any) -> Dict[str, Any]:
    normalized_payload = _payload_from_value(normalized_value)
    existing_payload = _payload_from_value(existing_value)
    items = [item for item in _as_list(normalized_payload.get("normalized_domain_items")) if isinstance(item, dict)]
    existing_by_key = _existing_map(existing_payload)
    issues: list[Dict[str, Any]] = []
    item_results: list[Dict[str, Any]] = []

    alias_owners: Dict[str, str] = {}
    keyword_owners: Dict[str, str] = {}
    for identity, existing in existing_by_key.items():
        for alias in _as_list(existing.get("normalized_aliases")):
            alias_owners[str(alias)] = identity
        for keyword in _as_list(existing.get("normalized_keywords")):
            keyword_owners[str(keyword)] = identity

    seen_keys: set[str] = set()
    for item in items:
        gbn = str(item.get("gbn") or "")
        key = str(item.get("key") or "")
        identity = f"{gbn}:{key}"
        status = "active"
        item_issues: list[Dict[str, Any]] = []
        if identity in seen_keys:
            item_issues.append({"severity": "error", "type": "duplicate_in_batch", "message": f"{identity} appears more than once in this batch."})
        seen_keys.add(identity)
        if identity in existing_by_key:
            item_issues.append({"severity": "warning", "type": "update_existing", "message": f"{identity} already exists and will be updated."})
        for alias in _as_list(item.get("normalized_aliases")):
            owner = alias_owners.get(str(alias))
            if owner and owner != identity:
                item_issues.append({"severity": "error", "type": "alias_collision", "message": f"Alias '{alias}' already belongs to {owner}."})
        for keyword in _as_list(item.get("normalized_keywords")):
            owner = keyword_owners.get(str(keyword))
            if owner and owner != identity:
                item_issues.append({"severity": "error", "type": "keyword_collision", "message": f"Keyword '{keyword}' already belongs to {owner}."})
        if any(issue["severity"] == "error" for issue in item_issues):
            status = "review_required"
        issues.extend(item_issues)
        item_results.append({"gbn": gbn, "key": key, "recommended_status": status, "issues": item_issues})

    return {
        "conflict_report": {
            "has_blocking_conflict": any(issue["severity"] == "error" for issue in issues),
            "issues": issues,
            "item_results": item_results,
        },
        "normalized_domain_items": items,
    }


class DomainItemConflictChecker(Component):
    display_name = "Domain Item Conflict Checker"
    description = "Check key, alias, and dataset keyword collisions before item-level MongoDB save."
    icon = "ShieldAlert"
    name = "DomainItemConflictChecker"

    inputs = [
        DataInput(name="normalized_domain_items", display_name="Normalized Domain Items", info="Output from Normalize Domain Item.", input_types=["Data", "JSON"]),
        DataInput(name="existing_items", display_name="Existing Items", info="Output from MongoDB Existing Domain Item Loader.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="conflict_report", display_name="Conflict Report", method="build_report", types=["Data"]),
    ]

    def build_report(self) -> Data:
        return _make_data(check_domain_item_conflicts(getattr(self, "normalized_domain_items", None), getattr(self, "existing_items", None)))
