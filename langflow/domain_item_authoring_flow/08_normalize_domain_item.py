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


VALID_GBNS = {"products", "process_groups", "terms", "datasets", "metrics", "join_rules"}
VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}
VALID_JOIN_TYPES = {"left", "inner", "right", "outer"}
VALID_CALCULATION_MODES = {"ratio", "difference", "sum", "mean", "count", "condition_flag", "threshold_flag", "custom", ""}


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


def _string_list(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _slug(value: Any, fallback: str = "domain_item") -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^0-9a-zA-Z가-힣_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def _norm_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return text


def _payload(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload")
    return deepcopy(payload) if isinstance(payload, dict) else {}


def _base_key(item: Dict[str, Any], payload: Dict[str, Any], gbn: str) -> str:
    for key in ("key", "name"):
        if str(item.get(key) or "").strip():
            return _slug(item[key], gbn)
    for key in ("display_name", "canonical", "base_dataset"):
        if str(payload.get(key) or "").strip():
            if gbn == "join_rules" and payload.get("base_dataset") and payload.get("join_dataset"):
                return _slug(f"{payload.get('base_dataset')}_{payload.get('join_dataset')}_join", gbn)
            return _slug(payload[key], gbn)
    return gbn.rstrip("s")


def _normalize_payload(gbn: str, payload: Dict[str, Any], warnings: list[str]) -> Dict[str, Any]:
    if gbn == "products":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "filters": payload.get("filters") if isinstance(payload.get("filters"), dict) else {},
        }
    if gbn == "process_groups":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "processes": _string_list(payload.get("processes")),
        }
    if gbn == "terms":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "filter": payload.get("filter") if isinstance(payload.get("filter"), dict) else {},
        }
    if gbn == "datasets":
        columns = []
        for column in _as_list(payload.get("columns")):
            if not isinstance(column, dict) or not column.get("name"):
                continue
            item = {"name": str(column.get("name")).strip(), "type": str(column.get("type") or "string").strip()}
            if item["type"] not in VALID_COLUMN_TYPES:
                warnings.append(f"Unknown column type '{item['type']}' for column '{item['name']}'.")
                item["type"] = "string"
            columns.append(item)
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "keywords": _string_list(payload.get("keywords")),
            "required_params": _string_list(payload.get("required_params")),
            "query_template_id": str(payload.get("query_template_id") or "").strip(),
            "tool_name": str(payload.get("tool_name") or "").strip(),
            "columns": columns,
        }
    if gbn == "metrics":
        mode = str(payload.get("calculation_mode") or "").strip()
        if mode not in VALID_CALCULATION_MODES:
            warnings.append(f"Unknown calculation_mode '{mode}'.")
            mode = "custom"
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "required_datasets": _string_list(payload.get("required_datasets")),
            "required_columns": _string_list(payload.get("required_columns")),
            "source_columns": [item for item in _as_list(payload.get("source_columns")) if isinstance(item, dict)],
            "calculation_mode": mode,
            "formula": str(payload.get("formula") or "").strip(),
            "condition": str(payload.get("condition") or "").strip(),
            "output_column": str(payload.get("output_column") or "").strip(),
            "default_group_by": _string_list(payload.get("default_group_by")),
            "pandas_hint": str(payload.get("pandas_hint") or "").strip(),
        }
    if gbn == "join_rules":
        join_type = str(payload.get("join_type") or "left").strip().lower()
        if join_type not in VALID_JOIN_TYPES:
            warnings.append(f"Unknown join_type '{join_type}'.")
            join_type = "left"
        return {
            "base_dataset": str(payload.get("base_dataset") or "").strip(),
            "join_dataset": str(payload.get("join_dataset") or "").strip(),
            "join_type": join_type,
            "join_keys": _string_list(payload.get("join_keys") or payload.get("keys")),
            "description": str(payload.get("description") or "").strip(),
        }
    return payload


def _aliases_for(gbn: str, key: str, payload: Dict[str, Any]) -> list[str]:
    aliases = [key]
    if payload.get("display_name"):
        aliases.append(str(payload["display_name"]))
    aliases.extend(_string_list(payload.get("aliases")))
    if gbn == "process_groups":
        aliases.extend(_string_list(payload.get("processes")))
    return list(dict.fromkeys(_norm_token(item) for item in aliases if _norm_token(item)))


def _keywords_for(gbn: str, payload: Dict[str, Any]) -> list[str]:
    if gbn != "datasets":
        return []
    return list(dict.fromkeys(_norm_token(item) for item in _string_list(payload.get("keywords")) if _norm_token(item)))


def normalize_domain_items(raw_items_value: Any, route_value: Any = None) -> Dict[str, Any]:
    raw_payload = _payload_from_value(raw_items_value)
    route_payload = _payload_from_value(route_value)
    raw_text = str(route_payload.get("raw_text") or "").strip()
    raw_notes = route_payload.get("raw_notes") if isinstance(route_payload.get("raw_notes"), list) else []
    note_text_by_id = {
        str(note.get("note_id")): str(note.get("raw_text") or "")
        for note in raw_notes
        if isinstance(note, dict) and note.get("note_id")
    }
    candidates = raw_payload.get("domain_items_raw") if isinstance(raw_payload.get("domain_items_raw"), list) else []
    normalized: list[Dict[str, Any]] = []
    errors = list(raw_payload.get("parse_errors") or [])
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        gbn = str(candidate.get("gbn") or "").strip()
        if gbn not in VALID_GBNS:
            errors.append(f"Unsupported gbn '{gbn}' skipped.")
            continue
        warnings = [str(item) for item in _as_list(candidate.get("warnings")) if str(item).strip()]
        payload = _normalize_payload(gbn, _payload(candidate), warnings)
        key = _base_key(candidate, payload, gbn)
        source_note_id = str(candidate.get("source_note_id") or "").strip()
        source_text = note_text_by_id.get(source_note_id) or raw_text
        normalized.append(
            {
                "gbn": gbn,
                "key": key,
                "status": "active",
                "payload": payload,
                "normalized_aliases": _aliases_for(gbn, key, payload),
                "normalized_keywords": _keywords_for(gbn, payload),
                "source_note_id": source_note_id,
                "source_text": source_text,
                "warnings": warnings,
            }
        )
    if not normalized and not errors:
        errors.append("No valid domain items were extracted.")
    return {
        "normalized_domain_items": normalized,
        "normalization_errors": errors,
        "unmapped_text": raw_payload.get("unmapped_text", ""),
    }


class NormalizeDomainItem(Component):
    display_name = "Normalize Domain Item"
    description = "Normalize raw LLM item candidates into compact MongoDB domain item documents."
    icon = "WandSparkles"
    name = "NormalizeDomainItem"

    inputs = [
        DataInput(name="domain_items_raw", display_name="Domain Items Raw", info="Output from Parse Domain Item JSON.", input_types=["Data", "JSON"]),
        DataInput(name="route_payload", display_name="Route Payload", info="Output from Domain Item Router.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="normalized_domain_items", display_name="Normalized Domain Items", method="build_items", types=["Data"]),
    ]

    def build_items(self) -> Data:
        return _make_data(normalize_domain_items(getattr(self, "domain_items_raw", None), getattr(self, "route_payload", None)))
