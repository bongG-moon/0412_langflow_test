from __future__ import annotations

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
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


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
    return {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}


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


def _domain_from_existing(value: Any) -> tuple[Dict[str, Any], Dict[str, Any]]:
    payload = _payload_from_value(value)
    document = payload.get("existing_domain_document") if isinstance(payload.get("existing_domain_document"), dict) else {}
    domain = payload.get("existing_domain") if isinstance(payload.get("existing_domain"), dict) else {}
    if not domain and isinstance(document.get("domain"), dict):
        domain = document["domain"]
    if not domain and isinstance(payload.get("domain"), dict):
        domain = payload["domain"]
    return document, domain or _empty_domain()


def _patch_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    patch = payload.get("normalized_domain_patch")
    if isinstance(patch, dict):
        return patch
    patch = payload.get("domain_patch")
    return patch if isinstance(patch, dict) else {}


def merge_domain_patch(existing_value: Any, patch_value: Any, conflict_value: Any, config_value: Any) -> Dict[str, Any]:
    existing_document, existing_domain = _domain_from_existing(existing_value)
    patch = _patch_from_value(patch_value)
    conflict_payload = _payload_from_value(conflict_value)
    config_outer = _payload_from_value(config_value)
    config = config_outer.get("authoring_config") if isinstance(config_outer.get("authoring_config"), dict) else config_outer
    mode = str(config.get("authoring_mode") or "append").lower()

    base_domain = _empty_domain() if mode == "create" else deepcopy(existing_domain)
    for key in ("products", "process_groups", "terms", "datasets", "metrics"):
        base_domain[key] = _deep_merge(base_domain.get(key, {}), patch.get(key, {}))
    base_domain["join_rules"] = _dedupe_list([*_as_list(base_domain.get("join_rules")), *_as_list(patch.get("join_rules"))])

    metadata = existing_document.get("metadata") if isinstance(existing_document.get("metadata"), dict) else {}
    metadata = _deep_merge(metadata, config.get("metadata") if isinstance(config.get("metadata"), dict) else {})
    domain_document = {
        "domain_id": config.get("domain_id") or existing_document.get("domain_id") or "manufacturing_default",
        "status": config.get("target_status") or existing_document.get("status") or "draft",
        "metadata": metadata,
        "domain": base_domain,
    }
    blocking_errors = conflict_payload.get("blocking_errors") if isinstance(conflict_payload.get("blocking_errors"), list) else []
    merge_status = {
        "authoring_mode": mode,
        "merged": True,
        "is_saveable": not blocking_errors and mode != "validate_only",
        "blocking_errors": blocking_errors,
        "conflict_count": len(conflict_payload.get("conflicts", [])) if isinstance(conflict_payload.get("conflicts"), list) else 0,
    }
    return {
        "domain_document": domain_document,
        "merge_status": merge_status,
        "conflict_report": conflict_payload,
    }


class DomainPatchMerger(Component):
    display_name = "Domain Patch Merger"
    description = "Merge a normalized Domain JSON patch into an existing or empty domain document."
    icon = "GitMerge"
    name = "DomainPatchMerger"

    inputs = [
        DataInput(name="existing_domain", display_name="Existing Domain", info="Output from MongoDB Active Domain Loader.", input_types=["Data", "JSON"]),
        DataInput(name="normalized_domain_patch", display_name="Normalized Domain Patch", info="Output from Normalize Domain Patch.", input_types=["Data", "JSON"]),
        DataInput(name="conflict_report", display_name="Conflict Report", info="Output from Domain Conflict Detector.", input_types=["Data", "JSON"]),
        DataInput(
            name="authoring_config",
            display_name="Authoring Config",
            info="Optional override from Domain Authoring Config Input.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="merged_domain", display_name="Merged Domain", method="build_merged_domain", types=["Data"]),
    ]

    def build_merged_domain(self) -> Data:
        return _make_data(
            merge_domain_patch(
                getattr(self, "existing_domain", None),
                getattr(self, "normalized_domain_patch", None),
                getattr(self, "conflict_report", None),
                getattr(self, "authoring_config", None),
            )
        )
