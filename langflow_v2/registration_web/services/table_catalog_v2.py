from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any, Dict

from .config import VALID_COLUMN_TYPES, VALID_SOURCE_TYPES
from .domain_v2 import as_list, split_lines


DROP_SQL_KEYS = {"sql", "sql_template", "oracle_sql", "query", "query_template"}


def slug(value: Any, fallback: str = "dataset") -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^0-9a-zA-Z_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def parse_jsonish(value: Any) -> tuple[Any, list[str]]:
    if isinstance(value, (dict, list)):
        return deepcopy(value), []
    raw = str(value or "").strip()
    if not raw:
        return {}, []
    try:
        return json.loads(raw), []
    except Exception as exc:
        return {}, [str(exc)]


def parse_columns(value: Any) -> list[Dict[str, Any]]:
    if isinstance(value, list):
        raw_columns = value
    else:
        raw_columns = []
        for line in str(value or "").splitlines():
            text = line.strip()
            if not text:
                continue
            parts = [part.strip() for part in text.split("|")]
            raw_columns.append({"name": parts[0], "type": parts[1] if len(parts) > 1 else "string", "description": parts[2] if len(parts) > 2 else ""})

    columns: list[Dict[str, Any]] = []
    for column in raw_columns:
        if isinstance(column, str):
            column = {"name": column, "type": "string"}
        if not isinstance(column, dict) or not column.get("name"):
            continue
        column_type = str(column.get("type") or "string").strip().lower()
        if column_type not in VALID_COLUMN_TYPES:
            column_type = "string"
        columns.append(
            {
                "name": str(column.get("name") or "").strip(),
                "type": column_type,
                "description": str(column.get("description") or "").strip(),
            }
        )
    return columns


def normalize_dataset(dataset_key: str, payload: Dict[str, Any], status: str = "active") -> Dict[str, Any]:
    payload = deepcopy(payload) if isinstance(payload, dict) else {}
    for key in DROP_SQL_KEYS:
        payload.pop(key, None)
    dataset_key = slug(dataset_key or payload.get("dataset_key") or payload.get("key"), "dataset")
    source_type = str(payload.get("source_type") or "auto").strip().lower()
    if source_type not in VALID_SOURCE_TYPES:
        source_type = "auto"
    return {
        "dataset_key": dataset_key,
        "status": status or "active",
        "display_name": str(payload.get("display_name") or dataset_key).strip(),
        "description": str(payload.get("description") or "").strip(),
        "source_type": source_type,
        "db_key": str(payload.get("db_key") or "PKG_RPT").strip(),
        "table_name": str(payload.get("table_name") or "").strip(),
        "tool_name": str(payload.get("tool_name") or f"get_{dataset_key}_data").strip(),
        "required_params": split_lines(payload.get("required_params") or ["date"]),
        "format_params": split_lines(payload.get("format_params")),
        "keywords": split_lines(payload.get("keywords")),
        "aliases": split_lines(payload.get("aliases")),
        "question_examples": split_lines(payload.get("question_examples")),
        "columns": parse_columns(payload.get("columns")),
        "source": "langflow_v2_registration_web",
    }


def normalize_table_input(raw_value: Any) -> Dict[str, Any]:
    parsed, errors = parse_jsonish(raw_value)
    items: list[Dict[str, Any]] = []
    if isinstance(parsed, dict) and isinstance(parsed.get("table_catalog"), dict):
        parsed = parsed["table_catalog"]
    if isinstance(parsed, dict) and isinstance(parsed.get("datasets"), dict):
        for key, dataset in parsed["datasets"].items():
            if isinstance(dataset, dict):
                items.append(normalize_dataset(str(key), dataset, str(dataset.get("status") or "active")))
    elif isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
        for item in parsed["items"]:
            if isinstance(item, dict):
                items.append(normalize_dataset(str(item.get("dataset_key") or item.get("key") or ""), item, str(item.get("status") or "active")))
    elif isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                items.append(normalize_dataset(str(item.get("dataset_key") or item.get("key") or ""), item, str(item.get("status") or "active")))
    elif isinstance(parsed, dict) and any(key in parsed for key in ("dataset_key", "display_name", "tool_name")):
        items.append(normalize_dataset(str(parsed.get("dataset_key") or parsed.get("key") or ""), parsed, str(parsed.get("status") or "active")))
    return {"items": items, "errors": errors}


def table_catalog(items: list[Dict[str, Any]]) -> Dict[str, Any]:
    datasets: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if str(item.get("status") or "active") == "deleted":
            continue
        key = str(item.get("dataset_key") or "").strip()
        if not key:
            continue
        dataset = {k: deepcopy(v) for k, v in item.items() if k not in {"dataset_key", "status", "source", "created_at", "updated_at"}}
        for drop_key in DROP_SQL_KEYS:
            dataset.pop(drop_key, None)
        datasets[key] = dataset
    return {"catalog_id": "manufacturing_v2_catalog", "datasets": datasets}


def validate_items(items: list[Dict[str, Any]], existing_items: list[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    existing_items = existing_items or []
    existing_keys = {str(item.get("dataset_key")) for item in existing_items if item.get("dataset_key")}
    seen: set[str] = set()
    issues: list[Dict[str, str]] = []
    for item in items:
        key = str(item.get("dataset_key") or "").strip()
        if not key:
            issues.append({"severity": "error", "message": "Dataset item has no dataset_key."})
            continue
        if key in seen:
            issues.append({"severity": "error", "message": f"{key} appears more than once."})
        if key in existing_keys:
            issues.append({"severity": "warning", "message": f"{key} already exists and will be updated."})
        seen.add(key)
        if not item.get("tool_name"):
            issues.append({"severity": "warning", "message": f"{key} has no tool_name."})
        if not item.get("required_params"):
            issues.append({"severity": "warning", "message": f"{key} has no required_params."})
    return {"can_save": bool(items) and not any(issue["severity"] == "error" for issue in issues), "issues": issues}
