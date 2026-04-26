from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any, Dict

from .config import VALID_GBNS, VALID_JOIN_TYPES


def empty_domain() -> Dict[str, Any]:
    return {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def split_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        text = str(value or "").replace(",", "\n").replace(";", "\n")
        items = text.splitlines()
    result: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def norm_token(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def slug(value: Any, fallback: str = "domain_item") -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def parse_jsonish(value: Any) -> tuple[Any, list[str]]:
    if isinstance(value, (dict, list)):
        return deepcopy(value), []
    raw = str(value or "").strip()
    if not raw:
        return {}, []
    try:
        return json.loads(raw), []
    except Exception as exc:
        return {}, [str(exc)]


def normalized_aliases(gbn: str, key: str, payload: Dict[str, Any]) -> list[str]:
    candidates = [key, payload.get("display_name", ""), *as_list(payload.get("aliases"))]
    if gbn == "process_groups":
        candidates.extend(as_list(payload.get("processes")))
    return list(dict.fromkeys(token for token in (norm_token(item) for item in candidates) if token))


def normalized_keywords(gbn: str, payload: Dict[str, Any]) -> list[str]:
    if gbn not in {"datasets", "metrics"}:
        return []
    return list(dict.fromkeys(token for token in (norm_token(item) for item in as_list(payload.get("keywords"))) if token))


def normalize_payload(gbn: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(payload) if isinstance(payload, dict) else {}
    if gbn == "products":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": split_lines(payload.get("aliases")),
            "filters": payload.get("filters") if isinstance(payload.get("filters"), dict) else {},
        }
    if gbn == "process_groups":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": split_lines(payload.get("aliases")),
            "processes": split_lines(payload.get("processes")),
        }
    if gbn == "terms":
        filter_value = payload.get("filter") if isinstance(payload.get("filter"), dict) else {}
        column_candidates = split_lines(payload.get("column_candidates"))
        result = {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": split_lines(payload.get("aliases")),
            "meaning": str(payload.get("meaning") or payload.get("description") or "").strip(),
            "filter": filter_value,
        }
        if column_candidates:
            result["column_candidates"] = column_candidates
        return result
    if gbn == "datasets":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": split_lines(payload.get("aliases")),
            "keywords": split_lines(payload.get("keywords")),
            "primary_quantity_column": str(payload.get("primary_quantity_column") or "").strip(),
            "default_group_by": split_lines(payload.get("default_group_by")),
            "required_params": split_lines(payload.get("required_params")),
            "tool_name": str(payload.get("tool_name") or "").strip(),
        }
    if gbn == "metrics":
        source_columns = payload.get("source_columns")
        if isinstance(source_columns, str):
            source_columns = split_lines(source_columns)
        grouping_hint = split_lines(payload.get("grouping_hint") or payload.get("default_group_by"))
        result = {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": split_lines(payload.get("aliases")),
            "required_datasets": split_lines(payload.get("required_datasets")),
            "formula": str(payload.get("formula") or "").strip(),
            "output_column": str(payload.get("output_column") or "").strip(),
            "source_columns": source_columns if isinstance(source_columns, list) else [],
            "grouping_hint": grouping_hint,
        }
        pandas_hint = str(payload.get("pandas_hint") or "").strip()
        if pandas_hint:
            result["pandas_hint"] = pandas_hint
        return result
    if gbn == "join_rules":
        keys = split_lines(payload.get("keys") or payload.get("join_keys"))
        join_type = str(payload.get("join_type") or "inner").strip().lower()
        if join_type not in VALID_JOIN_TYPES:
            join_type = "inner"
        return {
            "left_dataset": str(payload.get("left_dataset") or payload.get("base_dataset") or "").strip(),
            "right_dataset": str(payload.get("right_dataset") or payload.get("join_dataset") or "").strip(),
            "keys": keys,
            "join_type": join_type,
            "description": str(payload.get("description") or "").strip(),
        }
    return payload


def make_item(gbn: str, key: str, payload: Dict[str, Any], status: str = "active", source_text: str = "") -> Dict[str, Any]:
    gbn = str(gbn or "").strip()
    if gbn not in VALID_GBNS:
        raise ValueError(f"Unsupported domain type: {gbn}")
    normalized_payload = normalize_payload(gbn, payload)
    key = slug(key or normalized_payload.get("display_name") or gbn, gbn)
    return {
        "gbn": gbn,
        "key": key,
        "status": status or "active",
        "payload": normalized_payload,
        "normalized_aliases": normalized_aliases(gbn, key, normalized_payload),
        "normalized_keywords": normalized_keywords(gbn, normalized_payload),
        "source_text": source_text,
        "source": "langflow_v2_registration_web",
    }


def merge_item(domain: Dict[str, Any], item: Dict[str, Any]) -> None:
    if isinstance(item.get("domain"), dict):
        for key, value in item["domain"].items():
            if key == "join_rules" and isinstance(value, list):
                domain.setdefault("join_rules", []).extend(deepcopy(value))
            elif isinstance(value, dict):
                domain.setdefault(key, {}).update(deepcopy(value))
        return

    gbn = str(item.get("gbn") or item.get("category") or "").strip()
    key = str(item.get("key") or item.get("name") or "").strip()
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    if not gbn:
        return
    if gbn == "join_rules":
        rule = normalize_payload("join_rules", payload)
        if key:
            rule.setdefault("name", key)
        domain.setdefault("join_rules", []).append(rule)
        return
    if gbn not in domain or not isinstance(domain.get(gbn), dict):
        domain[gbn] = {}
    if key:
        domain[gbn][key] = normalize_payload(gbn, payload)


def normalize_domain_input(raw_value: Any) -> Dict[str, Any]:
    parsed, errors = parse_jsonish(raw_value)
    candidates: list[Dict[str, Any]] = []
    if isinstance(parsed, dict) and isinstance(parsed.get("domain"), dict):
        for gbn in ("products", "process_groups", "terms", "datasets", "metrics"):
            values = parsed["domain"].get(gbn)
            if isinstance(values, dict):
                for key, payload in values.items():
                    candidates.append({"gbn": gbn, "key": key, "payload": payload})
        for rule in as_list(parsed["domain"].get("join_rules")):
            if isinstance(rule, dict):
                key = rule.get("name") or f"{rule.get('left_dataset') or rule.get('base_dataset')}_{rule.get('right_dataset') or rule.get('join_dataset')}_join"
                candidates.append({"gbn": "join_rules", "key": key, "payload": rule})
    elif isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
        candidates = [item for item in parsed["items"] if isinstance(item, dict)]
    elif isinstance(parsed, list):
        candidates = [item for item in parsed if isinstance(item, dict)]
    elif isinstance(parsed, dict) and any(key in parsed for key in ("gbn", "category", "payload")):
        candidates = [parsed]
    elif isinstance(parsed, dict) and any(key in parsed for key in VALID_GBNS):
        for gbn in VALID_GBNS:
            values = parsed.get(gbn)
            if isinstance(values, dict):
                for key, payload in values.items():
                    candidates.append({"gbn": gbn, "key": key, "payload": payload})
            elif gbn == "join_rules" and isinstance(values, list):
                for rule in values:
                    if isinstance(rule, dict):
                        candidates.append({"gbn": gbn, "key": rule.get("name", ""), "payload": rule})

    items: list[Dict[str, Any]] = []
    for candidate in candidates:
        try:
            items.append(
                make_item(
                    str(candidate.get("gbn") or candidate.get("category") or ""),
                    str(candidate.get("key") or candidate.get("name") or ""),
                    candidate.get("payload") if isinstance(candidate.get("payload"), dict) else {},
                    str(candidate.get("status") or "active"),
                    str(candidate.get("source_text") or ""),
                )
            )
        except Exception as exc:
            errors.append(str(exc))
    return {"items": items, "errors": errors}


def aggregate_domain(items: list[Dict[str, Any]]) -> Dict[str, Any]:
    domain = empty_domain()
    for item in items:
        if str(item.get("status") or "active") == "deleted":
            continue
        merge_item(domain, item)
    return domain


def validate_items(items: list[Dict[str, Any]], existing_items: list[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    existing_items = existing_items or []
    issues: list[Dict[str, Any]] = []
    identities: set[str] = set()
    existing_identities = {f"{item.get('gbn')}:{item.get('key')}" for item in existing_items}
    dataset_keys = {str(item.get("key")) for item in [*existing_items, *items] if item.get("gbn") == "datasets"}

    for item in items:
        gbn = str(item.get("gbn") or "")
        key = str(item.get("key") or "")
        identity = f"{gbn}:{key}"
        if gbn not in VALID_GBNS:
            issues.append({"severity": "error", "message": f"{identity} has invalid gbn."})
        if not key:
            issues.append({"severity": "error", "message": f"{identity} has no key."})
        if identity in identities:
            issues.append({"severity": "error", "message": f"{identity} appears more than once."})
        if identity in existing_identities:
            issues.append({"severity": "warning", "message": f"{identity} already exists and will be updated."})
        identities.add(identity)
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        if gbn == "metrics":
            required = split_lines(payload.get("required_datasets"))
            missing = [dataset for dataset in required if dataset not in dataset_keys]
            if missing:
                issues.append({"severity": "warning", "message": f"{identity} references datasets not registered in domain items: {missing}."})
            if not payload.get("formula") and not payload.get("pandas_hint"):
                issues.append({"severity": "warning", "message": f"{identity} has no formula or pandas_hint."})
            if not payload.get("output_column"):
                issues.append({"severity": "warning", "message": f"{identity} has no output_column."})
        if gbn == "join_rules":
            if not payload.get("keys"):
                issues.append({"severity": "warning", "message": f"{identity} has no join keys."})
    return {"can_save": bool(items) and not any(issue["severity"] == "error" for issue in issues), "issues": issues}
