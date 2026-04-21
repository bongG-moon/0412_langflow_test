from __future__ import annotations

import json
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


VALID_GBNS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
ITEM_SCHEMAS = {
    "products": {
        "gbn": "products",
        "key": "short_unique_product_or_family_key",
        "payload": {
            "display_name": "user-facing product/family name",
            "aliases": ["synonym"],
            "filters": {"column_name": ["value"]},
        },
    },
    "process_groups": {
        "gbn": "process_groups",
        "key": "short_unique_process_group_key",
        "payload": {
            "display_name": "process group name",
            "aliases": ["synonym"],
            "processes": ["actual OPER_NAME value"],
        },
    },
    "terms": {
        "gbn": "terms",
        "key": "short_unique_term_key",
        "payload": {
            "display_name": "term name",
            "aliases": ["synonym"],
            "filter": {"field": "column_name", "operator": "in", "values": ["value"]},
        },
    },
    "datasets": {
        "gbn": "datasets",
        "key": "dataset_key",
        "payload": {
            "display_name": "dataset display name",
            "keywords": ["question keyword"],
            "required_params": ["date"],
            "query_template_id": "query template id",
            "tool_name": "query tool name",
            "columns": [{"name": "column_name", "type": "string|number|date|datetime|boolean"}],
        },
    },
    "metrics": {
        "gbn": "metrics",
        "key": "metric_key",
        "payload": {
            "display_name": "metric display name",
            "aliases": ["metric synonym"],
            "required_datasets": ["dataset_key"],
            "required_columns": ["column_name"],
            "source_columns": [{"dataset_key": "dataset_key", "column": "column_name", "role": "numerator"}],
            "calculation_mode": "ratio|difference|sum|mean|count|condition_flag|threshold_flag|custom",
            "formula": "calculation expression",
            "condition": "",
            "output_column": "result column",
            "default_group_by": ["OPER_NAME"],
            "pandas_hint": "short pandas-oriented hint",
        },
    },
    "join_rules": {
        "gbn": "join_rules",
        "key": "base_join_join_dataset_join",
        "payload": {
            "base_dataset": "dataset_key",
            "join_dataset": "dataset_key",
            "join_type": "left|inner|right|outer",
            "join_keys": ["WORK_DT", "OPER_NAME"],
            "description": "when to use this join",
        },
    },
}


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
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _compact_json(value: Any, limit: int = 6000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED..."


def _routes(route_payload: Dict[str, Any]) -> list[str]:
    routes = [str(item) for item in _as_list(route_payload.get("routes")) if str(item) in VALID_GBNS]
    primary = str(route_payload.get("primary_gbn") or "")
    if primary in VALID_GBNS:
        routes.append(primary)
    return list(dict.fromkeys(routes)) or list(VALID_GBNS)


def build_prompt_context(route_value: Any, existing_items_value: Any) -> Dict[str, Any]:
    route_payload = _payload_from_value(route_value)
    existing_payload = _payload_from_value(existing_items_value)
    routes = _routes(route_payload)
    raw_text = str(route_payload.get("raw_text") or "").strip()
    raw_notes = route_payload.get("raw_notes") if isinstance(route_payload.get("raw_notes"), list) else []
    existing_items = existing_payload.get("existing_items") if isinstance(existing_payload.get("existing_items"), dict) else {}
    schemas = {gbn: ITEM_SCHEMAS[gbn] for gbn in routes if gbn in ITEM_SCHEMAS}
    output_schema = {
        "items": [
            {
                "gbn": "one of selected gbn values",
                "source_note_id": "note id from raw_notes when available",
                "key": "stable unique key",
                "payload": {},
                "warnings": [],
            }
        ],
        "unmapped_text": "",
    }
    template_vars = {
        "routes": ", ".join(routes),
        "item_schemas": _compact_json(schemas, limit=8000),
        "existing_items": _compact_json(existing_items, limit=6000),
        "raw_notes": _compact_json(raw_notes, limit=6000),
        "raw_text": raw_text,
        "output_schema": _compact_json(output_schema, limit=2000),
    }
    return {
        "routes": routes,
        "raw_text": raw_text,
        "raw_notes": raw_notes,
        "template_vars": template_vars,
        "prompt_context": {
            "selected_routes": routes,
            "item_schemas": schemas,
            "existing_items": existing_items,
            "raw_notes": raw_notes,
            "output_schema": output_schema,
        },
    }


class DomainItemPromptContextBuilder(Component):
    display_name = "Domain Item Prompt Context Builder"
    description = "Build compact variables for Prompt Template from route, schemas, existing items, and raw text."
    icon = "Braces"
    name = "DomainItemPromptContextBuilder"

    inputs = [
        DataInput(name="route_payload", display_name="Route Payload", info="Output from Domain Item Router or Smart Router.", input_types=["Data", "JSON"]),
        DataInput(name="existing_items", display_name="Existing Items", info="Output from MongoDB Existing Domain Item Loader.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="prompt_context", display_name="Prompt Context", method="build_context", types=["Data"]),
    ]

    def build_context(self) -> Data:
        return _make_data(build_prompt_context(getattr(self, "route_payload", None), getattr(self, "existing_items", None)))
