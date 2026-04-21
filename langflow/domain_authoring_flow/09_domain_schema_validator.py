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


def validate_domain_schema(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    document = payload.get("domain_document") if isinstance(payload.get("domain_document"), dict) else {}
    domain = payload.get("merged_domain") if isinstance(payload.get("merged_domain"), dict) else document.get("domain")
    if not isinstance(domain, dict):
        domain = {}
    errors: list[str] = []
    warnings: list[str] = []
    conflicts = []
    conflict_report = payload.get("conflict_report") if isinstance(payload.get("conflict_report"), dict) else {}
    if isinstance(conflict_report.get("conflicts"), list):
        conflicts = conflict_report["conflicts"]
    if isinstance(conflict_report.get("warnings"), list):
        warnings.extend(str(item) for item in conflict_report["warnings"])
    if isinstance(conflict_report.get("blocking_errors"), list):
        errors.extend(str(item) for item in conflict_report["blocking_errors"])

    for key in ("products", "process_groups", "terms", "datasets", "metrics"):
        if not isinstance(domain.get(key), dict):
            errors.append(f"`domain.{key}` must be an object.")
            domain[key] = {}
    if not isinstance(domain.get("join_rules"), list):
        errors.append("`domain.join_rules` must be a list.")
        domain["join_rules"] = []

    dataset_columns: Dict[str, set[str]] = {}
    for dataset_key, dataset in domain.get("datasets", {}).items():
        if not isinstance(dataset, dict):
            errors.append(f"Dataset `{dataset_key}` must be an object.")
            continue
        if not isinstance(dataset.get("required_params", []), list):
            errors.append(f"Dataset `{dataset_key}` required_params must be a list.")
        columns = dataset.get("columns")
        if not isinstance(columns, list):
            warnings.append(f"Dataset `{dataset_key}` has no columns list.")
            columns = []
        names: set[str] = set()
        for column in columns:
            if not isinstance(column, dict) or not column.get("name"):
                errors.append(f"Dataset `{dataset_key}` has a column without name.")
                continue
            names.add(str(column["name"]))
            column_type = str(column.get("type") or "string")
            if column_type not in VALID_COLUMN_TYPES:
                warnings.append(f"Dataset `{dataset_key}` column `{column['name']}` has unknown type `{column_type}`.")
        dataset_columns[str(dataset_key)] = names

    for metric_key, metric in domain.get("metrics", {}).items():
        if not isinstance(metric, dict):
            errors.append(f"Metric `{metric_key}` must be an object.")
            continue
        required_datasets = _as_list(metric.get("required_datasets"))
        if not required_datasets:
            warnings.append(f"Metric `{metric_key}` has no required_datasets.")
        for dataset_key in required_datasets:
            if str(dataset_key) not in domain.get("datasets", {}):
                warnings.append(f"Metric `{metric_key}` references undefined dataset `{dataset_key}`.")
        for source_column in _as_list(metric.get("source_columns")):
            if not isinstance(source_column, dict):
                continue
            dataset_key = str(source_column.get("dataset_key") or "")
            column = str(source_column.get("column") or "")
            if dataset_key in dataset_columns and column and column not in dataset_columns[dataset_key]:
                warnings.append(f"Metric `{metric_key}` source column `{dataset_key}.{column}` is not declared in dataset columns.")

    for rule in domain.get("join_rules", []):
        if not isinstance(rule, dict):
            errors.append("Join rule must be an object.")
            continue
        datasets = [item for item in _as_list(rule.get("datasets") or [rule.get("base_dataset"), rule.get("join_dataset")]) if item]
        for dataset_key in datasets:
            if str(dataset_key) not in domain.get("datasets", {}):
                warnings.append(f"Join rule `{rule.get('name', '')}` references undefined dataset `{dataset_key}`.")

    if document:
        document = dict(document)
        document["domain"] = domain
    else:
        document = {"domain_id": "manufacturing_default", "status": "draft", "metadata": {}, "domain": domain}
    validation = {"errors": errors, "warnings": warnings, "conflicts": conflicts}
    return {
        "domain_document": document,
        "validation": validation,
        "is_saveable": not errors,
        "merge_status": payload.get("merge_status", {}),
    }


class DomainSchemaValidator(Component):
    display_name = "Domain Schema Validator"
    description = "Validate that the merged Domain JSON can be consumed by the Main Data Answer Flow."
    icon = "BadgeCheck"
    name = "DomainSchemaValidator"

    inputs = [
        DataInput(name="merged_domain", display_name="Merged Domain", info="Output from Domain Patch Merger.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="validated_domain", display_name="Validated Domain", method="build_validated_domain", types=["Data"]),
    ]

    def build_validated_domain(self) -> Data:
        return _make_data(validate_domain_schema(getattr(self, "merged_domain", None)))
