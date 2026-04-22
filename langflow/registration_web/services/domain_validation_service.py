from __future__ import annotations

from typing import Any, Dict

from .config import VALID_GBNS


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _existing_map(existing_items: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in existing_items:
        gbn = str(item.get("gbn") or "")
        key = str(item.get("key") or "")
        if gbn and key:
            result[f"{gbn}:{key}"] = item
    return result


def _dataset_keys(existing_items: list[Dict[str, Any]], batch_items: list[Dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for item in [*existing_items, *batch_items]:
        if item.get("gbn") == "datasets" and item.get("key"):
            keys.add(str(item["key"]))
    return keys


def validate_domain_items(
    normalized_items: list[Dict[str, Any]],
    existing_items: list[Dict[str, Any]],
) -> Dict[str, Any]:
    issues: list[Dict[str, Any]] = []
    item_results: list[Dict[str, Any]] = []
    existing_by_key = _existing_map(existing_items)
    valid_dataset_keys = _dataset_keys(existing_items, normalized_items)

    alias_owners: Dict[str, str] = {}
    keyword_owners: Dict[str, str] = {}
    for identity, existing in existing_by_key.items():
        for alias in _as_list(existing.get("normalized_aliases")):
            alias_owners[str(alias)] = identity
        for keyword in _as_list(existing.get("normalized_keywords")):
            keyword_owners[str(keyword)] = identity

    seen_keys: set[str] = set()
    for item in normalized_items:
        gbn = str(item.get("gbn") or "")
        key = str(item.get("key") or "")
        identity = f"{gbn}:{key}"
        item_issues: list[Dict[str, Any]] = []
        recommended_status = "active"

        if gbn not in VALID_GBNS:
            item_issues.append({"severity": "error", "type": "invalid_gbn", "message": f"{identity} has invalid gbn."})
        if not key:
            item_issues.append({"severity": "error", "type": "missing_key", "message": f"{identity} has no key."})
        if identity in seen_keys:
            item_issues.append({"severity": "error", "type": "duplicate_in_batch", "message": f"{identity} appears more than once."})
        seen_keys.add(identity)
        if identity in existing_by_key:
            item_issues.append({"severity": "warning", "type": "update_existing", "message": f"{identity} already exists and will be updated."})

        for alias in _as_list(item.get("normalized_aliases")):
            owner = alias_owners.get(str(alias))
            if owner and owner != identity:
                item_issues.append({"severity": "error", "type": "alias_collision", "message": f"Alias '{alias}' already belongs to {owner}."})
        for keyword in _as_list(item.get("normalized_keywords")):
            owner = keyword_owners.get(str(keyword))
            if owner and owner != identity:
                item_issues.append({"severity": "error", "type": "keyword_collision", "message": f"Keyword '{keyword}' already belongs to {owner}."})

        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        if gbn == "metrics":
            missing = [dataset for dataset in _as_list(payload.get("required_datasets")) if str(dataset) not in valid_dataset_keys]
            if missing:
                item_issues.append(
                    {
                        "severity": "warning",
                        "type": "unknown_required_dataset",
                        "message": f"{identity} references datasets not currently registered: {missing}.",
                    }
                )
            if not payload.get("formula") and not payload.get("pandas_hint"):
                item_issues.append(
                    {
                        "severity": "warning",
                        "type": "missing_formula",
                        "message": f"{identity} has no formula or pandas_hint.",
                    }
                )
        if gbn == "join_rules":
            for field in ("base_dataset", "join_dataset"):
                dataset = str(payload.get(field) or "")
                if dataset and dataset not in valid_dataset_keys:
                    item_issues.append(
                        {
                            "severity": "warning",
                            "type": "unknown_join_dataset",
                            "message": f"{identity} references unknown {field}: {dataset}.",
                        }
                    )
            if not payload.get("join_keys"):
                item_issues.append({"severity": "warning", "type": "missing_join_keys", "message": f"{identity} has no join_keys."})

        if any(issue["severity"] == "error" for issue in item_issues):
            recommended_status = "review_required"
            item["status"] = "review_required"

        issues.extend(item_issues)
        item_results.append({"gbn": gbn, "key": key, "recommended_status": recommended_status, "issues": item_issues})

    return {
        "can_save": not any(issue["severity"] == "error" for issue in issues) and bool(normalized_items),
        "has_blocking_conflict": any(issue["severity"] == "error" for issue in issues),
        "issues": issues,
        "item_results": item_results,
        "normalized_domain_items": normalized_items,
    }
