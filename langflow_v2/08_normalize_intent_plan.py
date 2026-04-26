from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


def _normalize_triple_quoted_json(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return json.dumps(match.group(2))

    return re.sub(r'("""|\'\'\')(.*?)(\1)', replace, str(text or ""), flags=re.DOTALL)


def _strip_code_fence(text: str) -> str:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json|JSON)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _parse_jsonish(value: Any) -> tuple[Any, list[str]]:
    if value is None:
        return {}, []
    if isinstance(value, (dict, list)):
        return deepcopy(value), []
    text = _strip_code_fence(str(value or ""))
    if not text:
        return {}, []
    errors: list[str] = []
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text), []
        except Exception as exc:
            errors.append(str(exc))
    normalized = _normalize_triple_quoted_json(text)
    if normalized != text:
        for parser in (json.loads, ast.literal_eval):
            try:
                return parser(normalized), []
            except Exception as exc:
                errors.append(str(exc))
    return {}, errors


def _extract_json_object(text: str) -> Dict[str, Any]:
    parsed, errors = _parse_jsonish(text)
    if isinstance(parsed, dict) and parsed:
        return parsed
    match = re.search(r"\{.*\}", str(text or ""), flags=re.DOTALL)
    if match:
        parsed, errors = _parse_jsonish(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    return {"_parse_errors": errors}


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return deepcopy(data)
    text = getattr(value, "text", None) or getattr(value, "content", None)
    if isinstance(text, str):
        parsed, _errors = _parse_jsonish(text)
        return parsed if isinstance(parsed, dict) else {"text": text}
    return {}


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


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _normalize_metric_text(value: Any) -> str:
    return _normalize_text(value).replace("률", "율")


def _runtime_today(reference_date: str = "") -> datetime:
    if reference_date:
        for fmt in ("%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(reference_date, fmt)
            except Exception:
                pass
    try:
        zoneinfo = import_module("zoneinfo")
        return datetime.now(zoneinfo.ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
    except Exception:
        return datetime.now()


def _extract_date(question: str, reference_date: str = "") -> str | None:
    base = _runtime_today(reference_date)
    lowered = str(question or "").lower()
    if any(token in lowered for token in ("today", "금일", "오늘")):
        return base.strftime("%Y%m%d")
    if any(token in lowered for token in ("yesterday", "어제", "전일")):
        return (base - timedelta(days=1)).strftime("%Y%m%d")
    if any(token in lowered for token in ("tomorrow", "내일")):
        return (base + timedelta(days=1)).strftime("%Y%m%d")
    match = re.search(r"\b(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?([0-2]\d|3[01])\b", str(question or ""))
    if match:
        return f"{match.group(1)}{match.group(2)}{match.group(3)}"
    return None


def _dataset_configs(table_catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    return {str(key): value for key, value in datasets.items() if isinstance(value, dict)}


def _active_dataset_configs(table_catalog: Dict[str, Any], dataset_keys: list[str] | None = None) -> Dict[str, Dict[str, Any]]:
    configs = _dataset_configs(table_catalog)
    active_keys = [str(key) for key in _as_list(dataset_keys) if str(key) in configs]
    if not active_keys:
        active_keys = list(configs.keys())
    return {key: configs[key] for key in active_keys}


def _main_flow_filter_defs(main_flow_filters: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    filters = main_flow_filters.get("filters") if isinstance(main_flow_filters.get("filters"), dict) else {}
    return {str(key): value for key, value in filters.items() if isinstance(value, dict)}


def _main_flow_required_param_defs(main_flow_filters: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    params = main_flow_filters.get("required_params") if isinstance(main_flow_filters.get("required_params"), dict) else {}
    return {str(key): value for key, value in params.items() if isinstance(value, dict)}


def _dataset_column_items(dataset: Dict[str, Any]) -> list[Dict[str, Any]]:
    columns: list[Dict[str, Any]] = []
    for item in _as_list(dataset.get("columns")):
        if isinstance(item, dict):
            text = str(item.get("name") or item.get("column") or "").strip()
            if text:
                columns.append({**deepcopy(item), "name": text})
        else:
            text = str(item or "").strip()
            if text:
                columns.append({"name": text})
    return columns


def _dataset_columns(dataset: Dict[str, Any]) -> list[str]:
    return _unique_strings([item.get("name") for item in _dataset_column_items(dataset)])


def _columns_from_config(value: Any) -> list[str]:
    columns: list[str] = []
    raw = value
    if isinstance(raw, dict):
        raw = raw.get("columns") or raw.get("column") or raw.get("names") or raw.get("name")
    for item in _as_list(raw):
        if isinstance(item, dict):
            text = str(item.get("name") or item.get("column") or "").strip()
        else:
            text = str(item or "").strip()
        if text and text not in columns:
            columns.append(text)
    return columns


def _definition_columns(definition: Dict[str, Any]) -> list[str]:
    columns: list[str] = []
    for key in ("group_by_columns", "group_columns", "column_candidates", "columns"):
        columns.extend(_columns_from_config(definition.get(key)))
    return _unique_strings(columns)


def _dataset_filter_columns(dataset: Dict[str, Any], filter_key: str) -> list[str]:
    mappings = dataset.get("filter_mappings") if isinstance(dataset.get("filter_mappings"), dict) else {}
    raw_columns = mappings.get(filter_key)
    columns = _columns_from_config(raw_columns)
    if columns:
        return columns
    dataset_columns = _dataset_columns(dataset)
    return [column for column in dataset_columns if _normalize_text(column) == _normalize_text(filter_key)]


def _dataset_required_param_columns(dataset: Dict[str, Any], param_key: str) -> list[str]:
    for mapping_key in ("required_param_mappings", "param_mappings"):
        mappings = dataset.get(mapping_key) if isinstance(dataset.get(mapping_key), dict) else {}
        columns = _columns_from_config(mappings.get(param_key))
        if columns:
            return columns
    dataset_columns = _dataset_columns(dataset)
    return [column for column in dataset_columns if _normalize_text(column) == _normalize_text(param_key)]


def _current_columns(state: Dict[str, Any]) -> list[str]:
    current = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    rows = current.get("data") if isinstance(current.get("data"), list) else []
    if rows and isinstance(rows[0], dict):
        return [str(column) for column in rows[0].keys()]
    data_ref = current.get("data_ref") if isinstance(current.get("data_ref"), dict) else {}
    return [str(column) for column in _as_list(data_ref.get("columns"))]


def _contains_any(question: str, tokens: list[str]) -> bool:
    lowered = str(question or "").lower()
    return any(str(token).lower() in lowered for token in tokens)


def _planner_terms(main_flow_filters: Dict[str, Any] | None, key: str) -> list[str]:
    config = main_flow_filters or {}
    if isinstance(config.get("main_flow_filters"), dict):
        config = config["main_flow_filters"]
    terms = config.get("planner_terms") if isinstance(config.get("planner_terms"), dict) else {}
    raw = terms.get(key)
    if isinstance(raw, dict):
        raw = raw.get("tokens") or raw.get("aliases") or raw.get("keywords") or raw.get("values")
    return _unique_strings([str(item) for item in _as_list(raw) if str(item or "").strip()])


def _contains_planner_term(question: str, main_flow_filters: Dict[str, Any] | None, key: str) -> bool:
    return _matches_alias(question, _planner_terms(main_flow_filters, key))


def _alias_candidates(key: str, item: Dict[str, Any]) -> list[Any]:
    return [
        key,
        item.get("display_name", ""),
        item.get("name", ""),
        item.get("description", ""),
        *_as_list(item.get("aliases")),
        *_as_list(item.get("keywords")),
        *_as_list(item.get("question_examples")),
    ]


def _matches_alias(question: str, aliases: list[Any]) -> bool:
    normalized_question = _normalize_text(question)
    for alias in aliases:
        text = str(alias or "").strip()
        normalized_alias = _normalize_text(text)
        if not normalized_alias:
            continue
        if re.fullmatch(r"[A-Za-z0-9_]+", text):
            if re.search(rf"(?i)(?<![A-Za-z0-9_]){re.escape(text)}(?![A-Za-z0-9_])", str(question or "")):
                return True
            continue
        if normalized_alias in normalized_question:
            return True
    return False


def _merge_filter_values(target: Dict[str, Any], field: str, values: Any) -> None:
    clean_values = _unique_strings([str(item) for item in _as_list(values) if str(item).strip()])
    if not field or not clean_values:
        return
    target[field] = _unique_strings([*_as_list(target.get(field)), *clean_values])


def _domain_dataset_config(domain: Dict[str, Any], dataset_key: str) -> Dict[str, Any]:
    datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    dataset = datasets.get(dataset_key)
    return dataset if isinstance(dataset, dict) else {}


def _domain_filter_matches(question: str, domain: Dict[str, Any] | None = None) -> Dict[str, Any]:
    domain = domain or {}
    filters: Dict[str, Any] = {}

    process_groups = domain.get("process_groups") if isinstance(domain.get("process_groups"), dict) else {}
    for group_key, group in process_groups.items():
        if not isinstance(group, dict):
            continue
        processes = [str(item) for item in _as_list(group.get("processes")) if str(item).strip()]
        if _matches_alias(question, _alias_candidates(str(group_key), group)):
            group_filters = group.get("filters") if isinstance(group.get("filters"), dict) else {}
            if group_filters:
                for field, values in group_filters.items():
                    _merge_filter_values(filters, str(field), values)
            elif processes:
                _merge_filter_values(filters, "process_name", processes)
        for process in processes:
            if _normalize_text(process) and _normalize_text(process) in _normalize_text(question):
                _merge_filter_values(filters, "process_name", [process])

    for section_name in ("products", "terms"):
        section = domain.get(section_name) if isinstance(domain.get(section_name), dict) else {}
        for item_key, item in section.items():
            if not isinstance(item, dict):
                continue
            if not _matches_alias(question, _alias_candidates(str(item_key), item)):
                continue
            item_filters = item.get("filters") if isinstance(item.get("filters"), dict) else item.get("filter_values")
            if isinstance(item_filters, dict):
                for field, values in item_filters.items():
                    _merge_filter_values(filters, str(field), values)

    return filters


def _dataset_hints(question: str, table_catalog: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
    normalized_question = _normalize_text(question)
    found: list[str] = []
    for dataset_key, dataset in _dataset_configs(table_catalog).items():
        domain_dataset = _domain_dataset_config(domain, dataset_key)
        candidates = [
            dataset_key,
            dataset.get("display_name", ""),
            dataset.get("description", ""),
            *_as_list(dataset.get("keywords")),
            *_as_list(dataset.get("aliases")),
            *_as_list(dataset.get("question_examples")),
            *_alias_candidates(str(dataset_key), domain_dataset),
        ]
        if any(_normalize_text(item) and _normalize_text(item) in normalized_question for item in candidates):
            found.append(dataset_key)

    for _metric_key, metric in _matched_metrics(question, domain).items():
        if isinstance(metric, dict):
            found.extend(str(item) for item in _as_list(metric.get("required_datasets")))

    return _unique_strings(found)


def _matched_metrics(question: str, domain: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    metrics = domain.get("metrics") if isinstance(domain.get("metrics"), dict) else {}
    normalized_question = _normalize_metric_text(question)
    matched: Dict[str, Dict[str, Any]] = {}
    for metric_key, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        aliases = [
            metric_key,
            metric.get("display_name", ""),
            metric.get("output_column", ""),
            *_as_list(metric.get("aliases")),
        ]
        if any(_normalize_metric_text(item) and _normalize_metric_text(item) in normalized_question for item in aliases):
            matched[str(metric_key)] = deepcopy(metric)
    return matched


def _filters_from_question(question: str, domain: Dict[str, Any] | None = None, main_flow_filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
    filters: Dict[str, Any] = _domain_filter_matches(question, domain)
    filter_defs = _main_flow_filter_defs(main_flow_filters or {})
    normalized_question = _normalize_text(question)
    for filter_key, definition in filter_defs.items():
        if filter_key in filters:
            continue
        value_aliases = definition.get("value_aliases") if isinstance(definition.get("value_aliases"), dict) else {}
        matched_values: list[Any] = []
        for alias, values in value_aliases.items():
            if _normalize_text(alias) and _normalize_text(alias) in normalized_question:
                matched_values.extend(_as_list(values))
        known_values = definition.get("known_values") or definition.get("values")
        for value in _as_list(known_values):
            if _normalize_text(value) and _normalize_text(value) in normalized_question:
                matched_values.append(value)
        if matched_values:
            filters[filter_key] = _unique_strings(matched_values)
    return filters


def _column_filters_from_question(question: str, table_catalog: Dict[str, Any], current_columns: list[str]) -> Dict[str, Any]:
    columns = set(current_columns)
    for dataset in _dataset_configs(table_catalog).values():
        columns.update(_dataset_columns(dataset))
    filters: Dict[str, Any] = {}
    for column in sorted(columns, key=len, reverse=True):
        if not column:
            continue
        pattern = rf"(?i)(?:\b{re.escape(column)}\b)\s*(?:=|:|이|가|은|는)\s*([A-Za-z0-9_./-]+)"
        match = re.search(pattern, question)
        if match:
            value = match.group(1).strip()
            if value and _normalize_text(value) != _normalize_text(column):
                filters[column] = [value]
    return filters


def _merge_conditions(previous: Dict[str, Any], current: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
    merged = deepcopy(previous) if isinstance(previous, dict) else {}
    inherited = [str(key) for key in merged.keys()]
    for key, value in current.items():
        if value in (None, "", []):
            continue
        merged[key] = deepcopy(value)
        if key in inherited:
            inherited.remove(key)
    return merged, inherited


def _required_param_changed(previous: Dict[str, Any], explicit_params: Dict[str, Any]) -> bool:
    for key, value in explicit_params.items():
        if value in (None, "", []):
            continue
        if previous.get(key) not in (None, "", []) and str(previous.get(key)) != str(value):
            return True
    return False


def _values_within_scope(requested: Any, source: Any) -> bool:
    source_values = {_normalize_text(item) for item in _as_list(source) if str(item).strip()}
    if not source_values:
        return True
    requested_values = {_normalize_text(item) for item in _as_list(requested) if str(item).strip()}
    return bool(requested_values) and requested_values.issubset(source_values)


def _filters_within_current_scope(state: Dict[str, Any], filters: Dict[str, Any], column_filters: Dict[str, Any]) -> bool:
    current = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    source_filters = current.get("source_filters") if isinstance(current.get("source_filters"), dict) else current.get("filters", {})
    source_column_filters = current.get("source_column_filters") if isinstance(current.get("source_column_filters"), dict) else {}
    for key, value in filters.items():
        if not _values_within_scope(value, source_filters.get(key)):
            return False
    for key, value in column_filters.items():
        if not _values_within_scope(value, source_column_filters.get(key)):
            return False
    return True


def _filter_plan(filters: Dict[str, Any], column_filters: Dict[str, Any], needed_datasets: list[str], table_catalog: Dict[str, Any], main_flow_filters: Dict[str, Any], current_columns: list[str]) -> list[Dict[str, Any]]:
    configs = _dataset_configs(table_catalog)
    active_datasets = needed_datasets or list(configs.keys())
    plan: list[Dict[str, Any]] = []
    filter_defs = _main_flow_filter_defs(main_flow_filters)
    for filter_key, values in filters.items():
        for dataset_key in active_datasets:
            dataset = configs.get(dataset_key, {})
            columns = _dataset_filter_columns(dataset, filter_key)
            if columns:
                definition = filter_defs.get(filter_key, {})
                plan.append({"kind": "semantic", "field": filter_key, "dataset_key": dataset_key, "columns": columns, "operator": definition.get("operator", "in"), "value_type": definition.get("value_type", "string"), "value_shape": definition.get("value_shape", "list"), "values": _as_list(values), "definition": definition})
    all_columns = set(current_columns)
    for dataset in configs.values():
        all_columns.update(_dataset_columns(dataset))
    for column, values in column_filters.items():
        if str(column) not in all_columns:
            continue
        matched_datasets = [key for key in active_datasets if str(column) in _dataset_columns(configs.get(key, {}))]
        if not matched_datasets and str(column) in current_columns:
            matched_datasets = ["current_data"]
        for dataset_key in matched_datasets:
            plan.append({"kind": "column", "field": str(column), "dataset_key": dataset_key, "columns": [str(column)], "operator": "in", "value_type": "string", "value_shape": "list", "values": _as_list(values)})
    return plan


def _label_candidates(key: str, item: Dict[str, Any]) -> list[Any]:
    return [
        key,
        item.get("display_name", ""),
        item.get("name", ""),
        *_as_list(item.get("aliases")),
        *_as_list(item.get("keywords")),
    ]


def _has_rank_or_sort_intent(question: str, main_flow_filters: Dict[str, Any] | None = None) -> bool:
    terms = [
        *_planner_terms(main_flow_filters, "rank_desc"),
        *_planner_terms(main_flow_filters, "rank_asc"),
        *_planner_terms(main_flow_filters, "sort"),
    ]
    return _contains_any(question, terms)


def _matches_grouping_alias(question: str, aliases: list[Any], main_flow_filters: Dict[str, Any] | None = None, allow_bare: bool = False) -> bool:
    normalized_question = _normalize_text(question)
    raw_question = str(question or "")
    suffixes = _planner_terms(main_flow_filters, "grouping_suffixes")
    prefixes = _planner_terms(main_flow_filters, "grouping_prefixes")
    postfixes = _planner_terms(main_flow_filters, "grouping_postfixes")
    for alias in aliases:
        text = str(alias or "").strip()
        normalized_alias = _normalize_text(text)
        if not normalized_alias:
            continue
        if suffixes and any(f"{normalized_alias}{_normalize_text(suffix)}" in normalized_question for suffix in suffixes):
            return True
        if re.fullmatch(r"[A-Za-z0-9_./ -]+", text):
            escaped = re.escape(text).replace(r"\ ", r"\s+")
            prefix_pattern = "|".join(re.escape(prefix).replace(r"\ ", r"\s+") for prefix in prefixes)
            postfix_pattern = "|".join(re.escape(postfix).replace(r"\ ", r"\s+") for postfix in postfixes)
            if prefix_pattern and re.search(rf"(?i)\b(?:{prefix_pattern})\s+{escaped}\b", raw_question):
                return True
            if postfix_pattern and re.search(rf"(?i)\b{escaped}\s*(?:{postfix_pattern})\b", raw_question):
                return True
        if allow_bare and _matches_alias(question, [text]):
            return True
    return False


def _candidate_column_items(table_catalog: Dict[str, Any], current_columns: list[str] | None = None, needed_datasets: list[str] | None = None) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    for dataset_key, dataset in _active_dataset_configs(table_catalog, needed_datasets).items():
        for item in _dataset_column_items(dataset):
            items.append({**item, "dataset_key": dataset_key})
    for column in _as_list(current_columns):
        text = str(column or "").strip()
        if text:
            items.append({"name": text, "dataset_key": "current_data"})
    deduped: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        name = str(item.get("name") or "").strip()
        if name and name not in seen:
            seen.add(name)
            deduped.append(item)
    return deduped


def _column_alias_candidates(column_item: Dict[str, Any]) -> list[Any]:
    return [
        column_item.get("name", ""),
        column_item.get("display_name", ""),
        column_item.get("label", ""),
        *_as_list(column_item.get("aliases")),
        *_as_list(column_item.get("keywords")),
    ]


def _columns_matching_aliases(columns: list[Dict[str, Any]], aliases: list[Any]) -> list[str]:
    normalized_aliases = {_normalize_text(alias) for alias in aliases if _normalize_text(alias)}
    result: list[str] = []
    for item in columns:
        name = str(item.get("name") or "").strip()
        column_aliases = {_normalize_text(alias) for alias in _column_alias_candidates(item) if _normalize_text(alias)}
        if name and normalized_aliases.intersection(column_aliases):
            result.append(name)
    return _unique_strings(result)


def _existing_or_configured_columns(columns: list[str], table_catalog: Dict[str, Any], current_columns: list[str] | None = None, needed_datasets: list[str] | None = None) -> list[str]:
    available = {str(item.get("name") or "").strip() for item in _candidate_column_items(table_catalog, current_columns, needed_datasets)}
    available.discard("")
    if not available:
        return _unique_strings(columns)
    existing = [column for column in columns if column in available]
    return _unique_strings(existing or columns)


def _semantic_group_columns(filter_key: str, definition: Dict[str, Any], table_catalog: Dict[str, Any], current_columns: list[str] | None = None, needed_datasets: list[str] | None = None, source: str = "filter") -> list[str]:
    columns: list[str] = []
    for dataset in _active_dataset_configs(table_catalog, needed_datasets).values():
        mapped = _dataset_required_param_columns(dataset, filter_key) if source == "required_param" else _dataset_filter_columns(dataset, filter_key)
        if mapped:
            columns.append(mapped[0])
    columns.extend(_existing_or_configured_columns(_definition_columns(definition), table_catalog, current_columns, needed_datasets))
    if not columns:
        columns.extend(_columns_matching_aliases(_candidate_column_items(table_catalog, current_columns, needed_datasets), _label_candidates(filter_key, definition)))
    return _unique_strings(columns)


def _domain_term_group_columns(term_key: str, term: Dict[str, Any], table_catalog: Dict[str, Any], main_flow_filters: Dict[str, Any], current_columns: list[str] | None = None, needed_datasets: list[str] | None = None) -> list[str]:
    columns = _existing_or_configured_columns(_definition_columns(term), table_catalog, current_columns, needed_datasets)
    semantic_key = str(term.get("semantic_key") or term.get("filter_key") or "").strip()
    if semantic_key:
        definition = _main_flow_filter_defs(main_flow_filters).get(semantic_key, {})
        columns.extend(_semantic_group_columns(semantic_key, definition, table_catalog, current_columns, needed_datasets))
    if not columns:
        columns.extend(_columns_matching_aliases(_candidate_column_items(table_catalog, current_columns, needed_datasets), _label_candidates(term_key, term)))
    return _unique_strings(columns)


def _normalize_group_by_values(values: Any, table_catalog: Dict[str, Any], main_flow_filters: Dict[str, Any], domain: Dict[str, Any], current_columns: list[str] | None = None, needed_datasets: list[str] | None = None) -> list[str]:
    columns: list[str] = []
    available_columns = {str(item.get("name")) for item in _candidate_column_items(table_catalog, current_columns, needed_datasets)}
    filter_defs = _main_flow_filter_defs(main_flow_filters)
    required_defs = _main_flow_required_param_defs(main_flow_filters)
    terms = domain.get("terms") if isinstance(domain.get("terms"), dict) else {}
    for value in _as_list(values):
        text = str(value or "").strip()
        if not text:
            continue
        if text in available_columns:
            columns.append(text)
        elif text in filter_defs:
            columns.extend(_semantic_group_columns(text, filter_defs[text], table_catalog, current_columns, needed_datasets))
        elif text in required_defs:
            columns.extend(_semantic_group_columns(text, required_defs[text], table_catalog, current_columns, needed_datasets, "required_param"))
        elif text in terms and isinstance(terms[text], dict):
            columns.extend(_domain_term_group_columns(text, terms[text], table_catalog, main_flow_filters, current_columns, needed_datasets))
        else:
            columns.append(text)
    return _unique_strings(columns)


def _group_by_from_question(question: str, table_catalog: Dict[str, Any] | None = None, main_flow_filters: Dict[str, Any] | None = None, domain: Dict[str, Any] | None = None, current_columns: list[str] | None = None, needed_datasets: list[str] | None = None) -> list[str]:
    table_catalog = table_catalog or {}
    main_flow_filters = main_flow_filters or {}
    domain = domain or {}
    allow_bare = _has_rank_or_sort_intent(question, main_flow_filters)
    group_columns: list[str] = []

    for filter_key, definition in _main_flow_filter_defs(main_flow_filters).items():
        if _matches_grouping_alias(question, _label_candidates(filter_key, definition), main_flow_filters, allow_bare):
            group_columns.extend(_semantic_group_columns(filter_key, definition, table_catalog, current_columns, needed_datasets))

    for param_key, definition in _main_flow_required_param_defs(main_flow_filters).items():
        if _matches_grouping_alias(question, _label_candidates(param_key, definition), main_flow_filters, allow_bare):
            group_columns.extend(_semantic_group_columns(param_key, definition, table_catalog, current_columns, needed_datasets, "required_param"))

    terms = domain.get("terms") if isinstance(domain.get("terms"), dict) else {}
    for term_key, term in terms.items():
        if not isinstance(term, dict):
            continue
        if _matches_grouping_alias(question, _label_candidates(str(term_key), term), main_flow_filters, allow_bare):
            group_columns.extend(_domain_term_group_columns(str(term_key), term, table_catalog, main_flow_filters, current_columns, needed_datasets))

    for column_item in _candidate_column_items(table_catalog, current_columns, needed_datasets):
        if _matches_grouping_alias(question, _column_alias_candidates(column_item), main_flow_filters, allow_bare):
            group_columns.append(str(column_item.get("name") or "").strip())

    return _unique_strings(group_columns)


def _sort_column_candidates(table_catalog: Dict[str, Any], domain: Dict[str, Any], needed_datasets: list[str] | None = None, current_columns: list[str] | None = None) -> list[tuple[str, list[Any]]]:
    candidates: list[tuple[str, list[Any]]] = []
    for dataset_key, dataset in _active_dataset_configs(table_catalog, needed_datasets).items():
        domain_dataset = _domain_dataset_config(domain, dataset_key)
        primary_columns = [
            domain_dataset.get("primary_quantity_column"),
            dataset.get("primary_quantity_column"),
            domain_dataset.get("output_column"),
            dataset.get("output_column"),
        ]
        if str(dataset_key) in _dataset_columns(dataset):
            primary_columns.append(dataset_key)
        for column in _unique_strings([str(item) for item in primary_columns if str(item or "").strip()]):
            candidates.append((column, [column, *_label_candidates(dataset_key, dataset), *_label_candidates(dataset_key, domain_dataset)]))
        for item in _dataset_column_items(dataset):
            column = str(item.get("name") or "").strip()
            column_type = str(item.get("type") or item.get("value_type") or "").lower()
            if column and column_type in {"number", "numeric", "int", "integer", "float", "double", "decimal"}:
                candidates.append((column, _column_alias_candidates(item)))
    for column in _as_list(current_columns):
        text = str(column or "").strip()
        if text:
            candidates.append((text, [text]))

    result: list[tuple[str, list[Any]]] = []
    seen: set[str] = set()
    for column, aliases in candidates:
        if column and column not in seen:
            seen.add(column)
            result.append((column, aliases))
    return result


def _sort_from_question(question: str, metric_definitions: Dict[str, Dict[str, Any]] | None = None, columns: list[str] | None = None, table_catalog: Dict[str, Any] | None = None, domain: Dict[str, Any] | None = None, needed_datasets: list[str] | None = None, main_flow_filters: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    if not _has_rank_or_sort_intent(question, main_flow_filters):
        return None

    metric = ""
    for metric_key, definition in (metric_definitions or {}).items():
        if isinstance(definition, dict):
            metric = str(definition.get("output_column") or metric_key).strip()
            if metric:
                break
    if not metric:
        for candidate, aliases in _sort_column_candidates(table_catalog or {}, domain or {}, needed_datasets, columns):
            if _matches_alias(question, aliases):
                metric = candidate
                break
    if not metric:
        candidates = _sort_column_candidates(table_catalog or {}, domain or {}, needed_datasets, columns)
        if candidates:
            metric = candidates[0][0]
    if not metric:
        return None

    if _contains_planner_term(question, main_flow_filters, "rank_desc"):
        return {"column": metric, "ascending": False}
    if _contains_planner_term(question, main_flow_filters, "rank_asc"):
        return {"column": metric, "ascending": True}
    return None


def _top_n_from_question(question: str, main_flow_filters: Dict[str, Any] | None = None) -> int | None:
    lowered = str(question or "").lower()
    for token in _planner_terms(main_flow_filters, "top_n"):
        match = re.search(rf"{re.escape(str(token).lower())}\s*(\d+)", lowered)
        if match:
            try:
                return max(1, int(match.group(1)))
            except Exception:
                return 1
    if _has_rank_or_sort_intent(question, main_flow_filters):
        return 1
    return None


def _required_params(question: str, state: Dict[str, Any], reference_date: str = "") -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    date = _extract_date(question, reference_date)
    if date:
        params["date"] = date
    else:
        context = state.get("context") if isinstance(state.get("context"), dict) else {}
        last_params = context.get("last_extracted_params") if isinstance(context.get("last_extracted_params"), dict) else {}
        if last_params.get("date"):
            params["date"] = last_params["date"]

    lot_match = re.search(r"\bLOT[-_A-Z0-9]+\b", str(question or ""), flags=re.IGNORECASE)
    if lot_match:
        params["lot_id"] = lot_match.group(0)
    return params


def _explicit_required_params(question: str, reference_date: str = "") -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    date = _extract_date(question, reference_date)
    if date:
        params["date"] = date
    lot_match = re.search(r"\bLOT[-_A-Z0-9]+\b", str(question or ""), flags=re.IGNORECASE)
    if lot_match:
        params["lot_id"] = lot_match.group(0)
    return params


def _has_current_data(state: Dict[str, Any]) -> bool:
    current = state.get("current_data")
    if not isinstance(current, dict):
        return False
    if isinstance(current.get("data"), list) and bool(current.get("data")):
        return True
    data_ref = current.get("data_ref")
    return isinstance(data_ref, dict) and bool(data_ref.get("ref_id") or data_ref.get("id"))


def _build_job(dataset_key: str, dataset: Dict[str, Any], params: Dict[str, Any], filters: Dict[str, Any], column_filters: Dict[str, Any], filter_plan: list[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "dataset_key": dataset_key,
        "dataset_label": dataset.get("display_name", dataset_key),
        "tool_name": dataset.get("tool_name", f"get_{dataset_key}_data"),
        "db_key": dataset.get("db_key", "PKG_RPT"),
        "source_type": dataset.get("source_type", "auto"),
        "required_params": [str(item) for item in _as_list(dataset.get("required_params"))],
        "params": deepcopy(params),
        "filters": deepcopy(filters),
        "column_filters": deepcopy(column_filters),
        "filter_plan": [deepcopy(item) for item in filter_plan if item.get("dataset_key") in (dataset_key, "current_data")],
    }


def _normalize_param_values(params: Dict[str, Any]) -> Dict[str, Any]:
    normalized = deepcopy(params)
    if normalized.get("date"):
        digits = "".join(ch for ch in str(normalized["date"]) if ch.isdigit())
        normalized["date"] = digits[:8] or normalized["date"]
    return normalized


def _drop_empty_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in params.items() if value not in (None, "", [])}


def _normalize_plan(raw_plan: Dict[str, Any], question: str, state: Dict[str, Any], table_catalog: Dict[str, Any], domain: Dict[str, Any], main_flow_filters: Dict[str, Any], reference_date: str = "") -> Dict[str, Any]:
    configs = _dataset_configs(table_catalog)
    matched_metrics = _matched_metrics(question, domain)
    needed_datasets = _unique_strings([*_as_list(raw_plan.get("needed_datasets")), *_as_list(raw_plan.get("dataset_keys")), *_as_list(raw_plan.get("datasets"))])
    if str(raw_plan.get("query_mode") or "").strip() != "followup_transform":
        for metric in matched_metrics.values():
            needed_datasets.extend(str(item) for item in _as_list(metric.get("required_datasets")))
    if not needed_datasets:
        needed_datasets = _dataset_hints(question, table_catalog, domain)
    needed_datasets = [key for key in _unique_strings(needed_datasets) if key in configs]
    current_columns = _current_columns(state)

    raw_filters = raw_plan.get("filters") if isinstance(raw_plan.get("filters"), dict) else {}
    explicit_filters = {**_filters_from_question(question, domain, main_flow_filters), **raw_filters}
    raw_column_filters = raw_plan.get("column_filters") if isinstance(raw_plan.get("column_filters"), dict) else {}
    explicit_column_filters = {**_column_filters_from_question(question, table_catalog, current_columns), **raw_column_filters}

    raw_params: Dict[str, Any] = {}
    if isinstance(raw_plan.get("required_params"), dict):
        raw_params.update(raw_plan["required_params"])
    if isinstance(raw_plan.get("params"), dict):
        raw_params.update(raw_plan["params"])
    context = state.get("context") if isinstance(state.get("context"), dict) else {}
    previous_params = context.get("last_required_params") if isinstance(context.get("last_required_params"), dict) else context.get("last_extracted_params", {})
    previous_filters = context.get("last_filters") if isinstance(context.get("last_filters"), dict) else {}
    previous_column_filters = context.get("last_column_filters") if isinstance(context.get("last_column_filters"), dict) else {}
    explicit_params = _normalize_param_values({**_drop_empty_params(raw_params), **_explicit_required_params(question, reference_date)})
    params, inherited_params = _merge_conditions(previous_params if isinstance(previous_params, dict) else {}, explicit_params)
    params = _normalize_param_values({**params, **_required_params(question, state, reference_date)})
    filters, inherited_filters = _merge_conditions(previous_filters, explicit_filters)
    column_filters, inherited_column_filters = _merge_conditions(previous_column_filters, explicit_column_filters)
    required_changed = _required_param_changed(previous_params if isinstance(previous_params, dict) else {}, explicit_params)

    explicit_fresh = _contains_planner_term(question, main_flow_filters, "fresh_retrieval")
    followup_like = _contains_planner_term(question, main_flow_filters, "followup_reference")
    query_mode = str(raw_plan.get("query_mode") or "").strip()
    query_mode_source = "llm" if query_mode in {"retrieval", "followup_transform", "finish", "clarification"} else "fallback"
    if query_mode not in {"retrieval", "followup_transform", "finish", "clarification"}:
        query_mode = "followup_transform" if _has_current_data(state) and followup_like and not explicit_fresh else "retrieval"
    if query_mode == "followup_transform" and explicit_fresh:
        query_mode = "retrieval"
        query_mode_source = "guard:fresh_retrieval"
    if query_mode == "followup_transform" and not _has_current_data(state):
        query_mode = "retrieval"
        query_mode_source = "guard:no_current_data"
    if query_mode == "followup_transform" and (required_changed or not _filters_within_current_scope(state, filters, column_filters)):
        query_mode = "retrieval"
        query_mode_source = "guard:scope_changed"
    if query_mode == "retrieval" and not needed_datasets and _has_current_data(state):
        current = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
        needed_datasets = [key for key in _as_list(current.get("source_dataset_keys")) if str(key) in configs]

    raw_group_by = _normalize_group_by_values(raw_plan.get("group_by"), table_catalog, main_flow_filters, domain, current_columns, needed_datasets)
    question_group_by = _group_by_from_question(question, table_catalog, main_flow_filters, domain, current_columns, needed_datasets)
    group_by = _unique_strings([*raw_group_by, *question_group_by])
    sort = raw_plan.get("sort") or _sort_from_question(question, matched_metrics, current_columns, table_catalog, domain, needed_datasets, main_flow_filters)
    top_n = raw_plan.get("top_n") or _top_n_from_question(question, main_flow_filters)
    raw_needs_pandas_present = "needs_pandas" in raw_plan or "needs_post_processing" in raw_plan
    needs_pandas = bool(raw_plan.get("needs_pandas") or raw_plan.get("needs_post_processing") or group_by or sort or top_n)
    if (not raw_needs_pandas_present and _contains_planner_term(question, main_flow_filters, "post_processing")) or query_mode == "followup_transform" or len(needed_datasets) > 1 or bool(matched_metrics):
        needs_pandas = True

    jobs = []
    missing: list[Dict[str, str]] = []
    resolved_filter_plan = _filter_plan(filters, column_filters, needed_datasets, table_catalog, main_flow_filters, current_columns)
    if query_mode == "retrieval":
        for dataset_key in needed_datasets:
            job = _build_job(dataset_key, configs.get(dataset_key, {}), params, filters, column_filters, resolved_filter_plan)
            for required in job["required_params"]:
                if params.get(required) in (None, "", []):
                    missing.append({"dataset_key": dataset_key, "param": required})
            jobs.append(job)

    if query_mode == "retrieval" and not needed_datasets:
        return {
            "request_type": "clarification",
            "query_mode": "finish",
            "route": "finish",
            "needed_datasets": [],
            "retrieval_jobs": [],
            "required_params": params,
            "filters": filters,
            "column_filters": column_filters,
            "filter_plan": resolved_filter_plan,
            "group_by": group_by,
            "needs_pandas": False,
            "analysis_goal": raw_plan.get("analysis_goal") or question,
            "response": "질문에 맞는 조회 데이터셋을 찾지 못했습니다. 생산, 목표, WIP처럼 조회할 데이터를 조금 더 구체적으로 적어주세요.",
            "failure_type": "unknown_dataset",
        }
    if missing:
        labels = ", ".join(f"{item['dataset_key']}.{item['param']}" for item in missing)
        return {
            "request_type": "clarification",
            "query_mode": "finish",
            "route": "finish",
            "needed_datasets": needed_datasets,
            "retrieval_jobs": jobs,
            "required_params": params,
            "filters": filters,
            "column_filters": column_filters,
            "filter_plan": resolved_filter_plan,
            "group_by": group_by,
            "needs_pandas": False,
            "analysis_goal": raw_plan.get("analysis_goal") or question,
            "response": f"데이터 조회에 필요한 필수 조건이 부족합니다: {labels}",
            "failure_type": "missing_required_params",
            "missing_required_params": missing,
        }

    route = "followup_transform" if query_mode == "followup_transform" else ("multi_retrieval" if len(jobs) > 1 else "single_retrieval")
    return {
        "request_type": str(raw_plan.get("request_type") or "data_question"),
        "query_mode": query_mode,
        "route": route,
        "needed_datasets": needed_datasets,
        "retrieval_jobs": jobs,
        "required_params": params,
        "filters": filters,
        "column_filters": column_filters,
        "filter_plan": resolved_filter_plan,
        "inherited_required_params": inherited_params,
        "inherited_filters": inherited_filters,
        "inherited_column_filters": inherited_column_filters,
        "required_param_changed": required_changed,
        "query_mode_source": query_mode_source,
        "group_by": group_by,
        "sort": sort,
        "top_n": top_n,
        "needs_pandas": needs_pandas,
        "metric_keys": list(matched_metrics.keys()),
        "metric_definitions": matched_metrics,
        "analysis_goal": str(raw_plan.get("analysis_goal") or question),
        "reason": str(raw_plan.get("reason") or ""),
    }


def normalize_intent_plan(llm_result_value: Any, reference_date_value: Any = "") -> Dict[str, Any]:
    payload = _payload_from_value(llm_result_value)
    llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
    prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
    state = prompt_payload.get("state") if isinstance(prompt_payload.get("state"), dict) else {}
    domain = prompt_payload.get("domain") if isinstance(prompt_payload.get("domain"), dict) else {}
    table_catalog = prompt_payload.get("table_catalog") if isinstance(prompt_payload.get("table_catalog"), dict) else {}
    main_flow_filters = prompt_payload.get("main_flow_filters") if isinstance(prompt_payload.get("main_flow_filters"), dict) else {}
    question = str(prompt_payload.get("user_question") or state.get("pending_user_question") or "").strip()
    reference_date = str(reference_date_value or prompt_payload.get("reference_date") or "").strip()

    warnings = [str(item) for item in _as_list(llm_result.get("errors")) if str(item).strip()]
    llm_text = str(llm_result.get("llm_text") or "").strip()
    raw_plan = _extract_json_object(llm_text)
    if not llm_text or not raw_plan or "_parse_errors" in raw_plan:
        if isinstance(raw_plan, dict) and raw_plan.get("_parse_errors"):
            warnings.extend(str(item) for item in _as_list(raw_plan.get("_parse_errors")) if str(item).strip())
        fallback_datasets = _dataset_hints(question, table_catalog, domain)
        current_columns = _current_columns(state)
        raw_plan = {
            "needed_datasets": fallback_datasets,
            "required_params": _required_params(question, state, reference_date),
            "filters": _filters_from_question(question, domain, main_flow_filters),
            "column_filters": _column_filters_from_question(question, table_catalog, current_columns),
            "group_by": _group_by_from_question(question, table_catalog, main_flow_filters, domain, current_columns, fallback_datasets),
            "analysis_goal": question,
        }
        source = "heuristic_fallback"
    else:
        source = "llm"

    plan = _normalize_plan(raw_plan, question, state, table_catalog, domain, main_flow_filters, reference_date)
    plan["planner_source"] = source
    if warnings:
        plan["planner_warnings"] = _unique_strings(warnings)
    return {
        "intent_plan": plan,
        "retrieval_jobs": plan.get("retrieval_jobs", []),
        "state": state,
        "domain": domain,
        "table_catalog": table_catalog,
        "main_flow_filters": main_flow_filters,
        "user_question": question,
    }


class NormalizeIntentPlan(Component):
    display_name = "Normalize Intent Plan"
    description = "Parse and normalize the LLM intent JSON into retrieval jobs and routing fields."
    icon = "ListChecks"
    name = "NormalizeIntentPlan"

    inputs = [
        DataInput(name="llm_result", display_name="LLM Result", info="Output from LLM JSON Caller.", input_types=["Data", "JSON"]),
        MessageTextInput(name="reference_date", display_name="Reference Date Override", value="", advanced=True),
    ]
    outputs = [Output(name="intent_plan", display_name="Intent Plan", method="build_plan", types=["Data"])]

    def build_plan(self):
        payload = normalize_intent_plan(getattr(self, "llm_result", None), getattr(self, "reference_date", ""))
        plan = payload.get("intent_plan", {})
        self.status = {
            "route": plan.get("route"),
            "query_mode": plan.get("query_mode"),
            "datasets": plan.get("needed_datasets", []),
            "planner_source": plan.get("planner_source"),
        }
        return _make_data(payload)

