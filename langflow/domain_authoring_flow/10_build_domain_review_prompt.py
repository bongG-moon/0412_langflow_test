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


def _compact_json(value: Any, limit: int = 10000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED..."


def _domain_from_existing(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    document = payload.get("existing_domain_document") if isinstance(payload.get("existing_domain_document"), dict) else {}
    if isinstance(document.get("domain"), dict):
        return document["domain"]
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else {}


def _patch_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    patch = payload.get("normalized_domain_patch")
    if isinstance(patch, dict):
        return patch
    patch = payload.get("domain_patch")
    return patch if isinstance(patch, dict) else {}


def _validation_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    validation = payload.get("validation")
    return validation if isinstance(validation, dict) else {}


def _summary_items(items: Any, fields: tuple[str, ...], limit: int = 80) -> Dict[str, Dict[str, Any]]:
    if not isinstance(items, dict):
        return {}
    summary: Dict[str, Dict[str, Any]] = {}
    for key, value in list(items.items())[:limit]:
        if not isinstance(value, dict):
            continue
        summary[str(key)] = {field: value.get(field) for field in fields if value.get(field) not in (None, "", [], {})}
    return summary


def _join_rule_summary(rules: Any, limit: int = 80) -> list[Dict[str, Any]]:
    summary: list[Dict[str, Any]] = []
    for rule in _as_list(rules)[:limit]:
        if not isinstance(rule, dict):
            continue
        summary.append(
            {
                key: rule.get(key)
                for key in ("name", "datasets", "base_dataset", "join_dataset", "keys", "join_type")
                if rule.get(key) not in (None, "", [], {})
            }
        )
    return summary


def _domain_review_summary(domain: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "products": _summary_items(domain.get("products"), ("display_name", "aliases", "filters")),
        "process_groups": _summary_items(domain.get("process_groups"), ("display_name", "aliases", "processes")),
        "terms": _summary_items(domain.get("terms"), ("display_name", "aliases", "filter")),
        "datasets": _summary_items(domain.get("datasets"), ("display_name", "keywords", "required_params", "columns")),
        "metrics": _summary_items(
            domain.get("metrics"),
            ("display_name", "aliases", "required_datasets", "required_columns", "formula", "condition", "output_column"),
        ),
        "join_rules": _join_rule_summary(domain.get("join_rules")),
    }


def build_domain_review_prompt(
    existing_domain_value: Any,
    normalized_patch_value: Any,
    conflict_report_value: Any,
    validated_domain_value: Any,
) -> str:
    existing_domain = _domain_from_existing(existing_domain_value)
    patch = _patch_from_value(normalized_patch_value)
    conflict_report = _payload_from_value(conflict_report_value)
    validation = _validation_from_value(validated_domain_value)
    schema = {
        "semantic_review": {
            "semantic_conflicts": [
                {
                    "type": "possible_duplicate_metric | possible_duplicate_term | possible_duplicate_dataset | meaning_conflict | formula_meaning_conflict",
                    "existing_key": "",
                    "new_key": "",
                    "reason": "",
                    "severity": "low | medium | high",
                }
            ],
            "semantic_warnings": [],
            "recommended_status": "active | review_required | rejected",
            "confidence": 0.0,
        }
    }

    return f"""You are reviewing manufacturing domain changes before MongoDB storage.
Return ONLY one valid JSON object. Do not include markdown fences.

Review goal:
- Find semantic duplicates or meaning conflicts that simple code rules may miss.
- Focus on products, process groups, terms, datasets, metrics, formulas, and join rules.
- Use review_required when the new patch may duplicate or contradict existing domain knowledge.
- Use active only when the patch is semantically safe to store and use.
- Use rejected only for clearly invalid or dangerous domain definitions.
- Do not repeat full input data in the output.

Output JSON schema:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Existing active domain summary:
{_compact_json(_domain_review_summary(existing_domain), limit=12000)}

New normalized domain patch summary:
{_compact_json(_domain_review_summary(patch), limit=12000)}

Rule-based conflict report:
{_compact_json(conflict_report, limit=5000)}

Schema validation result:
{_compact_json(validation, limit=5000)}
"""


class BuildDomainReviewPrompt(Component):
    display_name = "Build Domain Review Prompt"
    description = "Create a compact prompt for semantic review of a domain patch before MongoDB storage."
    icon = "TextCursorInput"
    name = "BuildDomainReviewPrompt"

    inputs = [
        DataInput(name="existing_domain", display_name="Existing Domain", info="Output from MongoDB Active Domain Loader.", input_types=["Data", "JSON"]),
        DataInput(name="normalized_domain_patch", display_name="Normalized Domain Patch", info="Output from Normalize Domain Patch.", input_types=["Data", "JSON"]),
        DataInput(name="conflict_report", display_name="Conflict Report", info="Output from Domain Conflict Detector.", input_types=["Data", "JSON"]),
        DataInput(name="validated_domain", display_name="Validated Domain", info="Output from Domain Schema Validator.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="review_prompt", display_name="Review Prompt", method="build_prompt", types=["Data"]),
    ]

    def build_prompt(self) -> Data:
        prompt = build_domain_review_prompt(
            getattr(self, "existing_domain", None),
            getattr(self, "normalized_domain_patch", None),
            getattr(self, "conflict_report", None),
            getattr(self, "validated_domain", None),
        )
        return _make_data({"prompt": prompt})
