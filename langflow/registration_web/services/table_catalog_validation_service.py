from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any, Dict

from .config import VALID_COLUMN_TYPES


SQL_BIND_RE = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")


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


def _normalize_sql(dataset: Dict[str, Any]) -> str:
    for key in ("sql_template_lines", "query_template_lines", "sql_lines"):
        lines = dataset.get(key)
        if isinstance(lines, list):
            return "\n".join(str(line).rstrip() for line in lines if str(line).strip()).strip()
    for key in ("sql_template", "query_template", "sql", "sql_text", "query", "oracle_sql"):
        value = dataset.get(key)
        if isinstance(value, list):
            return "\n".join(str(line).rstrip() for line in value if str(line).strip()).strip()
        if isinstance(value, str):
            return value.strip()
    sql = dataset.get("sql") if isinstance(dataset.get("sql"), dict) else {}
    if isinstance(sql.get("lines"), list):
        return "\n".join(str(line).rstrip() for line in sql["lines"] if str(line).strip()).strip()
    if isinstance(sql.get("template"), str):
        return sql["template"].strip()
    return ""


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
    normalized = {
        "display_name": str(dataset.get("display_name") or dataset_key).strip(),
        "description": str(dataset.get("description") or "").strip(),
        "keywords": _string_list(dataset.get("keywords")),
        "question_examples": _string_list(dataset.get("question_examples") or dataset.get("example_questions")),
        "tool_name": str(dataset.get("tool_name") or (dataset.get("tool", {}) if isinstance(dataset.get("tool"), dict) else {}).get("name") or f"get_{dataset_key}_data").strip(),
        "source_type": str(dataset.get("source_type") or source.get("type") or "oracle").strip(),
        "required_params": _string_list(dataset.get("required_params")),
        "db_key": str(dataset.get("db_key") or oracle.get("db_key") or "").strip(),
        "table_name": str(dataset.get("table_name") or dataset.get("table") or "").strip(),
        "sql_template": _normalize_sql(dataset),
        "bind_params": dataset.get("bind_params") if isinstance(dataset.get("bind_params"), dict) else {},
        "columns": _normalize_columns(dataset.get("columns"), dataset_key, issues),
    }
    return normalized


def _sql_binds(sql_template: str) -> set[str]:
    return set(SQL_BIND_RE.findall(sql_template or ""))


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
        if not dataset["sql_template"]:
            issues.append({"severity": "error", "type": "missing_sql", "message": f"{dataset_key}: sql_template is empty."})
        if not dataset["columns"]:
            issues.append({"severity": "warning", "type": "missing_columns", "message": f"{dataset_key}: columns are empty."})

        binds = _sql_binds(dataset["sql_template"])
        bind_params = {str(key): str(value) for key, value in dataset["bind_params"].items()}
        missing_bind_params = sorted(bind for bind in binds if bind not in bind_params)
        if missing_bind_params:
            issues.append(
                {
                    "severity": "error",
                    "type": "missing_bind_params",
                    "message": f"{dataset_key}: bind_params missing SQL binds {missing_bind_params}.",
                }
            )
        mapped_params = set(bind_params.values())
        missing_required = sorted(param for param in dataset["required_params"] if param not in mapped_params)
        if missing_required and binds:
            issues.append(
                {
                    "severity": "warning",
                    "type": "required_param_not_mapped",
                    "message": f"{dataset_key}: required_params not mapped by bind_params {missing_required}.",
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
    return {
        "can_save": bool(datasets) and not any(issue["severity"] == "error" for issue in issues),
        "table_catalog": table_catalog,
        "issues": issues,
        "dataset_count": len(datasets),
    }


def table_catalog_json_text(table_catalog: Dict[str, Any]) -> str:
    return json.dumps(table_catalog, ensure_ascii=False, indent=2)
