from __future__ import annotations

import json
import re
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
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


ROOT_KEYS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}


def _make_data(payload: Dict[str, Any], text: str | None = None) -> Any:
    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload, text=text)


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


def _normalize_alias(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _extract_json_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    if payload:
        for key in ("domain_json_text", "domain_json", "text"):
            if isinstance(payload.get(key), str):
                return payload[key].strip()
        return json.dumps(payload, ensure_ascii=False)
    return str(value or "").strip()


def _parse_domain_json(domain_json_text: Any) -> tuple[Dict[str, Any], list[str]]:
    errors: list[str] = []
    text = _extract_json_text(domain_json_text)
    if not text:
        errors.append("domain_json_text is empty.")
        return {}, errors
    try:
        parsed = json.loads(text)
    except Exception as exc:
        errors.append(f"Domain JSON parse failed: {exc}")
        return {}, errors
    if not isinstance(parsed, dict):
        errors.append("Domain JSON root must be an object.")
        return {}, errors
    return parsed, errors


def _normalize_domain_document(parsed: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
    errors: list[str] = []
    source = deepcopy(parsed)
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    metadata = {key: value for key, value in metadata.items() if key != "timezone"}
    if isinstance(source.get("domain"), dict):
        domain = deepcopy(source["domain"])
        document = {
            "domain_id": source.get("domain_id") or "manufacturing_default",
            "status": source.get("status") or "active",
            "metadata": metadata,
            "domain": domain,
        }
    else:
        domain = {key: deepcopy(source.get(key)) for key in ROOT_KEYS if key in source}
        document = {
            "domain_id": source.get("domain_id") or "manufacturing_default",
            "status": source.get("status") or "active",
            "metadata": metadata,
            "domain": domain,
        }

    domain = document["domain"]
    for key in ("products", "process_groups", "terms", "datasets", "metrics"):
        if not isinstance(domain.get(key), dict):
            domain[key] = {}
    if not isinstance(domain.get("join_rules"), list):
        domain["join_rules"] = []

    for dataset_key, dataset in list(domain["datasets"].items()):
        if not isinstance(dataset, dict):
            errors.append(f"Dataset '{dataset_key}' must be an object; skipped.")
            domain["datasets"].pop(dataset_key, None)
            continue
        dataset.setdefault("display_name", dataset_key)
        dataset["keywords"] = [str(item) for item in _as_list(dataset.get("keywords")) if str(item).strip()]
        dataset["required_params"] = [
            str(item) for item in _as_list(dataset.get("required_params")) if str(item).strip()
        ]
        columns = dataset.get("columns")
        if not isinstance(columns, list):
            dataset["columns"] = []
            continue
        normalized_columns = []
        for column in columns:
            if not isinstance(column, dict) or not column.get("name"):
                errors.append(f"Dataset '{dataset_key}' has a column without a name; skipped.")
                continue
            column = dict(column)
            column.setdefault("type", "string")
            if column["type"] not in VALID_COLUMN_TYPES:
                errors.append(
                    f"Dataset '{dataset_key}' column '{column['name']}' has unknown type '{column['type']}'."
                )
            normalized_columns.append(column)
        dataset["columns"] = normalized_columns

    for metric_key, metric in list(domain["metrics"].items()):
        if not isinstance(metric, dict):
            errors.append(f"Metric '{metric_key}' must be an object; skipped.")
            domain["metrics"].pop(metric_key, None)
            continue
        metric.setdefault("display_name", metric_key)
        metric["aliases"] = [str(item) for item in _as_list(metric.get("aliases")) if str(item).strip()]
        if "required_datasets" not in metric:
            errors.append(f"Metric '{metric_key}' is missing required_datasets; using empty list.")
        metric["required_datasets"] = [
            str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip()
        ]

    return document, errors


def _add_alias(index: Dict[str, Dict[str, str]], bucket: str, alias: Any, key: str, errors: list[str]) -> None:
    normalized = _normalize_alias(alias)
    if not normalized:
        return
    existing = index[bucket].get(normalized)
    if existing and existing != key:
        errors.append(f"Alias collision in {bucket}: '{alias}' maps to '{existing}' and '{key}'.")
        return
    index[bucket][normalized] = key


def _build_domain_index(domain: Dict[str, Any], errors: list[str]) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {
        "term_alias_to_key": {},
        "product_alias_to_key": {},
        "process_alias_to_group": {},
        "metric_alias_to_key": {},
        "dataset_keyword_to_key": {},
    }

    for key, product in domain.get("products", {}).items():
        _add_alias(index, "product_alias_to_key", key, key, errors)
        if isinstance(product, dict):
            _add_alias(index, "product_alias_to_key", product.get("display_name"), key, errors)
            for alias in _as_list(product.get("aliases")):
                _add_alias(index, "product_alias_to_key", alias, key, errors)

    for key, group in domain.get("process_groups", {}).items():
        _add_alias(index, "process_alias_to_group", key, key, errors)
        if isinstance(group, dict):
            _add_alias(index, "process_alias_to_group", group.get("display_name"), key, errors)
            for alias in _as_list(group.get("aliases")):
                _add_alias(index, "process_alias_to_group", alias, key, errors)
            for process in _as_list(group.get("processes")):
                _add_alias(index, "process_alias_to_group", process, key, errors)

    for key, term in domain.get("terms", {}).items():
        _add_alias(index, "term_alias_to_key", key, key, errors)
        if isinstance(term, dict):
            _add_alias(index, "term_alias_to_key", term.get("display_name"), key, errors)
            for alias in _as_list(term.get("aliases")):
                _add_alias(index, "term_alias_to_key", alias, key, errors)

    for key, metric in domain.get("metrics", {}).items():
        _add_alias(index, "metric_alias_to_key", key, key, errors)
        if isinstance(metric, dict):
            _add_alias(index, "metric_alias_to_key", metric.get("display_name"), key, errors)
            for alias in _as_list(metric.get("aliases")):
                _add_alias(index, "metric_alias_to_key", alias, key, errors)

    for key, dataset in domain.get("datasets", {}).items():
        _add_alias(index, "dataset_keyword_to_key", key, key, errors)
        if isinstance(dataset, dict):
            _add_alias(index, "dataset_keyword_to_key", dataset.get("display_name"), key, errors)
            for keyword in _as_list(dataset.get("keywords")):
                _add_alias(index, "dataset_keyword_to_key", keyword, key, errors)

    return index


def load_domain_json(domain_json_text: Any) -> Dict[str, Any]:
    parsed, errors = _parse_domain_json(domain_json_text)
    document, normalize_errors = _normalize_domain_document(parsed) if parsed else (
        {
            "domain_id": "manufacturing_default",
            "status": "active",
            "metadata": {},
            "domain": {
                "products": {},
                "process_groups": {},
                "terms": {},
                "datasets": {},
                "metrics": {},
                "join_rules": [],
            },
        },
        [],
    )
    errors.extend(normalize_errors)
    domain = document["domain"]
    domain_index = _build_domain_index(domain, errors)
    return {
        "domain_document": document,
        "domain": domain,
        "domain_index": domain_index,
        "domain_errors": errors,
    }


class DomainJsonLoader(Component):
    display_name = "Domain JSON Loader"
    description = "Parse and normalize the domain JSON document used by the data answer flow."
    icon = "Braces"
    name = "DomainJsonLoader"

    inputs = [
        DataInput(
            name="domain_json_payload",
            display_name="Domain JSON Payload",
            info="Optional output from Domain JSON Input.",
            input_types=["Data", "JSON"],
        ),
        MultilineInput(
            name="domain_json_text",
            display_name="Domain JSON Text",
            info="Paste the domain JSON document or bare domain object.",
            value="",
        ),
    ]

    outputs = [
        Output(
            name="domain_payload",
            display_name="Domain Payload",
            method="build_domain_payload",
            group_outputs=True,
            types=["Data"],
        ),
        Output(
            name="domain_index",
            display_name="Domain Index",
            method="build_domain_index",
            group_outputs=True,
            types=["Data"],
        ),
    ]

    def build_domain_payload(self) -> Data:
        source = getattr(self, "domain_json_payload", None) or getattr(self, "domain_json_text", "")
        payload = load_domain_json(source)
        return _make_data(payload, text=json.dumps(payload, ensure_ascii=False))

    def build_domain(self) -> Data:
        source = getattr(self, "domain_json_payload", None) or getattr(self, "domain_json_text", "")
        payload = load_domain_json(source)
        return _make_data({"domain": payload["domain"]}, text=json.dumps(payload["domain"], ensure_ascii=False))

    def build_domain_index(self) -> Data:
        source = getattr(self, "domain_json_payload", None) or getattr(self, "domain_json_text", "")
        payload = load_domain_json(source)
        return _make_data(
            {"domain_index": payload["domain_index"], "domain_errors": payload["domain_errors"]},
            text=json.dumps(payload["domain_index"], ensure_ascii=False),
        )

    def build_domain_document(self) -> Data:
        source = getattr(self, "domain_json_payload", None) or getattr(self, "domain_json_text", "")
        payload = load_domain_json(source)
        return _make_data(
            {"domain_document": payload["domain_document"]},
            text=json.dumps(payload["domain_document"], ensure_ascii=False),
        )
