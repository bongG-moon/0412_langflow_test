"""Portable Langflow node: domain-rich manufacturing pipeline for Add Custom Node environments."""

from __future__ import annotations

import hashlib
import random
import re
from datetime import datetime, timedelta
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


PROCESS_GROUPS = {
    "DA": {
        "synonyms": ["D/A", "DA", "Die Attach", "die attach", "다이어태치", "다이본딩"],
        "actual_values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
    },
    "WB": {
        "synonyms": ["W/B", "WB", "Wire Bonding", "wire bonding", "와이어본딩"],
        "actual_values": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"],
    },
    "FCB": {
        "synonyms": ["FCB", "Flip Chip", "flip chip", "플립칩"],
        "actual_values": ["FCB1", "FCB2", "FCB/H"],
    },
    "BM": {
        "synonyms": ["B/M", "BM", "비엠"],
        "actual_values": ["B/M"],
    },
    "PC": {
        "synonyms": ["P/C", "PC"],
        "actual_values": ["P/C1", "P/C2", "P/C3", "P/C4", "P/C5"],
    },
    "QCSPC": {
        "synonyms": ["QCSPC"],
        "actual_values": ["QCSPC1", "QCSPC2", "QCSPC3", "QCSPC4"],
    },
    "SAT": {
        "synonyms": ["SAT"],
        "actual_values": ["SAT1", "SAT2"],
    },
    "PL": {
        "synonyms": ["P/L", "PL"],
        "actual_values": ["PLH"],
    },
    "DP": {
        "synonyms": ["DP", "D/P"],
        "actual_values": ["WET1", "WET2", "L/T1", "L/T2", "B/G1", "B/G2", "H/S1", "H/S2", "W/S1", "W/S2"],
    },
}

MODE_GROUPS = {
    "DDR4": {"synonyms": ["DDR4", "디디알4", "DDR 4"], "actual_values": ["DDR4"]},
    "DDR5": {"synonyms": ["DDR5", "디디알5", "DDR 5"], "actual_values": ["DDR5"]},
    "LPDDR5": {"synonyms": ["LPDDR5", "LP DDR5", "엘피디디알5", "LP5", "저전력DDR5"], "actual_values": ["LPDDR5"]},
}

DEN_GROUPS = {
    "256G": {"synonyms": ["256G", "256기가", "256Gb", "256gb"], "actual_values": ["256G"]},
    "512G": {"synonyms": ["512G", "512기가", "512Gb", "512gb"], "actual_values": ["512G"]},
    "1T": {"synonyms": ["1T", "1테라", "1Tb", "1tb", "1TB"], "actual_values": ["1T"]},
}

TECH_GROUPS = {
    "LC": {"synonyms": ["LC", "엘씨", "LC제품", "엘시"], "actual_values": ["LC"]},
    "FO": {"synonyms": ["FO", "팬아웃", "FO제품", "fan-out", "Fan-Out", "에프오"], "actual_values": ["FO"]},
    "FC": {"synonyms": ["FC", "플립칩", "FC제품", "에프씨"], "actual_values": ["FC"]},
}

PKG_TYPE1_GROUPS = {
    "FCBGA": {"synonyms": ["FCBGA", "fcbga"], "actual_values": ["FCBGA"]},
    "LFBGA": {"synonyms": ["LFBGA", "lfbga"], "actual_values": ["LFBGA"]},
}

PKG_TYPE2_GROUPS = {
    "ODP": {"synonyms": ["ODP", "odp"], "actual_values": ["ODP"]},
    "16DP": {"synonyms": ["16DP", "16dp"], "actual_values": ["16DP"]},
    "SDP": {"synonyms": ["SDP", "sdp"], "actual_values": ["SDP"]},
}

CUSTOM_VALUE_GROUPS = [
    {
        "field": "process_name",
        "canonical": "후공정A",
        "synonyms": ["후공정A"],
        "values": ["D/A1", "D/A2"],
    }
]

DATASET_KEYWORDS = {
    "production": ["생산", "생산량", "production"],
    "target": ["목표", "목표량", "계획", "target"],
    "wip": ["재공", "wip"],
    "hold": ["홀드", "hold"],
    "defect": ["불량", "결함", "defect"],
    "yield": ["수율", "yield", "양품률"],
    "equipment": ["설비", "장비", "equipment", "uptime", "alarm"],
    "scrap": ["스크랩", "폐기", "scrap"],
    "recipe": ["레시피", "공정 조건", "recipe"],
    "lot_trace": ["lot", "로트", "이력", "trace"],
}

ANALYSIS_RULES = [
    {
        "name": "achievement_rate",
        "synonyms": ["achievement rate", "달성률", "생산 달성률", "목표 대비 생산"],
        "required_datasets": ["production", "target"],
        "calculation_mode": "ratio",
        "numerator_dataset": "production",
        "numerator_column": "production",
        "denominator_dataset": "target",
        "denominator_column": "target",
        "output_column": "achievement_rate",
        "default_group_by": ["process_name"],
    },
    {
        "name": "yield_rate",
        "synonyms": ["yield", "yield rate", "수율", "양품률"],
        "required_datasets": ["yield"],
        "calculation_mode": "preferred_metric",
        "preferred_column": "yield_rate",
        "fallback_formula": "pass_qty / tested_qty",
        "output_column": "yield_rate",
        "default_group_by": ["process_name"],
    },
    {
        "name": "production_saturation_rate",
        "synonyms": ["production saturation", "production saturation rate", "포화율", "생산 포화율", "생산포화율"],
        "required_datasets": ["production", "wip"],
        "calculation_mode": "ratio",
        "numerator_dataset": "production",
        "numerator_column": "production",
        "denominator_dataset": "wip",
        "denominator_column": "wip_qty",
        "output_column": "production_saturation_rate",
        "default_group_by": ["process_name"],
    },
    {
        "name": "hold_anomaly_check",
        "synonyms": ["hold_anomaly_check", "HOLD 이상여부", "홀드 체크"],
        "required_datasets": ["wip"],
        "calculation_mode": "condition_flag",
        "source_dataset": "wip",
        "source_column": "상태",
        "output_column": "hold_anomaly_flag",
        "default_group_by": [],
    },
    {
        "name": "plan_gap_rate",
        "synonyms": ["plan_gap_rate", "생산 목표 차이율", "목표 차이율", "계획 차이율"],
        "required_datasets": ["production", "target"],
        "calculation_mode": "custom_ratio_gap",
        "numerator_dataset": "production",
        "numerator_column": "production",
        "denominator_dataset": "target",
        "denominator_column": "target",
        "output_column": "plan_gap_rate",
        "default_group_by": ["process_name"],
    },
    {
        "name": "hold_load_index",
        "synonyms": ["hold_load_index", "홀드 부하지수", "부하지수"],
        "required_datasets": ["hold", "production"],
        "calculation_mode": "ratio",
        "numerator_dataset": "hold",
        "numerator_column": "hold_qty",
        "denominator_dataset": "production",
        "denominator_column": "production",
        "output_column": "hold_load_index",
        "default_group_by": ["process_name"],
    },
]


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


def _normalize(text: Any) -> str:
    return re.sub(r"[^a-z0-9가-힣/]+", "", str(text or "").lower())


def _contains_alias(text: str, alias: str) -> bool:
    return _normalize(alias) in _normalize(text)


def _detect_date(text: str) -> str:
    lowered = text.lower()
    now = datetime.now()
    if "어제" in text or "yesterday" in lowered:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if "오늘" in text or "today" in lowered:
        return now.strftime("%Y-%m-%d")
    compact = re.search(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?(0[1-9]|[12]\d|3[01])", text)
    if compact:
        return f"{compact.group(1)}-{compact.group(2)}-{compact.group(3)}"
    return ""


def _expand_group_values(text: str, field_name: str, groups: dict[str, dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for group in groups.values():
        aliases = group.get("synonyms", []) + group.get("actual_values", [])
        if any(_contains_alias(text, alias) for alias in aliases):
            for actual in group.get("actual_values", []):
                if actual not in values:
                    values.append(actual)
    for custom in CUSTOM_VALUE_GROUPS:
        if custom.get("field") != field_name:
            continue
        aliases = custom.get("synonyms", []) + [custom.get("canonical", "")]
        if any(_contains_alias(text, alias) for alias in aliases):
            for actual in custom.get("values", []):
                if actual not in values:
                    values.append(actual)
    return values


def _detect_direct_processes(text: str) -> list[str]:
    patterns = [
        r"D/A\d",
        r"W/B\d",
        r"FCB/H",
        r"FCB\d",
        r"P/C\d",
        r"QCSPC\d",
        r"SAT\d",
        r"WET\d",
        r"L/T\d",
        r"B/G\d",
        r"H/S\d",
        r"W/S\d",
        r"PLH",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            normalized = match.upper()
            if normalized not in found:
                found.append(normalized)
    return found


def _detect_group_by(text: str) -> str:
    lowered = text.lower()
    if "공정별" in text or "by process" in lowered:
        return "process_name"
    if "라인별" in text or "by line" in lowered:
        return "line_name"
    if "제품별" in text or "by product" in lowered:
        return "product_name"
    if "mode별" in text or "by mode" in lowered:
        return "MODE"
    if "기술별" in text or "by tech" in lowered:
        return "TECH"
    return ""


def _detect_top_n(text: str) -> int:
    match = re.search(r"(?:상위|top)\s*(\d+)", text.lower())
    return int(match.group(1)) if match else 0


def _detect_dataset_keys(text: str, matched_rules: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for dataset_key, keywords in DATASET_KEYWORDS.items():
        if any(_contains_alias(text, keyword) for keyword in keywords):
            keys.append(dataset_key)
    for rule in matched_rules:
        for dataset_key in rule.get("required_datasets", []):
            if dataset_key not in keys:
                keys.append(dataset_key)
    return keys or ["production"]


def _match_rules(text: str) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for rule in ANALYSIS_RULES:
        if any(_contains_alias(text, synonym) for synonym in rule.get("synonyms", [])):
            matched.append(rule)
    return matched


def _message_requests_followup(text: str) -> bool:
    followup_keywords = ["그 결과", "그거", "위 결과", "정리", "상위", "평균", "합계", "비교", "공정별", "라인별", "제품별"]
    lowered = text.lower()
    return any(keyword in text for keyword in followup_keywords) or any(keyword in lowered for keyword in ["top", "average", "sum", "group"])


def _extract_params(text: str) -> dict[str, Any]:
    process_values = _expand_group_values(text, "process_name", PROCESS_GROUPS)
    for process_name in _detect_direct_processes(text):
        if process_name not in process_values:
            process_values.append(process_name)
    return {
        "date": _detect_date(text),
        "process_names": process_values,
        "mode_values": _expand_group_values(text, "mode", MODE_GROUPS),
        "den_values": _expand_group_values(text, "den", DEN_GROUPS),
        "tech_values": _expand_group_values(text, "tech", TECH_GROUPS),
        "pkg_type1_values": _expand_group_values(text, "pkg_type1", PKG_TYPE1_GROUPS),
        "pkg_type2_values": _expand_group_values(text, "pkg_type2", PKG_TYPE2_GROUPS),
        "group_by": _detect_group_by(text),
        "top_n": _detect_top_n(text),
    }


def _rng_for(*parts: str) -> random.Random:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return random.Random(int(digest, 16))


def _base_dimensions(date_value: str, process_name: str, line_name: str, index_value: int) -> dict[str, Any]:
    mode = ["DDR4", "DDR5", "LPDDR5"][index_value % 3]
    den = ["256G", "512G", "1T"][index_value % 3]
    tech = ["LC", "FO", "FC"][index_value % 3]
    pkg1 = ["FCBGA", "LFBGA"][index_value % 2]
    pkg2 = ["ODP", "16DP", "SDP"][index_value % 3]
    product_name = f"{pkg1}-{mode}-{den}"
    return {
        "date": date_value,
        "WORK_DT": date_value.replace("-", ""),
        "process_name": process_name,
        "OPER_NAME": process_name,
        "line_name": line_name,
        "라인": line_name,
        "MODE": mode,
        "DEN": den,
        "TECH": tech,
        "PKG_TYPE1": pkg1,
        "PKG_TYPE2": pkg2,
        "product_name": product_name,
        "MCP_NO": f"MCP-{process_name.replace('/', '')}-{index_value + 1}",
    }


def _generate_dataset_rows(dataset_key: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    process_names = params.get("process_names") or ["D/A1", "D/A2", "D/A3", "W/B1", "FCB1"]
    date_value = str(params.get("date") or datetime.now().strftime("%Y-%m-%d"))
    rows: list[dict[str, Any]] = []
    rng = _rng_for(dataset_key, date_value, ",".join(process_names))

    for index_value, process_name in enumerate(process_names):
        for line_suffix in range(1, 3):
            base = _base_dimensions(date_value, process_name, f"{process_name.split('/')[0]}-L{line_suffix}", index_value + line_suffix)
            production_value = rng.randint(800, 1800)
            row = dict(base)
            if dataset_key == "production":
                row["production"] = production_value
                row["quantity"] = production_value
            elif dataset_key == "target":
                row["target"] = int(production_value * rng.uniform(1.02, 1.15))
            elif dataset_key == "wip":
                row["wip_qty"] = int(production_value * rng.uniform(0.08, 0.22))
                row["상태"] = rng.choice(["WAIT", "RUN", "HOLD", "REWORK"])
            elif dataset_key == "hold":
                row["hold_qty"] = rng.randint(0, 120)
                row["상태"] = rng.choice(["HOLD", "REWORK", "WAIT"])
            elif dataset_key == "defect":
                row["defect_qty"] = max(5, int(production_value * rng.uniform(0.01, 0.05)))
                row["defect_reason"] = rng.choice(["void", "scratch", "lift", "contamination"])
            elif dataset_key == "yield":
                tested_qty = production_value
                pass_qty = int(tested_qty * rng.uniform(0.92, 0.995))
                row["tested_qty"] = tested_qty
                row["pass_qty"] = pass_qty
                row["yield_rate"] = round((pass_qty / tested_qty) * 100, 2)
            elif dataset_key == "equipment":
                row["equipment_id"] = f"{process_name.replace('/', '')}-{line_suffix}"
                row["uptime_pct"] = round(rng.uniform(88.0, 99.5), 2)
                row["alarm_minutes"] = rng.randint(0, 60)
            elif dataset_key == "scrap":
                row["scrap_qty"] = rng.randint(0, 40)
                row["scrap_reason"] = rng.choice(["crack", "void", "label_ng", "wire_open"])
            elif dataset_key == "recipe":
                row["temp_c"] = rng.randint(25, 240)
                row["pressure_kpa"] = rng.randint(0, 130)
                row["process_time_sec"] = rng.randint(120, 600)
            elif dataset_key == "lot_trace":
                row["LOT_ID"] = f"LOT-{date_value.replace('-', '')}-{index_value + 1:03d}"
                row["상태"] = rng.choice(["WAIT", "RUNNING", "MOVE_OUT", "HOLD", "REWORK", "COMPLETE"])
            rows.append(row)
    return rows


def _filter_rows(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
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
        filtered.append(row)
    return filtered


def _numeric_keys(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    keys: list[str] = []
    for key in rows[0]:
        if all(isinstance(row.get(key), (int, float)) for row in rows if key in row):
            keys.append(key)
    return keys


def _aggregate_rows(rows: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    if not group_by:
        return rows
    numeric_keys = _numeric_keys(rows)
    bucket: dict[str, dict[str, Any]] = {}
    for row in rows:
        group_value = str(row.get(group_by) or "unknown")
        current = bucket.setdefault(group_value, {group_by: group_value})
        for key in numeric_keys:
            current[key] = round(float(current.get(key, 0)) + float(row.get(key, 0)), 2)
    return list(bucket.values())


def _sort_rows(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    numeric_keys = _numeric_keys(rows)
    metric = next((key for key in ["achievement_rate", "plan_gap_rate", "hold_load_index", "production", "quantity", "yield_rate", "defect_qty", "wip_qty"] if key in numeric_keys), numeric_keys[0] if numeric_keys else "")
    sorted_rows = sorted(rows, key=lambda row: float(row.get(metric, 0) or 0), reverse=True) if metric else rows
    return sorted_rows[:top_n] if top_n else sorted_rows


def _join_on_process(left_rows: list[dict[str, Any]], right_rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    right_index = {(str(row.get("OPER_NAME") or ""), str(row.get("WORK_DT") or "")): row for row in right_rows}
    joined: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for left in left_rows:
        key = (str(left.get("OPER_NAME") or ""), str(left.get("WORK_DT") or ""))
        right = right_index.get(key, {})
        joined.append((left, right))
    return joined


def _apply_rule(rule: dict[str, Any], source_results: dict[str, list[dict[str, Any]]], params: dict[str, Any]) -> list[dict[str, Any]]:
    mode = str(rule.get("calculation_mode") or "")
    group_by = params.get("group_by") or (rule.get("default_group_by") or ["process_name"])[0]

    if mode == "condition_flag":
        rows = [dict(row) for row in source_results.get(rule.get("source_dataset"), [])]
        for row in rows:
            status = str(row.get(rule.get("source_column")) or "")
            row[rule["output_column"]] = "이상" if status in {"HOLD", "REWORK"} else "정상"
        return _sort_rows(_aggregate_rows(rows, group_by if group_by in rows[0] else ""), int(params.get("top_n") or 0)) if rows else []

    if mode == "preferred_metric":
        rows = [dict(row) for row in source_results.get("yield", [])]
        for row in rows:
            if rule.get("preferred_column") not in row:
                tested = float(row.get("tested_qty", 0) or 0)
                passed = float(row.get("pass_qty", 0) or 0)
                row[rule["output_column"]] = round((passed / tested) * 100, 2) if tested else 0.0
        return _sort_rows(_aggregate_rows(rows, group_by), int(params.get("top_n") or 0))

    left_rows = source_results.get(rule.get("numerator_dataset"), [])
    right_rows = source_results.get(rule.get("denominator_dataset"), [])
    joined_rows: list[dict[str, Any]] = []
    for left, right in _join_on_process(left_rows, right_rows):
        row = dict(left)
        numerator = float(left.get(rule.get("numerator_column"), 0) or 0)
        denominator = float(right.get(rule.get("denominator_column"), 0) or 0)
        row[rule.get("denominator_column")] = denominator
        if mode == "custom_ratio_gap":
            row[rule["output_column"]] = round(((numerator - denominator) / denominator) * 100, 2) if denominator else 0.0
        else:
            row[rule["output_column"]] = round((numerator / denominator) * 100, 2) if denominator else 0.0
        joined_rows.append(row)
    return _sort_rows(_aggregate_rows(joined_rows, group_by), int(params.get("top_n") or 0))


def _build_followup_result(state: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else None
    rows = list((current_data or {}).get("rows") or [])
    if not rows:
        return {
            "response": "이전 조회 결과가 없어 후속 분석을 진행할 수 없습니다.",
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": params,
            "failure_type": "missing_current_data",
            "awaiting_analysis_choice": False,
        }
    grouped = _aggregate_rows(rows, params.get("group_by") or "")
    transformed = _sort_rows(grouped, int(params.get("top_n") or 0))
    return {
        "response": f"후속 분석 결과입니다. {len(transformed)}건을 반환했습니다.",
        "tool_results": [],
        "current_data": {"title": "followup_result", "columns": list(transformed[0].keys()) if transformed else [], "rows": transformed[:20]},
        "extracted_params": params,
        "awaiting_analysis_choice": False,
    }


class PortableManufacturingFullPipelineComponent(Component):
    display_name = "Portable Manufacturing Full Pipeline"
    description = "Portable full-fidelity manufacturing pipeline with embedded domain registry and analysis rules."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Workflow"
    name = "portable_manufacturing_full_pipeline"

    inputs = [
        DataInput(name="state", display_name="State", info="Session state from Portable Manufacturing Session State"),
    ]

    outputs = [
        Output(name="result_data", display_name="Result Data", method="result_data", types=["Data"], selected="Data"),
        Output(name="response_message", display_name="Response Message", method="response_message", types=["Message"], selected="Message"),
    ]

    _cached_result: dict[str, Any] | None = None

    def _run(self) -> dict[str, Any]:
        if self._cached_result is not None:
            return self._cached_result

        state = _as_payload(getattr(self, "state", None))
        user_input = str(state.get("user_input") or "").strip()
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else None

        params = _extract_params(user_input)
        matched_rules = _match_rules(user_input)
        params["matched_analysis_rules"] = [rule["name"] for rule in matched_rules]

        explicit_reset = bool(params.get("date")) or any(keyword in user_input for keyword in ["생산", "목표", "불량", "수율", "양품률", "재공", "홀드", "설비"])
        query_mode = "followup" if current_data and _message_requests_followup(user_input) and not explicit_reset else "retrieval"

        if query_mode == "followup":
            result = _build_followup_result(state, params)
            self._cached_result = result
            self.status = "Full pipeline follow-up"
            return result

        dataset_keys = _detect_dataset_keys(user_input, matched_rules)
        requires_date = any(dataset_key in {"production", "target", "wip", "hold", "defect", "yield", "scrap", "recipe", "lot_trace"} for dataset_key in dataset_keys)
        if requires_date and not params.get("date"):
            result = {
                "response": "조회 기준 날짜가 필요합니다. 예: 오늘, 어제, 2026-04-12",
                "tool_results": [],
                "current_data": current_data,
                "extracted_params": params,
                "failure_type": "missing_date",
                "awaiting_analysis_choice": False,
            }
            self._cached_result = result
            self.status = "Missing date"
            return result

        source_results: dict[str, list[dict[str, Any]]] = {}
        tool_results: list[dict[str, Any]] = []
        for dataset_key in dataset_keys:
            rows = _filter_rows(_generate_dataset_rows(dataset_key, params), params)
            source_results[dataset_key] = rows
            tool_results.append({"dataset_key": dataset_key, "row_count": len(rows)})

        if matched_rules:
            rule = matched_rules[0]
            result_rows = _apply_rule(rule, source_results, params)
            response = f"{rule['name']} 규칙을 적용한 분석 결과입니다. 총 {len(result_rows)}건입니다."
        elif len(dataset_keys) == 1:
            rows = source_results[dataset_keys[0]]
            grouped = _aggregate_rows(rows, params.get("group_by") or "")
            result_rows = _sort_rows(grouped, int(params.get("top_n") or 0))
            response = f"{dataset_keys[0]} 데이터 조회 결과입니다. 총 {len(result_rows)}건입니다."
        else:
            fallback_rule = next((rule for rule in ANALYSIS_RULES if set(rule.get("required_datasets", [])) == set(dataset_keys)), None)
            if fallback_rule:
                result_rows = _apply_rule(fallback_rule, source_results, params)
                response = f"{fallback_rule['name']} 분석 결과입니다. 총 {len(result_rows)}건입니다."
            else:
                merged_rows: list[dict[str, Any]] = []
                for dataset_key, rows in source_results.items():
                    merged_rows.append({"dataset_key": dataset_key, "row_count": len(rows)})
                result_rows = merged_rows
                response = f"다중 데이터셋 개요 결과입니다. {len(dataset_keys)}개 데이터셋을 조회했습니다."

        result = {
            "response": response,
            "tool_results": tool_results,
            "current_data": {"title": "full_pipeline_result", "columns": list(result_rows[0].keys()) if result_rows else [], "rows": result_rows[:50]},
            "extracted_params": params,
            "matched_analysis_rules": params["matched_analysis_rules"],
            "selected_dataset_keys": dataset_keys,
            "awaiting_analysis_choice": False,
        }
        self._cached_result = result
        self.status = "Full pipeline retrieval"
        return result

    def result_data(self) -> Data:
        return Data(data=self._run())

    def response_message(self) -> Message:
        payload = self._run()
        session_id = str(_as_payload(getattr(self, "state", None)).get("session_id") or "")
        return Message(text=str(payload.get("response") or ""), data=payload, session_id=session_id)

