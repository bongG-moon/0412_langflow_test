from __future__ import annotations

import ast
import json
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import MultilineInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


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


def _default_catalog() -> Dict[str, Any]:
    return {
        "catalog_id": "manufacturing_v2_default",
        "datasets": {
            "production": {"display_name": "Production", "description": "Daily production quantity.", "keywords": ["production", "output", "생산", "실적"], "tool_name": "get_production_data", "db_key": "PKG_RPT", "required_params": ["date"], "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "MODE"}, {"name": "LINE"}, {"name": "DEN"}, {"name": "TECH"}, {"name": "MCP_NO"}, {"name": "production"}], "filter_mappings": {"process_name": ["OPER_NAME"], "mode": ["MODE"], "line": ["LINE"], "den": ["DEN"], "tech": ["TECH"], "mcp_no": ["MCP_NO"], "product_name": ["MCP_NO", "MODE", "DEN", "TECH"]}},
            "target": {"display_name": "Target", "description": "Daily target quantity.", "keywords": ["target", "plan", "목표", "계획"], "tool_name": "get_target_data", "db_key": "PKG_RPT", "required_params": ["date"], "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "MODE"}, {"name": "LINE"}, {"name": "DEN"}, {"name": "TECH"}, {"name": "MCP_NO"}, {"name": "target"}], "filter_mappings": {"process_name": ["OPER_NAME"], "mode": ["MODE"], "line": ["LINE"], "den": ["DEN"], "tech": ["TECH"], "mcp_no": ["MCP_NO"], "product_name": ["MCP_NO", "MODE", "DEN", "TECH"]}},
            "wip": {"display_name": "WIP", "description": "Work in process quantity.", "keywords": ["wip", "?ш났"], "tool_name": "get_wip_status", "db_key": "PKG_RPT", "required_params": ["date"], "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "MODE"}, {"name": "LINE"}, {"name": "wip_qty"}], "filter_mappings": {"process_name": ["OPER_NAME"], "mode": ["MODE"], "line": ["LINE"]}},
            "equipment": {"display_name": "Equipment", "description": "Equipment utilization.", "keywords": ["equipment", "?ㅻ퉬", "媛?숇쪧"], "tool_name": "get_equipment_status", "db_key": "PKG_RPT", "required_params": ["date"], "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "EQUIPMENT_ID"}, {"name": "utilization_rate"}], "filter_mappings": {"process_name": ["OPER_NAME"], "equipment_id": ["EQUIPMENT_ID"]}},
        },
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _normalize_columns(value: Any) -> list[Dict[str, Any]]:
    columns = []
    for item in _as_list(value):
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("column") or "").strip()
            if name:
                columns.append({**deepcopy(item), "name": name})
        elif str(item or "").strip():
            columns.append({"name": str(item).strip()})
    return columns


def _normalize_filter_mappings(value: Any) -> Dict[str, list[str]]:
    mappings: Dict[str, list[str]] = {}
    if not isinstance(value, dict):
        return mappings
    for key, raw_columns in value.items():
        columns = []
        if isinstance(raw_columns, dict):
            raw_columns = raw_columns.get("columns") or raw_columns.get("column") or raw_columns.get("names")
        for column in _as_list(raw_columns):
            text = str(column or "").strip()
            if text and text not in columns:
                columns.append(text)
        if str(key).strip() and columns:
            mappings[str(key).strip()] = columns
    return mappings


def load_table_catalog(table_catalog_json: Any) -> Dict[str, Any]:
    parsed, errors = _parse_jsonish(table_catalog_json)
    if isinstance(parsed, dict) and isinstance(parsed.get("table_catalog"), dict):
        catalog = deepcopy(parsed["table_catalog"])
    elif isinstance(parsed, dict) and isinstance(parsed.get("datasets"), dict):
        catalog = deepcopy(parsed)
    else:
        catalog = _default_catalog()
    datasets = catalog.get("datasets") if isinstance(catalog.get("datasets"), dict) else {}
    for key, dataset in list(datasets.items()):
        if not isinstance(dataset, dict):
            datasets.pop(key, None)
            continue
        dataset.pop("sql", None)
        dataset.pop("sql_template", None)
        dataset.pop("oracle_sql", None)
        dataset.setdefault("tool_name", f"get_{key}_data")
        dataset.setdefault("required_params", ["date"])
        dataset.setdefault("db_key", "PKG_RPT")
        dataset["columns"] = _normalize_columns(dataset.get("columns"))
        dataset["filter_mappings"] = _normalize_filter_mappings(dataset.get("filter_mappings"))
    return {"table_catalog_payload": {"table_catalog": catalog, "table_catalog_errors": errors}}


class TableCatalogLoader(Component):
    display_name = "Table Catalog Loader"
    description = "Standalone metadata-only table catalog loader. SQL fields are dropped."
    icon = "Table"
    name = "TableCatalogLoader"

    inputs = [
        MultilineInput(name="table_catalog_json", display_name="Table Catalog JSON", value=json.dumps(_default_catalog(), ensure_ascii=False, indent=2))
    ]
    outputs = [Output(name="table_catalog_payload", display_name="Table Catalog Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = load_table_catalog(getattr(self, "table_catalog_json", ""))
        catalog = payload["table_catalog_payload"]["table_catalog"]
        datasets = catalog.get("datasets", {}) if isinstance(catalog.get("datasets"), dict) else {}
        self.status = {"dataset_count": len(datasets), "errors": len(payload["table_catalog_payload"].get("table_catalog_errors", []))}
        return _make_data(payload)

