from __future__ import annotations

import json
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


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _domain_from_payload(value: Any, key: str) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get(key)
    if isinstance(domain, dict):
        return domain
    for document_key in ("existing_domain_document", "domain_document"):
        document = payload.get(document_key)
        if isinstance(document, dict) and isinstance(document.get("domain"), dict):
            return document["domain"]
    for fallback_key in ("existing_domain", "normalized_domain_patch", "domain_patch", "domain"):
        candidate = payload.get(fallback_key)
        if isinstance(candidate, dict):
            return candidate
    return payload if any(name in payload for name in ("products", "datasets", "metrics")) else {}


def _collect_alias_owners(domain: Dict[str, Any]) -> Dict[str, str]:
    owners: Dict[str, str] = {}
    buckets = {
        "products": "product",
        "process_groups": "process_group",
        "terms": "term",
        "metrics": "metric",
        "datasets": "dataset",
    }
    for bucket, label in buckets.items():
        items = domain.get(bucket) if isinstance(domain.get(bucket), dict) else {}
        for key, item in items.items():
            candidates = [key]
            if isinstance(item, dict):
                candidates.append(item.get("display_name"))
                candidates.extend(_as_list(item.get("aliases")))
                candidates.extend(_as_list(item.get("keywords")))
                if bucket == "process_groups":
                    candidates.extend(_as_list(item.get("processes")))
            for alias in candidates:
                normalized = _norm(alias)
                if normalized:
                    owners[normalized] = f"{label}:{key}"
    return owners


def detect_domain_conflicts(existing_value: Any, patch_value: Any) -> Dict[str, Any]:
    existing = _domain_from_payload(existing_value, "existing_domain")
    patch = _domain_from_payload(patch_value, "normalized_domain_patch")
    conflicts: list[Dict[str, Any]] = []
    warnings: list[str] = []
    blocking_errors: list[str] = []

    existing_aliases = _collect_alias_owners(existing)
    patch_aliases: Dict[str, str] = {}
    for alias, owner in _collect_alias_owners(patch).items():
        previous_owner = patch_aliases.get(alias)
        if previous_owner and previous_owner != owner:
            conflicts.append({"type": "patch_alias_collision", "alias": alias, "owners": [previous_owner, owner]})
        patch_aliases[alias] = owner
        existing_owner = existing_aliases.get(alias)
        if existing_owner and existing_owner != owner:
            conflicts.append({"type": "existing_alias_collision", "alias": alias, "existing_owner": existing_owner, "new_owner": owner})

    for metric_key, metric in (patch.get("metrics") or {}).items():
        if metric_key in (existing.get("metrics") or {}):
            old_formula = str((existing.get("metrics") or {}).get(metric_key, {}).get("formula", "")).strip()
            new_formula = str(metric.get("formula", "")).strip() if isinstance(metric, dict) else ""
            if old_formula and new_formula and old_formula != new_formula:
                conflicts.append(
                    {
                        "type": "metric_formula_changed",
                        "metric_key": metric_key,
                        "existing_formula": old_formula,
                        "new_formula": new_formula,
                    }
                )

    combined_datasets = set((existing.get("datasets") or {}).keys()) | set((patch.get("datasets") or {}).keys())
    for metric_key, metric in (patch.get("metrics") or {}).items():
        if not isinstance(metric, dict):
            continue
        for dataset_key in _as_list(metric.get("required_datasets")):
            if str(dataset_key) not in combined_datasets:
                warnings.append(f"Metric `{metric_key}` references dataset `{dataset_key}` that is not defined yet.")

    for rule in _as_list(patch.get("join_rules")):
        if not isinstance(rule, dict):
            continue
        for dataset_key in _as_list(rule.get("datasets") or [rule.get("base_dataset"), rule.get("join_dataset")]):
            if dataset_key and str(dataset_key) not in combined_datasets:
                warnings.append(f"Join rule `{rule.get('name', '')}` references dataset `{dataset_key}` that is not defined yet.")

    return {
        "conflicts": conflicts,
        "warnings": warnings,
        "blocking_errors": blocking_errors,
        "has_blocking_conflict": bool(blocking_errors),
    }


class DomainConflictDetector(Component):
    display_name = "Domain Conflict Detector"
    description = "Detect alias, metric, dataset, and join conflicts before merging a Domain JSON patch."
    icon = "TriangleAlert"
    name = "DomainConflictDetector"

    inputs = [
        DataInput(name="existing_domain", display_name="Existing Domain", info="Output from MongoDB Active Domain Loader.", input_types=["Data", "JSON"]),
        DataInput(name="normalized_domain_patch", display_name="Normalized Domain Patch", info="Output from Normalize Domain Patch.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="conflict_report", display_name="Conflict Report", method="build_conflict_report", types=["Data"]),
    ]

    def build_conflict_report(self) -> Data:
        return _make_data(
            detect_domain_conflicts(
                getattr(self, "existing_domain", None),
                getattr(self, "normalized_domain_patch", None),
            )
        )
