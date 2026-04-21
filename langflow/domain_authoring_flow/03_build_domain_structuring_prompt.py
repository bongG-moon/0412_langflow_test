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


def _compact_json(value: Any, limit: int = 4000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED..."


def _keys(value: Any) -> list[str]:
    return list(value.keys()) if isinstance(value, dict) else []


def _existing_domain_summary(domain: Dict[str, Any]) -> Dict[str, Any]:
    join_rule_names = []
    for rule in domain.get("join_rules", []) if isinstance(domain.get("join_rules"), list) else []:
        if isinstance(rule, dict) and rule.get("name"):
            join_rule_names.append(str(rule["name"]))
    return {
        "product_keys": _keys(domain.get("products")),
        "process_group_keys": _keys(domain.get("process_groups")),
        "term_keys": _keys(domain.get("terms")),
        "dataset_keys": _keys(domain.get("datasets")),
        "metric_keys": _keys(domain.get("metrics")),
        "join_rule_names": join_rule_names,
    }


def _compact_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "domain_id": config.get("domain_id") or "manufacturing_default",
        "authoring_mode": config.get("authoring_mode") or "append",
        "target_status": config.get("target_status") or "draft",
    }


def build_domain_structuring_prompt(raw_domain_payload: Any, existing_domain_payload: Any, config_payload: Any) -> str:
    raw_payload = _payload_from_value(raw_domain_payload)
    existing_payload = _payload_from_value(existing_domain_payload)
    config_outer = _payload_from_value(config_payload)
    config = config_outer.get("authoring_config") if isinstance(config_outer.get("authoring_config"), dict) else config_outer

    raw_text = str(raw_payload.get("raw_domain_text") or raw_payload.get("text") or "").strip()
    existing_domain = existing_payload.get("existing_domain")
    if not isinstance(existing_domain, dict):
        existing_document = (
            existing_payload.get("existing_domain_document")
            if isinstance(existing_payload.get("existing_domain_document"), dict)
            else existing_payload.get("domain_document")
        )
        if isinstance(existing_document, dict) and isinstance(existing_document.get("domain"), dict):
            existing_domain = existing_document["domain"]
        else:
            existing_domain = existing_payload.get("domain") if isinstance(existing_payload.get("domain"), dict) else {}

    return f"""You are converting manufacturing domain knowledge into a standard Domain JSON patch.
Return JSON only. Do not include markdown fences.

Return this minimal JSON shape:
{{
  "domain_patch": {{
    "products": {{}},
    "process_groups": {{}},
    "terms": {{}},
    "datasets": {{}},
    "metrics": {{}},
    "join_rules": []
  }},
  "warnings": []
}}

Authoring config:
{_compact_json(_compact_config(config), limit=1000)}

Existing domain keys only:
{_compact_json(_existing_domain_summary(existing_domain), limit=3000)}

Mapping rules:
- Product identity or product family -> domain_patch.products.<key> with display_name, aliases, filters.
- Process grouping -> domain_patch.process_groups.<key> with display_name, aliases, processes.
- Named filter or domain term -> domain_patch.terms.<key> with display_name, aliases, filter.
- Dataset definition or dataset keyword -> domain_patch.datasets.<key> with display_name, keywords, required_params, query_template_id, tool_name, columns.
- Formula, ratio, condition, KPI -> domain_patch.metrics.<key> with aliases, required_datasets, required_columns, source_columns, calculation_mode, formula or condition, output_column, default_group_by.
- Join description -> domain_patch.join_rules item with name, datasets, base_dataset, join_dataset, keys, join_keys, join_type.
- Do not create domain_index.
- Do not include explanations, classification logs, assumptions, preview data, or copied source text.
- Put only uncertain or unsupported facts into warnings.

Raw domain text:
{raw_text}
"""


class BuildDomainStructuringPrompt(Component):
    display_name = "Build Domain Structuring Prompt"
    description = "Create the JSON-only prompt that turns raw domain notes into a standard Domain JSON patch."
    icon = "TextCursorInput"
    name = "BuildDomainStructuringPrompt"

    inputs = [
        DataInput(
            name="raw_domain_payload",
            display_name="Raw Domain Payload",
            info="Output from Raw Domain Input.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="existing_domain",
            display_name="Existing Domain",
            info="Output from MongoDB Active Domain Loader.",
            input_types=["Data", "JSON"],
        ),
        DataInput(
            name="authoring_config",
            display_name="Authoring Config",
            info="Optional override from Domain Authoring Config Input.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="domain_structuring_prompt", display_name="Domain Structuring Prompt", method="build_prompt", types=["Data"]),
    ]

    def build_prompt(self) -> Data:
        prompt = build_domain_structuring_prompt(
            getattr(self, "raw_domain_payload", None),
            getattr(self, "existing_domain", None),
            getattr(self, "authoring_config", None),
        )
        return _make_data({"prompt": prompt})
