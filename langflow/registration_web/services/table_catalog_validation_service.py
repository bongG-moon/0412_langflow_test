from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from .config import VALID_COLUMN_TYPES


SQL_TEXT_KEYS = ("sql_template", "query_template", "sql", "sql_text", "query", "oracle_sql")
SQL_LINE_KEYS = ("sql_template_lines", "query_template_lines", "sql_lines")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string_list(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _has_sql_fields(dataset: Dict[str, Any]) -> bool:
    if any(key in dataset for key in (*SQL_TEXT_KEYS, *SQL_LINE_KEYS)):
        return True
    for nested_key in ("source", "oracle"):
        nested = dataset.get(nested_key)
        if isinstance(nested, dict) and any(key in nested for key in (*SQL_TEXT_KEYS, *SQL_LINE_KEYS)):
            return True
    return False


def _normalize_format_params(dataset: Dict[str, Any], required_params: list[str], issues: list[Dict[str, Any]], dataset_key: str) -> list[str]:
    if isinstance(dataset.get("format_params"), dict):
        items = list(dataset["format_params"].items())
        if all(str(key).strip().isdigit() for key, _ in items):
            items = sorted(items, key=lambda item: int(str(item[0]).strip()))
        return _string_list([value or key for key, value in items])
    if isinstance(dataset.get("format_params"), (list, tuple)):
        return _string_list(dataset.get("format_params"))
    if isinstance(dataset.get("bind_params"), dict):
        issues.append(
            {
                "severity": "warning",
                "type": "legacy_bind_params_ignored",
                "message": f"{dataset_key}: bind_params is legacy metadata; converted to format_params only.",
            }
        )
        return _string_list([value or key for key, value in dataset["bind_params"].items()])
    return list(required_params)


def _normalize_columns(value: Any, dataset_key: str, issues: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    columns: list[Dict[str, Any]] = []
    for column in _as_list(value):
        if not isinstance(column, dict) or not column.get("name"):
            issues.append({"severity": "warning", "type": "invalid_column", "message": f"{dataset_key}: column without name skipped."})
            continue
        item = {
            "name": str(column.get("name")).strip(),
            "type": str(column.get("type") or "string").strip(),
            "description": str(column.get("description") or "").strip(),
        }
        if item["type"] not in VALID_COLUMN_TYPES:
            issues.append(
                {
                    "severity": "warning",
                    "type": "unknown_column_type",
                    "message": f"{dataset_key}.{item['name']}: unknown type '{item['type']}', using string.",
                }
            )
            item["type"] = "string"
        columns.append(item)
    return columns


def _normalize_dataset(dataset_key: str, value: Any, issues: list[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not isinstance(value, dict):
        issues.append({"severity": "error", "type": "invalid_dataset", "message": f"{dataset_key}: dataset must be an object."})
        return None
    dataset = deepcopy(value)
    source = dataset.get("source") if isinstance(dataset.get("source"), dict) else {}
    oracle = dataset.get("oracle") if isinstance(dataset.get("oracle"), dict) else {}
    required_params = _string_list(dataset.get("required_params"))
    if _has_sql_fields(dataset):
        issues.append(
            {
                "severity": "warning",
                "type": "sql_fields_ignored",
                "message": f"{dataset_key}: SQL fields are ignored. Keep SQL in retriever tool functions.",
            }
        )
    normalized = {
        "display_name": str(dataset.get("display_name") or dataset_key).strip(),
        "description": str(dataset.get("description") or "").strip(),
        "keywords": _string_list(dataset.get("keywords")),
        "question_examples": _string_list(dataset.get("question_examples") or dataset.get("example_questions")),
        "tool_name": str(dataset.get("tool_name") or (dataset.get("tool", {}) if isinstance(dataset.get("tool"), dict) else {}).get("name") or f"get_{dataset_key}_data").strip(),
        "source_type": str(dataset.get("source_type") or source.get("type") or "oracle").strip(),
        "required_params": required_params,
        "format_params": _normalize_format_params(dataset, required_params, issues, dataset_key),
        "db_key": str(dataset.get("db_key") or oracle.get("db_key") or "").strip(),
        "table_name": str(dataset.get("table_name") or dataset.get("table") or "").strip(),
        "columns": _normalize_columns(dataset.get("columns"), dataset_key, issues),
    }
    return normalized


def _existing_keyword_owners(existing_table_items: list[Dict[str, Any]]) -> Dict[str, str]:
    owners: Dict[str, str] = {}
    for item in existing_table_items:
        dataset_key = str(item.get("dataset_key") or "")
        for keyword in _string_list(item.get("keywords")):
            owners[keyword.strip().lower()] = dataset_key
    return owners


def normalize_and_validate_table_catalog(
    raw_catalog: Dict[str, Any],
    existing_table_items: list[Dict[str, Any]],
) -> Dict[str, Any]:
    issues: list[Dict[str, Any]] = []
    if not isinstance(raw_catalog, dict):
        return {
            "can_save": False,
            "table_catalog": {"catalog_id": "invalid", "status": "active", "datasets": {}},
            "issues": [{"severity": "error", "type": "invalid_root", "message": "Table catalog root must be an object."}],
        }

    raw_datasets = raw_catalog.get("datasets") if isinstance(raw_catalog.get("datasets"), dict) else {}
    datasets: Dict[str, Any] = {}
    existing_dataset_keys = {str(item.get("dataset_key")) for item in existing_table_items if item.get("dataset_key")}
    keyword_owners = _existing_keyword_owners(existing_table_items)

    for raw_key, raw_dataset in raw_datasets.items():
        dataset_key = str(raw_key or "").strip()
        if not dataset_key:
            issues.append({"severity": "error", "type": "empty_dataset_key", "message": "Dataset key is empty."})
            continue
        dataset = _normalize_dataset(dataset_key, raw_dataset, issues)
        if dataset is None:
            continue
        if dataset_key in existing_dataset_keys:
            issues.append({"severity": "warning", "type": "update_existing", "message": f"{dataset_key} already exists and will be updated."})
        if not dataset["keywords"]:
            issues.append({"severity": "warning", "type": "missing_keywords", "message": f"{dataset_key}: keywords are empty."})
        if dataset["source_type"] == "oracle" and not dataset["db_key"]:
            issues.append({"severity": "error", "type": "missing_db_key", "message": f"{dataset_key}: oracle dataset requires db_key."})
        if not dataset["columns"]:
            issues.append({"severity": "warning", "type": "missing_columns", "message": f"{dataset_key}: columns are empty."})
        missing_format_params = sorted(param for param in dataset["required_params"] if param not in dataset["format_params"])
        if missing_format_params:
            issues.append(
                {
                    "severity": "warning",
                    "type": "required_param_not_formatted",
                    "message": f"{dataset_key}: required_params not listed in format_params {missing_format_params}.",
                }
            )
        for keyword in dataset["keywords"]:
            owner = keyword_owners.get(keyword.strip().lower())
            if owner and owner != dataset_key:
                issues.append({"severity": "error", "type": "keyword_collision", "message": f"Keyword '{keyword}' already belongs to {owner}."})
        datasets[dataset_key] = dataset

    table_catalog = {
        "catalog_id": raw_catalog.get("catalog_id") or "manufacturing_table_catalog",
        "status": raw_catalog.get("status") or "active",
        "datasets": datasets,
    }
    if raw_catalog.get("version"):
        table_catalog["version"] = raw_catalog.get("version")
    return {
        "can_save": bool(datasets) and not any(issue["severity"] == "error" for issue in issues),
        "table_catalog": table_catalog,
        "issues": issues,
        "dataset_count": len(datasets),
    }


def table_catalog_json_text(table_catalog: Dict[str, Any]) -> str:
    return json.dumps(table_catalog, ensure_ascii=False, indent=2)
