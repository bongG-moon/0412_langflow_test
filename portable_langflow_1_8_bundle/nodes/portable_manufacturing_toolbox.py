"""Portable Langflow node: domain-aware manufacturing toolbox for Agent/tool-calling flows."""

from __future__ import annotations

import hashlib
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DataInput, MessageInput, MultilineInput, Output, StrInput
from lfx.schema.data import Data
from lfx.schema.message import Message


DEFAULT_REGISTRY = {
    "process_groups": {
        "DP": {"group_name": "DP", "synonyms": ["DP", "D/P"], "actual_values": ["WET1", "WET2", "L/T1", "L/T2", "B/G1", "B/G2", "H/S1", "H/S2", "W/S1", "W/S2"]},
        "DA": {"group_name": "D/A", "synonyms": ["D/A", "DA", "Die Attach", "\ub2e4\uc774\uc5b4\ud0dc\uce58", "\ub2e4\uc774\ubcf8\ub529"], "actual_values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"]},
        "FCB": {"group_name": "FCB", "synonyms": ["FCB", "Flip Chip", "\ud50c\ub9bd\uce69"], "actual_values": ["FCB1", "FCB2", "FCB/H"]},
        "PC": {"group_name": "P/C", "synonyms": ["P/C", "PC"], "actual_values": ["P/C1", "P/C2", "P/C3", "P/C4", "P/C5"]},
        "WB": {"group_name": "W/B", "synonyms": ["W/B", "WB", "Wire Bonding", "\uc640\uc774\uc5b4\ubcf8\ub529"], "actual_values": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"]},
        "QCSPC": {"group_name": "QCSPC", "synonyms": ["QCSPC"], "actual_values": ["QCSPC1", "QCSPC2", "QCSPC3", "QCSPC4"]},
        "SAT": {"group_name": "SAT", "synonyms": ["SAT"], "actual_values": ["SAT1", "SAT2"]},
        "PL": {"group_name": "P/L", "synonyms": ["P/L", "PL"], "actual_values": ["PLH"]},
    },
    "attribute_groups": {
        "mode": {
            "DDR4": {"synonyms": ["DDR4", "\ub514\ub514\uc54c4", "DDR 4"], "actual_values": ["DDR4"]},
            "DDR5": {"synonyms": ["DDR5", "\ub514\ub514\uc54c5", "DDR 5"], "actual_values": ["DDR5"]},
            "LPDDR5": {"synonyms": ["LPDDR5", "LP DDR5", "\uc5d8\ud53c\ub514\ub514\uc54c5", "LP5"], "actual_values": ["LPDDR5"]},
        },
        "den": {
            "256G": {"synonyms": ["256G", "256\uae30\uac00", "256Gb"], "actual_values": ["256G"]},
            "512G": {"synonyms": ["512G", "512\uae30\uac00", "512Gb"], "actual_values": ["512G"]},
            "1T": {"synonyms": ["1T", "1\ud14c\ub77c", "1Tb", "1TB"], "actual_values": ["1T"]},
        },
        "tech": {
            "LC": {"synonyms": ["LC", "\uc5d8\uc528", "\uc5d8\uc2dc"], "actual_values": ["LC"]},
            "FO": {"synonyms": ["FO", "\ud32c\uc544\uc6c3", "fan-out"], "actual_values": ["FO"]},
            "FC": {"synonyms": ["FC", "\ud50c\ub9bd\uce69"], "actual_values": ["FC"]},
        },
        "pkg_type1": {
            "FCBGA": {"synonyms": ["FCBGA"], "actual_values": ["FCBGA"]},
            "LFBGA": {"synonyms": ["LFBGA"], "actual_values": ["LFBGA"]},
        },
        "pkg_type2": {
            "ODP": {"synonyms": ["ODP"], "actual_values": ["ODP"]},
            "16DP": {"synonyms": ["16DP"], "actual_values": ["16DP"]},
            "SDP": {"synonyms": ["SDP"], "actual_values": ["SDP"]},
        },
    },
    "value_groups": [
        {"field": "process_name", "canonical": "\ud6c4\uacf5\uc815A", "synonyms": ["\ud6c4\uacf5\uc815A"], "values": ["D/A1", "D/A2"]},
    ],
    "dataset_keyword_map": {
        "production": ["\uc0dd\uc0b0", "production", "\uc0dd\uc0b0\ub7c9", "\uc2e4\uc801"],
        "target": ["\ubaa9\ud45c", "target", "\ubaa9\ud45c\ub7c9", "\uacc4\ud68d"],
        "defect": ["\ubd88\ub7c9", "defect", "\uacb0\ud568"],
        "equipment": ["\uc124\ube44", "equipment", "\uac00\ub3d9\ub960"],
        "wip": ["wip", "\uc7ac\uacf5", "\ub300\uae30"],
        "yield": ["\uc218\uc728", "yield", "\uc591\ud488\ub960"],
        "hold": ["hold", "\ud640\ub4dc"],
        "scrap": ["scrap", "\uc2a4\ud06c\ub7a9", "\ud3d0\uae30"],
        "recipe": ["recipe", "\ub808\uc2dc\ud53c", "\uacf5\uc815 \uc870\uac74"],
        "lot_trace": ["lot", "trace", "\ub85c\ud2b8", "\ucd94\uc801"],
    },
    "analysis_rules": [
        {"name": "achievement_rate", "display_name": "achievement rate", "synonyms": ["achievement rate", "\ub2ec\uc131\ub960", "\uc0dd\uc0b0 \ub2ec\uc131\ub960"], "required_datasets": ["production", "target"], "calculation_mode": "ratio", "output_column": "achievement_rate", "source_columns": [{"dataset_key": "production", "column": "production"}, {"dataset_key": "target", "column": "target"}], "default_group_by": ["process_name"]},
        {"name": "yield_rate", "display_name": "yield rate", "synonyms": ["yield", "yield rate", "\uc218\uc728", "\uc591\ud488\ub960"], "required_datasets": ["yield"], "calculation_mode": "preferred_metric", "output_column": "yield_rate", "source_columns": [{"dataset_key": "yield", "column": "yield_rate"}], "default_group_by": ["process_name"]},
        {"name": "production_saturation_rate", "display_name": "production saturation rate", "synonyms": ["production saturation", "production saturation rate", "\ud3ec\ud654\uc728", "\uc0dd\uc0b0 \ud3ec\ud654\uc728"], "required_datasets": ["production", "wip"], "calculation_mode": "ratio", "output_column": "production_saturation_rate", "source_columns": [{"dataset_key": "production", "column": "production"}, {"dataset_key": "wip", "column": "wip_qty"}], "default_group_by": ["process_name"]},
        {"name": "hold_anomaly_check", "display_name": "HOLD \uc774\uc0c1\uc5ec\ubd80", "synonyms": ["hold_anomaly_check", "HOLD \uc774\uc0c1\uc5ec\ubd80", "\ud640\ub4dc \uccb4\ud06c"], "required_datasets": ["wip"], "calculation_mode": "condition_flag", "output_column": "hold_anomaly_flag", "source_columns": [{"dataset_key": "wip", "column": "\uc0c1\ud0dc"}], "default_group_by": []},
        {"name": "plan_gap_rate", "display_name": "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728", "synonyms": ["plan_gap_rate", "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728", "\ubaa9\ud45c \ucc28\uc774\uc728", "\uacc4\ud68d \ucc28\uc774\uc728"], "required_datasets": ["production", "target"], "calculation_mode": "custom_ratio_gap", "output_column": "plan_gap_rate", "source_columns": [{"dataset_key": "production", "column": "production"}, {"dataset_key": "target", "column": "target"}], "default_group_by": ["process_name"]},
        {"name": "hold_load_index", "display_name": "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218", "synonyms": ["hold_load_index", "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218", "\ubd80\ud558\uc9c0\uc218"], "required_datasets": ["hold", "production"], "calculation_mode": "ratio", "output_column": "hold_load_index", "source_columns": [{"dataset_key": "hold", "column": "hold_qty"}, {"dataset_key": "production", "column": "production"}], "default_group_by": ["process_name"]},
    ],
    "join_rules": [
        {"name": "production_target_join", "base_dataset": "production", "join_dataset": "target", "join_keys": ["WORK_DT", "OPER_NAME"]},
        {"name": "production_hold_join", "base_dataset": "production", "join_dataset": "hold", "join_keys": ["WORK_DT", "OPER_NAME"]},
    ],
    "tool_manifest": {
        "production": "get_production_data",
        "target": "get_target_data",
        "defect": "get_defect_rate",
        "equipment": "get_equipment_status",
        "wip": "get_wip_status",
        "yield": "get_yield_data",
        "hold": "get_hold_data",
        "scrap": "get_scrap_data",
        "recipe": "get_recipe_data",
        "lot_trace": "get_lot_trace_data",
    },
}

FOLLOWUP_KEYWORDS = ["\uadf8 \uacb0\uacfc", "\uadf8\uac70", "\uc774\uc804 \uacb0\uacfc", "\uc815\ub9ac", "\uc0c1\uc704", "\ud3c9\uade0", "\ud569\uacc4", "\ube44\uad50", "\uacf5\uc815\ubcc4", "\ub77c\uc778\ubcc4", "\uc81c\ud488\ubcc4", "top", "average", "sum", "group", "compare"]


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


def _normalize_chat_history(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if isinstance(item, dict) and item.get("role") and item.get("content"):
            normalized.append({"role": str(item["role"]), "content": str(item["content"])})
    return normalized


def _safe_session_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", str(raw or "").strip())
    return cleaned or "default"


def _storage_dir(subdir: str) -> Path:
    candidate = Path.cwd() / (subdir.strip() or ".portable_langflow_sessions")
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except Exception:
        fallback = Path.home() / (subdir.strip() or ".portable_langflow_sessions")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _message_session_id(value: Any) -> str:
    if value is None:
        return ""
    session_id = getattr(value, "session_id", None)
    if session_id is not None:
        return str(session_id or "")
    if isinstance(value, dict):
        return str(value.get("session_id") or "")
    return ""


def _normalize(text: Any) -> str:
    return re.sub(r"[^a-z0-9\uac00-\ud7a3]+", "", str(text or "").lower())


def _contains_alias(text: str, alias: str) -> bool:
    alias_norm = _normalize(alias)
    return bool(alias_norm) and alias_norm in _normalize(text)


def _unique(values: list[str]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return ordered


def _merge_registry(raw_value: Any) -> dict[str, Any]:
    registry = json.loads(json.dumps(DEFAULT_REGISTRY))
    payload = _as_payload(raw_value)
    if not payload:
        return registry
    candidate = payload.get("custom_registry") if isinstance(payload.get("custom_registry"), dict) else payload
    if isinstance(payload.get("process_groups"), dict):
        registry["process_groups"].update(payload["process_groups"])
    if isinstance(payload.get("attribute_groups"), dict):
        for field_name, groups in payload["attribute_groups"].items():
            registry["attribute_groups"].setdefault(field_name, {}).update(groups or {})
    if isinstance(payload.get("dataset_keyword_map"), dict):
        for dataset_key, keywords in payload["dataset_keyword_map"].items():
            registry["dataset_keyword_map"][dataset_key] = _unique([*(registry["dataset_keyword_map"].get(dataset_key) or []), *(keywords or [])])
    if isinstance(candidate.get("value_groups"), list):
        registry["value_groups"].extend(item for item in candidate["value_groups"] if isinstance(item, dict))
    if isinstance(candidate.get("analysis_rules"), list):
        registry["analysis_rules"].extend(item for item in candidate["analysis_rules"] if isinstance(item, dict))
    if isinstance(candidate.get("join_rules"), list):
        registry["join_rules"].extend(item for item in candidate["join_rules"] if isinstance(item, dict))
    if isinstance(payload.get("tool_manifest"), dict):
        registry["tool_manifest"].update(payload["tool_manifest"])
    return registry


def _load_snapshot(session_id: str, storage_subdir: str) -> dict[str, Any]:
    session_file = _storage_dir(storage_subdir) / f"{_safe_session_id(session_id)}.json"
    if not session_file.exists():
        return {"chat_history": [], "context": {}, "current_data": None, "path": str(session_file)}
    try:
        payload = json.loads(session_file.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    return {
        "chat_history": _normalize_chat_history(payload.get("chat_history")),
        "context": payload.get("context") if isinstance(payload.get("context"), dict) else {},
        "current_data": payload.get("current_data") if isinstance(payload.get("current_data"), dict) else None,
        "path": str(session_file),
    }


def _save_snapshot(session_id: str, storage_subdir: str, query: str, result_payload: dict[str, Any]) -> str:
    session_file = _storage_dir(storage_subdir) / f"{_safe_session_id(session_id)}.json"
    history = []
    if session_file.exists():
        try:
            existing = json.loads(session_file.read_text(encoding="utf-8"))
            history = _normalize_chat_history(existing.get("chat_history"))
        except Exception:
            history = []
    if query:
        history.append({"role": "user", "content": query})
    if result_payload.get("response"):
        history.append({"role": "assistant", "content": str(result_payload["response"])})
    snapshot = {
        "session_id": session_id,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "chat_history": history,
        "context": result_payload.get("extracted_params") if isinstance(result_payload.get("extracted_params"), dict) else {},
        "current_data": result_payload.get("current_data") if isinstance(result_payload.get("current_data"), dict) else None,
    }
    session_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(session_file)


def _detect_date(text: str) -> str:
    lowered = text.lower()
    now = datetime.now()
    if "\uc5b4\uc81c" in text or "yesterday" in lowered:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if "\uc624\ub298" in text or "today" in lowered:
        return now.strftime("%Y-%m-%d")
    compact = re.search(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?(0[1-9]|[12]\d|3[01])", text)
    if compact:
        return f"{compact.group(1)}-{compact.group(2)}-{compact.group(3)}"
    return ""


def _extract_date_slices(text: str, default_date: str) -> list[dict[str, str]]:
    lowered = text.lower()
    now = datetime.now()
    slices: list[dict[str, str]] = []
    if "\uc5b4\uc81c" in text or "yesterday" in lowered:
        slices.append({"label": "\uc5b4\uc81c", "date": (now - timedelta(days=1)).strftime("%Y-%m-%d")})
    if "\uc624\ub298" in text or "today" in lowered:
        slices.append({"label": "\uc624\ub298", "date": now.strftime("%Y-%m-%d")})
    for year, month, day in re.findall(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?(0[1-9]|[12]\d|3[01])", text):
        value = f"{year}-{month}-{day}"
        if value not in [item["date"] for item in slices]:
            slices.append({"label": value, "date": value})
    if not slices and default_date:
        slices.append({"label": default_date, "date": default_date})
    return slices


def _expand_group_values(text: str, field_name: str, groups: dict[str, dict[str, Any]], custom_groups: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for group in groups.values():
        aliases = [str(group.get("group_name") or ""), *(group.get("synonyms") or []), *(group.get("actual_values") or [])]
        if any(_contains_alias(text, alias) for alias in aliases):
            values.extend(str(item) for item in group.get("actual_values") or [])
    for group in custom_groups:
        if str(group.get("field") or "") != field_name:
            continue
        aliases = [str(group.get("canonical") or ""), *(group.get("synonyms") or [])]
        if any(_contains_alias(text, alias) for alias in aliases):
            values.extend(str(item) for item in group.get("values") or [])
    return _unique(values)


def _detect_direct_processes(text: str) -> list[str]:
    patterns = [r"D/A\d", r"W/B\d", r"FCB/H", r"FCB\d", r"P/C\d", r"QCSPC\d", r"SAT\d", r"WET\d", r"L/T\d", r"B/G\d", r"H/S\d", r"W/S\d", r"PLH"]
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            normalized = match.upper()
            if normalized not in found:
                found.append(normalized)
    return found


def _detect_line_names(text: str) -> list[str]:
    return _unique([match.upper() for match in re.findall(r"\bL\d+\b", text, flags=re.IGNORECASE)])


def _detect_group_by(text: str) -> str:
    lowered = text.lower()
    if "\uacf5\uc815\ubcc4" in text or "by process" in lowered:
        return "process_name"
    if "\ub77c\uc778\ubcc4" in text or "by line" in lowered:
        return "line_name"
    if "\uc81c\ud488\ubcc4" in text or "by product" in lowered:
        return "product_name"
    if "by mode" in lowered or "mode\ubcc4" in text:
        return "MODE"
    if "by tech" in lowered or "\uae30\uc220\ubcc4" in text:
        return "TECH"
    return ""


def _detect_top_n(text: str) -> int:
    match = re.search(r"(?:\uc0c1\uc704|top)\s*(\d+)", text.lower())
    return int(match.group(1)) if match else 0


def _match_rules(text: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    matched = []
    seen_names: set[str] = set()
    for rule in registry.get("analysis_rules", []):
        rule_name = str(rule.get("name") or "").strip()
        if any(_contains_alias(text, synonym) for synonym in rule.get("synonyms") or []):
            if rule_name and rule_name in seen_names:
                continue
            matched.append(rule)
            if rule_name:
                seen_names.add(rule_name)
    return matched


def _detect_dataset_keys(text: str, matched_rules: list[dict[str, Any]], registry: dict[str, Any]) -> list[str]:
    keys = []
    for dataset_key, keywords in registry.get("dataset_keyword_map", {}).items():
        if any(_contains_alias(text, keyword) for keyword in keywords or []):
            keys.append(dataset_key)
    for rule in matched_rules:
        for dataset_key in rule.get("required_datasets") or []:
            if dataset_key not in keys:
                keys.append(dataset_key)
    return _unique(keys) or ["production"]


def _is_followup(query: str, current_data: dict[str, Any] | None, params: dict[str, Any], registry: dict[str, Any]) -> bool:
    if not current_data or params.get("date"):
        return False
    if any(_contains_alias(query, keyword) for keywords in registry.get("dataset_keyword_map", {}).values() for keyword in keywords or []):
        return False
    lowered = query.lower()
    return any(keyword in query for keyword in FOLLOWUP_KEYWORDS if keyword not in {"top", "average", "sum", "group", "compare"}) or any(keyword in lowered for keyword in ["top", "average", "sum", "group", "compare"])


def _extract_params(query: str, registry: dict[str, Any]) -> dict[str, Any]:
    process_names = _expand_group_values(query, "process_name", registry.get("process_groups", {}), registry.get("value_groups", []))
    for process_name in _detect_direct_processes(query):
        if process_name not in process_names:
            process_names.append(process_name)
    return {
        "date": _detect_date(query),
        "process_names": process_names,
        "mode_values": _expand_group_values(query, "mode", registry.get("attribute_groups", {}).get("mode", {}), registry.get("value_groups", [])),
        "den_values": _expand_group_values(query, "den", registry.get("attribute_groups", {}).get("den", {}), registry.get("value_groups", [])),
        "tech_values": _expand_group_values(query, "tech", registry.get("attribute_groups", {}).get("tech", {}), registry.get("value_groups", [])),
        "pkg_type1_values": _expand_group_values(query, "pkg_type1", registry.get("attribute_groups", {}).get("pkg_type1", {}), registry.get("value_groups", [])),
        "pkg_type2_values": _expand_group_values(query, "pkg_type2", registry.get("attribute_groups", {}).get("pkg_type2", {}), registry.get("value_groups", [])),
        "line_names": _detect_line_names(query),
        "group_by": _detect_group_by(query),
        "top_n": _detect_top_n(query),
    }


def _family_from_process(process_name: str) -> str:
    normalized = str(process_name or "").upper()
    if normalized.startswith("D/A"):
        return "DA"
    if normalized.startswith("FCB"):
        return "FCB"
    if normalized.startswith("P/C"):
        return "PC"
    if normalized.startswith("W/B"):
        return "WB"
    if normalized.startswith("QCSPC"):
        return "QCSPC"
    if normalized.startswith("SAT"):
        return "SAT"
    if normalized.startswith("PL"):
        return "PL"
    return "DP"


def _group_name_from_process(process_name: str, registry: dict[str, Any]) -> str:
    for group in registry.get("process_groups", {}).values():
        if process_name in (group.get("actual_values") or []):
            return str(group.get("group_name") or "")
    return _family_from_process(process_name)


def _rng_for(*parts: str) -> random.Random:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return random.Random(int(digest, 16))


def _base_row(date_value: str, process_name: str, line_name: str, index_value: int, registry: dict[str, Any]) -> dict[str, Any]:
    mode = ["DDR4", "DDR5", "LPDDR5"][index_value % 3]
    den = ["256G", "512G", "1T"][index_value % 3]
    tech = ["LC", "FO", "FC"][index_value % 3]
    pkg_type1 = ["FCBGA", "LFBGA"][index_value % 2]
    pkg_type2 = ["ODP", "16DP", "SDP"][index_value % 3]
    family = _family_from_process(process_name)
    group_name = _group_name_from_process(process_name, registry)
    return {
        "date": date_value,
        "WORK_DT": date_value.replace("-", ""),
        "process_name": process_name,
        "OPER_NAME": process_name,
        "\uacf5\uc815\uad70": group_name,
        "OPER_NUM": f"{index_value + 1:03d}",
        "PKG_TYPE1": pkg_type1,
        "PKG_TYPE2": pkg_type2,
        "TSV_DIE_TYP": "TSV" if tech == "FC" else "STD",
        "MODE": mode,
        "DEN": den,
        "TECH": tech,
        "LEAD": "AUTO" if index_value % 2 == 0 else "MANUAL",
        "MCP_NO": f"MCP-{family}-{index_value + 1:03d}",
        "FAMILY": family,
        "FACTORY": "FAB1" if family in {"DP", "DA"} else "PKG1",
        "ORG": "Back-End Process" if family in {"DP", "DA"} else "Package Assembly",
        "\ub77c\uc778": line_name,
        "line_name": line_name,
        "product_name": f"{pkg_type1}-{mode}-{den}-{tech}",
    }


def _generate_rows(tool_name: str, dataset_key: str, params: dict[str, Any], registry: dict[str, Any], label: str | None) -> list[dict[str, Any]]:
    process_names = params.get("process_names") or ["D/A1", "D/A2", "D/A3", "W/B1", "FCB1", "SAT1"]
    line_names = params.get("line_names") or ["L1", "L2"]
    date_value = str(params.get("date") or datetime.now().strftime("%Y-%m-%d"))
    rng = _rng_for(tool_name, dataset_key, date_value, ",".join(process_names), str(label or ""))
    rows = []
    for index_value, process_name in enumerate(process_names):
        for line_index, line_name in enumerate(line_names):
            base = _base_row(date_value, process_name, line_name, index_value + line_index, registry)
            production = rng.randint(800, 1800)
            row = dict(base)
            if dataset_key == "production":
                row["production"] = production
                row["quantity"] = production
            elif dataset_key == "target":
                row["target"] = int(production * rng.uniform(1.02, 1.15))
            elif dataset_key == "defect":
                defect_qty = max(5, int(production * rng.uniform(0.01, 0.05)))
                row["defect_qty"] = defect_qty
                row["defect_rate"] = round((defect_qty / production) * 100, 2)
            elif dataset_key == "equipment":
                row["equipment_id"] = f"{process_name.replace('/', '')}-{line_name}"
                row["uptime_pct"] = round(rng.uniform(88.0, 99.5), 2)
                row["alarm_minutes"] = rng.randint(0, 60)
                row["status"] = "RUNNING" if row["uptime_pct"] >= 92 else "ALARM"
            elif dataset_key == "wip":
                row["wip_qty"] = int(production * rng.uniform(0.08, 0.22))
                row["\uc0c1\ud0dc"] = rng.choice(["QUEUED", "RUNNING", "HOLD", "REWORK"])
            elif dataset_key == "yield":
                row["tested_qty"] = production
                row["pass_qty"] = int(production * rng.uniform(0.92, 0.995))
                row["yield_rate"] = round((row["pass_qty"] / row["tested_qty"]) * 100, 2)
            elif dataset_key == "hold":
                row["hold_qty"] = rng.randint(0, 120)
                row["\uc0c1\ud0dc"] = rng.choice(["HOLD", "REWORK", "WAIT"])
            elif dataset_key == "scrap":
                row["scrap_qty"] = rng.randint(0, 40)
            elif dataset_key == "recipe":
                row["temp_c"] = rng.randint(25, 240)
                row["pressure_kpa"] = rng.randint(0, 130)
                row["process_time_sec"] = rng.randint(120, 600)
            elif dataset_key == "lot_trace":
                row["LOT_ID"] = f"LOT-{date_value.replace('-', '')}-{index_value + line_index + 1:03d}"
                row["\uc0c1\ud0dc"] = rng.choice(["WAIT", "RUNNING", "MOVE_OUT", "HOLD", "REWORK", "COMPLETE"])
            rows.append(row)
    return rows


def _filter_rows(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    filtered = []
    for row in rows:
        if params.get("process_names") and str(row.get("process_name")) not in params["process_names"]:
            continue
        if params.get("mode_values") and str(row.get("MODE")) not in params["mode_values"]:
            continue
        if params.get("den_values") and str(row.get("DEN")) not in params["den_values"]:
            continue
        if params.get("tech_values") and str(row.get("TECH")) not in params["tech_values"]:
            continue
        if params.get("pkg_type1_values") and str(row.get("PKG_TYPE1")) not in params["pkg_type1_values"]:
            continue
        if params.get("pkg_type2_values") and str(row.get("PKG_TYPE2")) not in params["pkg_type2_values"]:
            continue
        if params.get("line_names") and str(row.get("line_name")) not in params["line_names"]:
            continue
        filtered.append(row)
    return filtered


def _numeric_keys(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [key for key in rows[0] if all(isinstance(row.get(key), (int, float)) for row in rows if key in row)]


def _aggregate_rows(rows: list[dict[str, Any]], group_by: str, average_mode: bool = False) -> list[dict[str, Any]]:
    if not group_by:
        return rows
    numeric_keys = _numeric_keys(rows)
    bucket: dict[str, dict[str, Any]] = {}
    counts: dict[str, int] = {}
    for row in rows:
        group_value = str(row.get(group_by) or "unknown")
        counts[group_value] = counts.get(group_value, 0) + 1
        current = bucket.setdefault(group_value, {group_by: group_value})
        for key in numeric_keys:
            current[key] = round(float(current.get(key, 0)) + float(row.get(key, 0)), 2)
    if average_mode:
        for group_value, current in bucket.items():
            divisor = max(counts.get(group_value, 1), 1)
            for key in numeric_keys:
                current[key] = round(float(current.get(key, 0)) / divisor, 2)
    return list(bucket.values())


def _sort_rows(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    numeric_keys = _numeric_keys(rows)
    preferred = ["achievement_rate", "plan_gap_rate", "hold_load_index", "production_saturation_rate", "yield_rate", "production", "target", "defect_rate", "wip_qty", "hold_qty", "quantity", "uptime_pct"]
    metric = next((key for key in preferred if key in numeric_keys), numeric_keys[0] if numeric_keys else "")
    ordered = sorted(rows, key=lambda row: float(row.get(metric, 0) or 0), reverse=True) if metric else rows
    return ordered[:top_n] if top_n else ordered


def _join_on_keys(left_rows: list[dict[str, Any]], right_rows: list[dict[str, Any]], join_keys: list[str]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    right_index = {tuple(str(row.get(key) or "") for key in join_keys): row for row in right_rows}
    joined = []
    for left in left_rows:
        joined.append((left, right_index.get(tuple(str(left.get(key) or "") for key in join_keys), {})))
    return joined


def _apply_rule(rule: dict[str, Any], source_results: dict[str, list[dict[str, Any]]], params: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    mode = str(rule.get("calculation_mode") or "")
    group_by = params.get("group_by") or (rule.get("default_group_by") or ["process_name"])[0]
    top_n = int(params.get("top_n") or 0)
    if mode == "condition_flag":
        rows = [dict(row) for row in source_results.get((rule.get("required_datasets") or ["wip"])[0], [])]
        for row in rows:
            row[rule["output_column"]] = "\uc774\uc0c1" if str(row.get("\uc0c1\ud0dc") or "") in {"HOLD", "REWORK"} else "\uc815\uc0c1"
        return _sort_rows(rows, top_n)
    if mode == "preferred_metric":
        rows = [dict(row) for row in source_results.get("yield", [])]
        aggregated = _aggregate_rows(rows, group_by, average_mode=True)
        return _sort_rows(aggregated, top_n)

    dataset_keys = rule.get("required_datasets") or []
    if len(dataset_keys) < 2:
        return []
    join_keys = ["WORK_DT", "OPER_NAME"]
    for join_rule in registry.get("join_rules", []):
        if {join_rule.get("base_dataset"), join_rule.get("join_dataset")} == set(dataset_keys):
            join_keys = [str(item) for item in join_rule.get("join_keys") or [] if str(item).strip()] or join_keys
            break
    left_dataset, right_dataset = dataset_keys[0], dataset_keys[1]
    left_column = str((rule.get("source_columns") or [{}, {}])[0].get("column") or "")
    right_column = str((rule.get("source_columns") or [{}, {}])[1].get("column") or "")
    merged = []
    for left, right in _join_on_keys(source_results.get(left_dataset, []), source_results.get(right_dataset, []), join_keys):
        numerator = float(left.get(left_column, 0) or 0)
        denominator = float(right.get(right_column, 0) or 0)
        row = dict(left)
        if mode == "custom_ratio_gap":
            row[rule["output_column"]] = round(((numerator - denominator) / denominator) * 100, 2) if denominator else 0.0
        else:
            row[rule["output_column"]] = round((numerator / denominator) * 100, 2) if denominator else 0.0
        merged.append(row)
    return _sort_rows(_aggregate_rows(merged, group_by, average_mode=False), top_n)


def _build_followup_result(query: str, current_data: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    rows = list(current_data.get("rows") or [])
    if not rows:
        return {"response": "\uc774\uc804 \uacb0\uacfc\uac00 \uc5c6\uc5b4 \ud6c4\uc18d \ubd84\uc11d\uc744 \uc9c4\ud589\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", "tool_calls": [], "tool_results": [], "current_data": current_data, "extracted_params": params}
    lowered = query.lower()
    grouped = _aggregate_rows(rows, params.get("group_by") or "", average_mode=("\ud3c9\uade0" in query or "average" in lowered or "avg" in lowered))
    result_rows = _sort_rows(grouped, int(params.get("top_n") or 0))
    return {"response": f"\ud6c4\uc18d \ubd84\uc11d \uacb0\uacfc {len(result_rows)}\uac74\uc744 \ubc18\ud658\ud588\uc2b5\ub2c8\ub2e4.", "tool_calls": [], "tool_results": [], "current_data": {"title": "followup_result", "columns": list(result_rows[0].keys()) if result_rows else [], "rows": result_rows[:50]}, "extracted_params": params}


def _run_query(query: str, current_data: dict[str, Any] | None, registry: dict[str, Any]) -> dict[str, Any]:
    params = _extract_params(query, registry)
    matched_rules = _match_rules(query, registry)
    params["matched_analysis_rules"] = [str(rule.get("name") or "") for rule in matched_rules]

    if _is_followup(query, current_data, params, registry):
        result = _build_followup_result(query, current_data or {}, params)
        result["matched_analysis_rules"] = params["matched_analysis_rules"]
        result["selected_dataset_keys"] = (current_data or {}).get("selected_dataset_keys", [])
        return result

    dataset_keys = _detect_dataset_keys(query, matched_rules, registry)
    if any(dataset_key in registry.get("tool_manifest", {}) for dataset_key in dataset_keys) and not params.get("date"):
        return {"response": "\uc870\ud68c \uae30\uc900 \ub0a0\uc9dc\uac00 \ud544\uc694\ud569\ub2c8\ub2e4. \uc608: \uc624\ub298, \uc5b4\uc81c, 2026-04-12", "tool_calls": [], "tool_results": [], "current_data": current_data, "extracted_params": params, "selected_dataset_keys": dataset_keys, "matched_analysis_rules": params["matched_analysis_rules"], "failure_type": "missing_date"}

    source_results: dict[str, list[dict[str, Any]]] = {}
    tool_calls = []
    tool_results = []
    date_slices = _extract_date_slices(query, str(params.get("date") or ""))
    for dataset_key in dataset_keys:
        tool_name = registry.get("tool_manifest", {}).get(dataset_key, f"get_{dataset_key}_data")
        if len(dataset_keys) == 1 and len(date_slices) > 1:
            rows: list[dict[str, Any]] = []
            for item in date_slices:
                job_params = dict(params)
                job_params["date"] = item["date"]
                rows.extend(_filter_rows(_generate_rows(tool_name, dataset_key, job_params, registry, item["label"]), job_params))
                tool_calls.append({"tool_name": tool_name, "dataset_key": dataset_key, "params": job_params, "result_label": item["label"]})
            source_results[dataset_key] = rows
        else:
            rows = _filter_rows(_generate_rows(tool_name, dataset_key, params, registry, None), params)
            source_results[dataset_key] = rows
            tool_calls.append({"tool_name": tool_name, "dataset_key": dataset_key, "params": dict(params), "result_label": None})
        tool_results.append({"tool_name": tool_name, "dataset_key": dataset_key, "row_count": len(source_results[dataset_key])})

    if matched_rules:
        selected_rule = matched_rules[0]
        result_rows = _apply_rule(selected_rule, source_results, params, registry)
        response = f"{selected_rule.get('display_name') or selected_rule.get('name')} \uaddc\uce59\uc744 \uc801\uc6a9\ud574 {len(result_rows)}\uac74\uc744 \ubd84\uc11d\ud588\uc2b5\ub2c8\ub2e4."
    elif len(dataset_keys) == 1:
        result_rows = _sort_rows(_aggregate_rows(source_results[dataset_keys[0]], params.get("group_by") or "", average_mode=False), int(params.get("top_n") or 0))
        response = f"{dataset_keys[0]} \ub370\uc774\ud130\ub97c {len(result_rows)}\uac74 \ubc18\ud658\ud588\uc2b5\ub2c8\ub2e4."
    else:
        result_rows = [{"dataset_key": dataset_key, "row_count": len(rows), "tool_name": registry.get("tool_manifest", {}).get(dataset_key, "")} for dataset_key, rows in source_results.items()]
        response = f"{len(dataset_keys)}\uac1c dataset\uc744 \ub3d9\uc2dc \uc870\ud68c\ud558\uace0 \uac1c\uc694 \uacb0\uacfc\ub97c \uc815\ub9ac\ud588\uc2b5\ub2c8\ub2e4."

    return {
        "response": response,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "current_data": {"title": "portable_toolbox_result", "columns": list(result_rows[0].keys()) if result_rows else [], "rows": result_rows[:50], "selected_dataset_keys": dataset_keys},
        "extracted_params": params,
        "selected_dataset_keys": dataset_keys,
        "matched_analysis_rules": params["matched_analysis_rules"],
    }


class PortableManufacturingToolboxComponent(Component):
    display_name = "Portable Manufacturing Toolbox"
    description = "Agent/tool-calling friendly manufacturing query executor. Connect Domain Registry JSON for core-like dataset/rule parity."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "ToolCase"
    name = "portable_manufacturing_toolbox"

    inputs = [
        MultilineInput(name="query", display_name="Query", required=True, tool_mode=True, info="Natural language manufacturing question"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=True, info="Optional Portable Manufacturing Domain Registry JSON output"),
        StrInput(name="session_id", display_name="Session ID", value="", advanced=True, tool_mode=True, info="Optional fixed session id for multi-turn reuse"),
        MessageInput(name="message_history", display_name="Message History", advanced=True, info="Optional Message History input"),
        BoolInput(name="persist_session", display_name="Persist Session", value=True, advanced=True, info="If True, save current_data and chat history to a local session file"),
        StrInput(name="storage_subdir", display_name="Storage Subdir", value=".portable_langflow_sessions", advanced=True, info="Folder used to persist session JSON files"),
    ]

    outputs = [
        Output(name="result_data", display_name="Result Data", method="result_data", types=["Data"], selected="Data"),
        Output(name="response_message", display_name="Response Message", method="response_message", types=["Message"], selected="Message"),
    ]

    _cached_result: dict[str, Any] | None = None

    def _resolve_session_id(self) -> str:
        explicit = str(getattr(self, "session_id", "") or "").strip()
        if explicit:
            return _safe_session_id(explicit)
        history_session_id = _message_session_id(getattr(self, "message_history", None))
        if history_session_id:
            return _safe_session_id(history_session_id)
        graph = getattr(self, "graph", None)
        graph_session_id = getattr(graph, "session_id", "")
        return _safe_session_id(graph_session_id) if graph_session_id else "default"

    def _run(self) -> dict[str, Any]:
        if self._cached_result is not None:
            return self._cached_result

        query = str(getattr(self, "query", "") or "").strip()
        if not query:
            self.status = "No query"
            self._cached_result = {}
            return self._cached_result

        storage_subdir = str(getattr(self, "storage_subdir", "") or ".portable_langflow_sessions").strip() or ".portable_langflow_sessions"
        session_id = self._resolve_session_id()
        registry = _merge_registry(getattr(self, "domain_registry", None))
        snapshot = _load_snapshot(session_id, storage_subdir) if bool(getattr(self, "persist_session", True)) else {"chat_history": [], "context": {}, "current_data": None, "path": ""}

        result = _run_query(query, snapshot.get("current_data"), registry)
        result["session_id"] = session_id
        result["runtime"] = {"source": "portable_langflow_1_8_bundle", "mode": "toolbox"}
        result["registry_attached"] = bool(_as_payload(getattr(self, "domain_registry", None)))
        if bool(getattr(self, "persist_session", True)):
            result["session_memory_path"] = _save_snapshot(session_id, storage_subdir, query, result)
        else:
            result["session_memory_path"] = snapshot.get("path", "")

        self._cached_result = result
        self.status = f"Executed {len(result.get('tool_calls', []))} tool calls"
        return result

    def result_data(self) -> Data | None:
        payload = self._run()
        return Data(data=payload) if payload else None

    def response_message(self) -> Message | None:
        payload = self._run()
        if not payload:
            return None
        return Message(text=str(payload.get("response") or ""), data=payload, session_id=str(payload.get("session_id") or ""))
