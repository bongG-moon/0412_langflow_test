from __future__ import annotations

import json
import re
from copy import deepcopy
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


VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}
SQL_TEXT_KEYS = ("sql_template", "query_template", "sql", "sql_text", "query", "oracle_sql")
TRIPLE_DOUBLE_SQL_BLOCK_RE = re.compile(
    r'(?P<prefix>"(?:sql_template|query_template|sql|sql_text|query|oracle_sql)"\s*:\s*)"""(?P<body>.*?)"""',
    re.DOTALL,
)
TRIPLE_SINGLE_SQL_BLOCK_RE = re.compile(
    r"(?P<prefix>\"(?:sql_template|query_template|sql|sql_text|query|oracle_sql)\"\s*:\s*)'''(?P<body>.*?)'''",
    re.DOTALL,
)


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
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return {"text": content}
    return {}


def _extract_json_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("table_catalog_json", "table_catalog_json_text", "json", "text"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    if payload:
        return json.dumps(payload, ensure_ascii=False)
    return str(value or "").strip()


def _strip_outer_line_breaks(text: str) -> str:
    return text.strip("\r\n")


def _replace_sql_block(match: re.Match[str]) -> str:
    sql_text = _strip_outer_line_breaks(match.group("body"))
    return f"{match.group('prefix')}{json.dumps(sql_text, ensure_ascii=False)}"


def _normalize_relaxed_table_catalog_text(text: str) -> str:
    text = TRIPLE_DOUBLE_SQL_BLOCK_RE.sub(_replace_sql_block, text)
    text = TRIPLE_SINGLE_SQL_BLOCK_RE.sub(_replace_sql_block, text)
    return text


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in _as_list(value) if str(item).strip()]


def _normalize_sql(dataset: Dict[str, Any]) -> str:
    for key in ("sql_template_lines", "query_template_lines", "sql_lines"):
        lines = dataset.get(key)
        if isinstance(lines, list):
            return "\n".join(str(line).rstrip() for line in lines if str(line).strip()).strip()
    for key in SQL_TEXT_KEYS:
        value = dataset.get(key)
        if isinstance(value, list):
            return "\n".join(str(line).rstrip() for line in value if str(line).strip()).strip()
        if isinstance(value, str):
            return value.strip()
    sql = dataset.get("sql") if isinstance(dataset.get("sql"), dict) else {}
    lines = sql.get("lines")
    if isinstance(lines, list):
        return "\n".join(str(line).rstrip() for line in lines if str(line).strip()).strip()
    if isinstance(sql.get("template"), str):
        return sql["template"].strip()
    return ""


def _normalize_columns(value: Any, dataset_key: str, errors: list[str]) -> list[Dict[str, Any]]:
    columns: list[Dict[str, Any]] = []
    for column in _as_list(value):
        if not isinstance(column, dict) or not column.get("name"):
            errors.append(f"Dataset '{dataset_key}' has a column without a name; skipped.")
            continue
        item = dict(column)
        item["name"] = str(item["name"]).strip()
        item.setdefault("type", "string")
        if item["type"] not in VALID_COLUMN_TYPES:
            errors.append(f"Dataset '{dataset_key}' column '{item['name']}' has unknown type '{item['type']}'.")
        columns.append(item)
    return columns


def _normalize_dataset(dataset_key: str, value: Any, errors: list[str]) -> Dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"Dataset '{dataset_key}' must be an object; skipped.")
        return None
    dataset = deepcopy(value)
    dataset["display_name"] = str(dataset.get("display_name") or dataset_key)
    dataset["description"] = str(dataset.get("description") or "")
    dataset["keywords"] = _string_list(dataset.get("keywords"))
    dataset["question_examples"] = _string_list(dataset.get("question_examples") or dataset.get("example_questions"))
    dataset["tool_name"] = str(dataset.get("tool_name") or (dataset.get("tool", {}) if isinstance(dataset.get("tool"), dict) else {}).get("name") or f"get_{dataset_key}_data").strip()
    source = dataset.get("source") if isinstance(dataset.get("source"), dict) else {}
    dataset["source_type"] = str(dataset.get("source_type") or source.get("type") or "oracle").strip()
    dataset["required_params"] = _string_list(dataset.get("required_params"))
    dataset["db_key"] = str(dataset.get("db_key") or (dataset.get("oracle", {}) if isinstance(dataset.get("oracle"), dict) else {}).get("db_key") or "").strip()
    dataset["table_name"] = str(dataset.get("table_name") or dataset.get("table") or "").strip()
    dataset["sql_template"] = _normalize_sql(dataset)
    dataset["bind_params"] = dataset.get("bind_params") if isinstance(dataset.get("bind_params"), dict) else {}
    dataset["columns"] = _normalize_columns(dataset.get("columns"), dataset_key, errors)
    return dataset


def _build_prompt_context(table_catalog: Dict[str, Any]) -> Dict[str, Any]:
    datasets: Dict[str, Any] = {}
    for key, dataset in table_catalog.get("datasets", {}).items():
        if not isinstance(dataset, dict):
            continue
        datasets[key] = {
            "display_name": dataset.get("display_name", key),
            "description": dataset.get("description", ""),
            "keywords": dataset.get("keywords", []),
            "question_examples": dataset.get("question_examples", []),
            "tool_name": dataset.get("tool_name", ""),
            "source_type": dataset.get("source_type", ""),
            "required_params": dataset.get("required_params", []),
            "columns": [
                {
                    "name": column.get("name"),
                    "type": column.get("type", "string"),
                    "description": column.get("description", ""),
                }
                for column in dataset.get("columns", [])
                if isinstance(column, dict) and column.get("name")
            ],
        }
    return {"datasets": datasets}


def load_table_catalog(table_catalog_json_payload: Any) -> Dict[str, Any]:
    errors: list[str] = []
    text = _extract_json_text(table_catalog_json_payload)
    if not text:
        return {
            "table_catalog": {"catalog_id": "empty", "datasets": {}},
            "table_catalog_prompt_context": {"datasets": {}},
            "table_catalog_errors": ["table_catalog_json is empty."],
        }
    try:
        parsed = json.loads(_normalize_relaxed_table_catalog_text(text))
    except Exception as exc:
        return {
            "table_catalog": {"catalog_id": "invalid", "datasets": {}},
            "table_catalog_prompt_context": {"datasets": {}},
            "table_catalog_errors": [
                f"Table catalog JSON parse failed: {exc}",
                'For copy-paste SQL, use: "sql_template": """SELECT ..."""',
            ],
        }
    if not isinstance(parsed, dict):
        return {
            "table_catalog": {"catalog_id": "invalid", "datasets": {}},
            "table_catalog_prompt_context": {"datasets": {}},
            "table_catalog_errors": ["Table catalog JSON root must be an object."],
        }

    raw_datasets = parsed.get("datasets") if isinstance(parsed.get("datasets"), dict) else {}
    datasets: Dict[str, Any] = {}
    for dataset_key, dataset_value in raw_datasets.items():
        key = str(dataset_key or "").strip()
        if not key:
            errors.append("Dataset key is empty; skipped.")
            continue
        dataset = _normalize_dataset(key, dataset_value, errors)
        if dataset is not None:
            datasets[key] = dataset

    table_catalog = {
        "catalog_id": parsed.get("catalog_id") or "manufacturing_table_catalog",
        "status": parsed.get("status") or "active",
        "datasets": datasets,
    }
    return {
        "table_catalog": table_catalog,
        "table_catalog_prompt_context": _build_prompt_context(table_catalog),
        "table_catalog_errors": errors,
    }


class TableCatalogLoader(Component):
    display_name = "Table Catalog Loader"
    description = "Parse and normalize table catalog text for retrieval planning and Oracle execution."
    icon = "TableProperties"
    name = "TableCatalogLoader"

    inputs = [
        DataInput(
            name="table_catalog_json_payload",
            display_name="Table Catalog JSON Payload",
            info='Output from Table Catalog JSON Input. Copy-paste SQL blocks can use "sql_template": """...""".',
            input_types=["Data", "JSON", "Text"],
        ),
    ]

    outputs = [
        Output(name="table_catalog_payload", display_name="Table Catalog Payload", method="build_table_catalog_payload", types=["Data"]),
    ]

    def build_table_catalog_payload(self) -> Data:
        payload = load_table_catalog(getattr(self, "table_catalog_json_payload", None))
        datasets = payload.get("table_catalog", {}).get("datasets", {})
        self.status = {
            "dataset_count": len(datasets) if isinstance(datasets, dict) else 0,
            "error_count": len(payload.get("table_catalog_errors", [])),
        }
        return _make_data(payload)
