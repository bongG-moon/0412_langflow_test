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


def _unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _default_filters() -> Dict[str, Any]:
    return {
        "filter_set_id": "manufacturing_main_flow_default",
        "description": "Standard semantic filters and required retrieval parameters. Put value expansion rules in domain.process_groups.",
        "required_params": {
            "date": {
                "display_name": "Date",
                "description": "Work date used as a retrieval boundary.",
                "value_type": "date",
                "value_shape": "scalar",
                "normalized_format": "YYYYMMDD",
                "aliases": ["date", "work_date", "WORK_DT", "일자", "날짜"],
            },
        },
        "filters": {
            "process_name": {
                "display_name": "Process",
                "description": "Manufacturing process or operation name.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["process", "process_name", "process_nm", "oper", "operation", "process label"],
            },
            "mode": {
                "display_name": "Mode",
                "description": "Product mode or product family.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["mode", "product mode"],
            },
            "line": {
                "display_name": "Line",
                "description": "Manufacturing line.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["line", "line_name"],
            },
            "product_name": {
                "display_name": "Product",
                "description": "Product name or product-like identifier.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["product", "product_name", "part", "device"],
            },
            "equipment_id": {
                "display_name": "Equipment ID",
                "description": "Equipment, tool, or machine identifier.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["equipment", "equipment_id", "eqp", "tool"],
            },
            "den": {
                "display_name": "Density",
                "description": "Memory density.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["den", "density"],
            },
            "tech": {
                "display_name": "Technology",
                "description": "Product or package technology.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["tech", "technology"],
            },
            "mcp_no": {
                "display_name": "MCP No",
                "description": "MCP or product code.",
                "value_type": "string",
                "value_shape": "list",
                "operator": "in",
                "aliases": ["mcp", "mcp_no", "mcp number"],
            },
        },
    }


def _normalize_filter(key: str, value: Any) -> Dict[str, Any]:
    payload = deepcopy(value) if isinstance(value, dict) else {"description": str(value or "")}
    aliases = _unique_strings([key, *_as_list(payload.get("aliases"))])
    known_values = _unique_strings(_as_list(payload.get("known_values") or payload.get("values")))
    value_aliases = payload.get("value_aliases") if isinstance(payload.get("value_aliases"), dict) else {}
    normalized_aliases = {}
    for alias, alias_values in value_aliases.items():
        values = _unique_strings(_as_list(alias_values))
        if str(alias).strip() and values:
            normalized_aliases[str(alias).strip()] = values

    normalized = {
        "display_name": str(payload.get("display_name") or key).strip(),
        "description": str(payload.get("description") or "").strip(),
        "value_type": str(payload.get("value_type") or "string").strip(),
        "value_shape": str(payload.get("value_shape") or "list").strip(),
        "operator": str(payload.get("operator") or "in").strip(),
        "aliases": aliases,
    }
    if known_values:
        normalized["known_values"] = known_values
    if normalized_aliases:
        normalized["value_aliases"] = normalized_aliases
    return normalized


def _normalize_required_param(key: str, value: Any) -> Dict[str, Any]:
    payload = deepcopy(value) if isinstance(value, dict) else {"description": str(value or "")}
    return {
        "display_name": str(payload.get("display_name") or key).strip(),
        "description": str(payload.get("description") or "").strip(),
        "value_type": str(payload.get("value_type") or "string").strip(),
        "value_shape": str(payload.get("value_shape") or "scalar").strip(),
        "normalized_format": str(payload.get("normalized_format") or payload.get("format") or "").strip(),
        "aliases": _unique_strings([key, *_as_list(payload.get("aliases"))]),
    }


def load_main_flow_filters(main_flow_filters_json: Any) -> Dict[str, Any]:
    parsed, errors = _parse_jsonish(main_flow_filters_json)
    if isinstance(parsed, dict) and isinstance(parsed.get("main_flow_filters"), dict):
        config = deepcopy(parsed["main_flow_filters"])
    elif isinstance(parsed, dict) and isinstance(parsed.get("filters"), dict):
        config = deepcopy(parsed)
    elif isinstance(parsed, dict) and parsed:
        config = {"filters": deepcopy(parsed)}
    else:
        config = _default_filters()

    filters = config.get("filters") if isinstance(config.get("filters"), dict) else {}
    required_params = config.get("required_params") if isinstance(config.get("required_params"), dict) else {}
    default_filters = _default_filters()["filters"]
    default_required_params = _default_filters()["required_params"]
    merged = {key: deepcopy(value) for key, value in default_filters.items()}
    merged.update({str(key): value for key, value in filters.items() if isinstance(value, dict)})
    merged_required_params = {key: deepcopy(value) for key, value in default_required_params.items()}
    merged_required_params.update({str(key): value for key, value in required_params.items() if isinstance(value, dict)})
    config["required_params"] = {key: _normalize_required_param(key, value) for key, value in merged_required_params.items()}
    config["filters"] = {key: _normalize_filter(key, value) for key, value in merged.items()}
    return {"main_flow_filters_payload": {"main_flow_filters": config, "main_flow_filter_errors": errors}}


class MainFlowFiltersLoader(Component):
    display_name = "Main Flow Filters Loader"
    description = "Load standard semantic filters used for intent planning and follow-up inheritance."
    icon = "ListFilter"
    name = "MainFlowFiltersLoader"

    inputs = [
        MultilineInput(name="main_flow_filters_json", display_name="Main Flow Filters JSON", value=json.dumps(_default_filters(), ensure_ascii=False, indent=2))
    ]
    outputs = [Output(name="main_flow_filters_payload", display_name="Main Flow Filters Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = load_main_flow_filters(getattr(self, "main_flow_filters_json", ""))
        filters = payload["main_flow_filters_payload"]["main_flow_filters"].get("filters", {})
        self.status = {"filter_count": len(filters), "errors": len(payload["main_flow_filters_payload"].get("main_flow_filter_errors", []))}
        return _make_data(payload)
