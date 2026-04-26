from __future__ import annotations

import ast
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
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
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
            "production": {"display_name": "Production", "description": "Daily production quantity.", "keywords": ["production", "output", "생산", "실적"], "tool_name": "get_production_data", "db_key": "PKG_RPT", "required_params": ["date"]},
            "target": {"display_name": "Target", "description": "Daily target quantity.", "keywords": ["target", "plan", "목표", "계획"], "tool_name": "get_target_data", "db_key": "PKG_RPT", "required_params": ["date"]},
            "wip": {"display_name": "WIP", "description": "Work in process quantity.", "keywords": ["wip", "?ш났"], "tool_name": "get_wip_status", "db_key": "PKG_RPT", "required_params": ["date"]},
            "equipment": {"display_name": "Equipment", "description": "Equipment utilization.", "keywords": ["equipment", "?ㅻ퉬", "媛?숇쪧"], "tool_name": "get_equipment_status", "db_key": "PKG_RPT", "required_params": ["date"]},
        },
    }


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

