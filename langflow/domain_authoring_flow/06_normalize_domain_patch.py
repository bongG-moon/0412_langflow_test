from __future__ import annotations

import json
import re
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
VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}


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


def _dedupe(values: Any) -> list[str]:
    ordered: list[str] = []
    for item in _as_list(values):
        text = str(item or "").strip()
        if text and text not in ordered:
            ordered.append(text)
    return ordered


def _slug(value: Any, fallback: str = "item") -> str:
    text = str(value or "").strip()
    if not text:
        text = fallback
    text = re.sub(r"[^0-9A-Za-z가-힣_]+", "_", text).strip("_")
    return text or fallback


def _empty_patch() -> Dict[str, Any]:
    return {
        "products": {},
        "process_groups": {},
        "terms": {},
        "datasets": {},
        "metrics": {},
        "join_rules": [],
    }


def _merge_list_dict_item(items: list[Dict[str, Any]], item: Dict[str, Any], key_fields: list[str]) -> None:
    identity = tuple(str(item.get(key, "")) for key in key_fields)
    for existing in items:
        if tuple(str(existing.get(key, "")) for key in key_fields) == identity:
            existing.update({key: value for key, value in item.items() if value not in (None, "", [], {})})
            return
    items.append(item)


def _normalize_dataset(dataset_key: str, dataset: Any, warnings: list[str]) -> Dict[str, Any] | None:
    if not isinstance(dataset, dict):
        warnings.append(f"Dataset `{dataset_key}` is not an object and was skipped.")
        return None
    normalized = deepcopy(dataset)
    normalized.setdefault("display_name", dataset_key)
    normalized["keywords"] = _dedupe(normalized.get("keywords"))
    normalized["required_params"] = _dedupe(normalized.get("required_params"))
    columns = []
    for column in _as_list(normalized.get("columns")):
        if not isinstance(column, dict) or not str(column.get("name", "")).strip():
            continue
        item = dict(column)
        item["name"] = str(item["name"]).strip()
        item["type"] = str(item.get("type") or "string").strip()
        if item["type"] not in VALID_COLUMN_TYPES:
            warnings.append(f"Dataset `{dataset_key}` column `{item['name']}` has unknown type `{item['type']}`; using string.")
            item["type"] = "string"
        columns.append(item)
    normalized["columns"] = columns
    return normalized


def _normalize_metric(metric_key: str, metric: Any, warnings: list[str]) -> Dict[str, Any] | None:
    if not isinstance(metric, dict):
        warnings.append(f"Metric `{metric_key}` is not an object and was skipped.")
        return None
    normalized = deepcopy(metric)
    normalized.setdefault("display_name", metric_key)
    normalized["aliases"] = _dedupe([metric_key, normalized.get("display_name"), * _as_list(normalized.get("aliases"))])
    normalized["required_datasets"] = _dedupe(normalized.get("required_datasets"))
    normalized["required_columns"] = _dedupe(normalized.get("required_columns"))
    normalized["default_group_by"] = _dedupe(normalized.get("default_group_by"))
    source_columns = []
    for item in _as_list(normalized.get("source_columns")):
        if isinstance(item, dict) and item.get("dataset_key") and item.get("column"):
            source_columns.append(
                {
                    "dataset_key": str(item.get("dataset_key", "")).strip(),
                    "column": str(item.get("column", "")).strip(),
                    "role": str(item.get("role", "")).strip(),
                }
            )
    if source_columns:
        normalized["source_columns"] = source_columns
    return normalized


def _legacy_analysis_rule_to_metric(rule: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    key = _slug(rule.get("name") or rule.get("output_column") or rule.get("display_name"), "metric")
    metric = {
        "display_name": str(rule.get("display_name") or key).strip(),
        "aliases": _dedupe([rule.get("name"), rule.get("display_name"), * _as_list(rule.get("synonyms"))]),
        "required_datasets": _dedupe(rule.get("required_datasets")),
        "required_columns": _dedupe(rule.get("required_columns")),
        "source_columns": rule.get("source_columns") if isinstance(rule.get("source_columns"), list) else [],
        "calculation_mode": str(rule.get("calculation_mode") or "").strip(),
        "formula": str(rule.get("formula") or "").strip(),
        "condition": str(rule.get("condition") or "").strip(),
        "decision_rule": str(rule.get("decision_rule") or "").strip(),
        "pandas_hint": str(rule.get("pandas_hint") or "").strip(),
        "output_column": str(rule.get("output_column") or key).strip(),
        "default_group_by": _dedupe(rule.get("default_group_by")),
        "description": str(rule.get("description") or "").strip(),
        "source": str(rule.get("source") or "domain_authoring").strip(),
    }
    return key, metric


def _legacy_join_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    base = str(rule.get("base_dataset") or "").strip()
    join = str(rule.get("join_dataset") or "").strip()
    keys = _dedupe(rule.get("join_keys") or rule.get("keys"))
    return {
        "name": str(rule.get("name") or f"{base}_{join}_join").strip(),
        "datasets": _dedupe([base, join]),
        "base_dataset": base,
        "join_dataset": join,
        "keys": keys,
        "join_keys": keys,
        "join_type": str(rule.get("join_type") or "left").strip().lower(),
        "description": str(rule.get("description") or "").strip(),
        "source": str(rule.get("source") or "domain_authoring").strip(),
    }


def _apply_legacy_payload(patch: Dict[str, Any], raw_payload: Dict[str, Any], warnings: list[str]) -> None:
    for item in _as_list(raw_payload.get("dataset_keywords")):
        if not isinstance(item, dict):
            continue
        dataset_key = str(item.get("dataset_key") or "").strip()
        if not dataset_key:
            continue
        dataset = patch["datasets"].setdefault(dataset_key, {"display_name": dataset_key, "keywords": [], "required_params": [], "columns": []})
        dataset["keywords"] = _dedupe([* _as_list(dataset.get("keywords")), * _as_list(item.get("keywords"))])

    for group in _as_list(raw_payload.get("value_groups")):
        if not isinstance(group, dict):
            continue
        field = str(group.get("field") or "").strip()
        canonical = str(group.get("canonical") or "").strip()
        aliases = _dedupe([canonical, * _as_list(group.get("synonyms"))])
        values = _dedupe(group.get("values"))
        key = _slug(canonical or field, "term")
        if field in {"process", "process_name", "oper_name"}:
            patch["process_groups"][key] = {
                "display_name": canonical or key,
                "aliases": aliases,
                "processes": values or ([canonical] if canonical else []),
                "description": str(group.get("description") or "").strip(),
            }
        elif field in {"product", "product_name"}:
            patch["products"][key] = {
                "display_name": canonical or key,
                "aliases": aliases,
                "filters": {"product_name": canonical or (values[0] if values else key)},
                "description": str(group.get("description") or "").strip(),
            }
        else:
            filter_payload: Dict[str, Any] = {"column": field, "operator": "in" if len(values) > 1 else "equals"}
            if len(values) > 1:
                filter_payload["values"] = values
            elif values:
                filter_payload["value"] = values[0]
            elif canonical:
                filter_payload["value"] = canonical
            patch["terms"][key] = {
                "display_name": canonical or key,
                "aliases": aliases,
                "filter": filter_payload,
                "description": str(group.get("description") or "").strip(),
            }

    for rule in _as_list(raw_payload.get("analysis_rules")):
        if isinstance(rule, dict):
            key, metric = _legacy_analysis_rule_to_metric(rule)
            patch["metrics"][key] = metric

    for rule in _as_list(raw_payload.get("join_rules")):
        if isinstance(rule, dict):
            _merge_list_dict_item(patch["join_rules"], _legacy_join_rule(rule), ["name"])

    if raw_payload.get("notes") and not patch["terms"].get("DOMAIN_NOTES"):
        warnings.extend([str(note) for note in _as_list(raw_payload.get("notes")) if str(note).strip()])


def normalize_domain_patch(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    raw_patch = payload.get("domain_patch") if isinstance(payload.get("domain_patch"), dict) else payload
    if isinstance(raw_patch.get("domain"), dict):
        raw_patch = raw_patch["domain"]
    patch = _empty_patch()
    warnings = [str(item) for item in _as_list(payload.get("warnings")) if str(item).strip()]

    for key in ("products", "process_groups", "terms", "datasets", "metrics"):
        source = raw_patch.get(key) if isinstance(raw_patch.get(key), dict) else {}
        for item_key, item_value in source.items():
            if isinstance(item_value, dict):
                patch[key][str(item_key)] = deepcopy(item_value)
    for rule in _as_list(raw_patch.get("join_rules")):
        if isinstance(rule, dict):
            _merge_list_dict_item(patch["join_rules"], _legacy_join_rule(rule), ["name"])

    _apply_legacy_payload(patch, raw_patch if isinstance(raw_patch, dict) else {}, warnings)

    for dataset_key, dataset in list(patch["datasets"].items()):
        normalized = _normalize_dataset(dataset_key, dataset, warnings)
        if normalized is None:
            patch["datasets"].pop(dataset_key, None)
        else:
            patch["datasets"][dataset_key] = normalized

    for metric_key, metric in list(patch["metrics"].items()):
        normalized = _normalize_metric(metric_key, metric, warnings)
        if normalized is None:
            patch["metrics"].pop(metric_key, None)
        else:
            patch["metrics"][metric_key] = normalized

    for key in ("products", "process_groups", "terms"):
        for item_key, item in list(patch[key].items()):
            if not isinstance(item, dict):
                patch[key].pop(item_key, None)
                continue
            item.setdefault("display_name", item_key)
            item["aliases"] = _dedupe([item_key, item.get("display_name"), * _as_list(item.get("aliases"))])
            if key == "process_groups":
                item["processes"] = _dedupe(item.get("processes"))

    return {
        "normalized_domain_patch": patch,
        "warnings": warnings,
        "parse_errors": payload.get("parse_errors", []),
    }


class NormalizeDomainPatch(Component):
    display_name = "Normalize Domain Patch"
    description = "Normalize LLM domain_patch and legacy Streamlit domain registry fields to the Main Flow domain schema."
    icon = "ListChecks"
    name = "NormalizeDomainPatch"

    inputs = [
        DataInput(name="domain_patch", display_name="Domain Patch", info="Output from Parse Domain Patch JSON.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="normalized_domain_patch", display_name="Normalized Domain Patch", method="build_normalized_patch", types=["Data"]),
    ]

    def build_normalized_patch(self) -> Data:
        return _make_data(normalize_domain_patch(getattr(self, "domain_patch", None)))
