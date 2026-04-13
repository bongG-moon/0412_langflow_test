"""Portable Langflow node: execute domain-aware manufacturing retrieval jobs."""

from __future__ import annotations

import hashlib
import json
import random
import re
from datetime import datetime
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


DEFAULT_REGISTRY = {
    "process_groups": {
        "DP": {"group_name": "DP", "synonyms": ["DP", "D/P"], "actual_values": ["WET1", "WET2", "L/T1", "L/T2", "B/G1", "B/G2", "H/S1", "H/S2", "W/S1", "W/S2"]},
        "DA": {"group_name": "D/A", "synonyms": ["D/A", "DA", "Die Attach", "die attach"], "actual_values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"]},
        "FCB": {"group_name": "FCB", "synonyms": ["FCB", "Flip Chip", "flip chip"], "actual_values": ["FCB1", "FCB2", "FCB/H"]},
        "PC": {"group_name": "P/C", "synonyms": ["P/C", "PC"], "actual_values": ["P/C1", "P/C2", "P/C3", "P/C4", "P/C5"]},
        "WB": {"group_name": "W/B", "synonyms": ["W/B", "WB", "Wire Bonding", "wire bonding"], "actual_values": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"]},
        "QCSPC": {"group_name": "QCSPC", "synonyms": ["QCSPC"], "actual_values": ["QCSPC1", "QCSPC2", "QCSPC3", "QCSPC4"]},
        "SAT": {"group_name": "SAT", "synonyms": ["SAT"], "actual_values": ["SAT1", "SAT2"]},
        "PL": {"group_name": "P/L", "synonyms": ["P/L", "PL"], "actual_values": ["PLH"]},
    },
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


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


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

    if isinstance(payload.get("process_groups"), dict):
        registry["process_groups"].update(payload["process_groups"])
    if isinstance(payload.get("tool_manifest"), dict):
        registry["tool_manifest"].update(payload["tool_manifest"])
    custom = payload.get("custom_registry")
    if isinstance(custom, dict) and isinstance(custom.get("value_groups"), list):
        registry["value_groups"] = list(custom.get("value_groups") or [])
    return registry


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


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return _unique([str(item) for item in value])
    if value:
        return [str(value).strip()]
    return []


def _default_joinable_lines() -> list[str]:
    return ["L1", "L2"]


def _default_processes() -> list[str]:
    return ["D/A1", "D/A2", "D/A3", "W/B1", "FCB1", "SAT1"]


def _job_params(job: dict[str, Any]) -> dict[str, Any]:
    params = job.get("params") if isinstance(job.get("params"), dict) else {}
    if params:
        return dict(params)
    return {
        "date": str(job.get("date") or ""),
        "process_name": _normalize_list(job.get("process_names")),
        "line_name": _normalize_list(job.get("line_names")),
        "mode": _normalize_list(job.get("mode_values")),
        "den": _normalize_list(job.get("den_values")),
        "tech": _normalize_list(job.get("tech_values")),
        "pkg_type1": _normalize_list(job.get("pkg_type1_values")),
        "pkg_type2": _normalize_list(job.get("pkg_type2_values")),
        "product_name": str(job.get("product_name") or "").strip() or None,
        "group_by": str(job.get("group_by") or "").strip() or None,
    }


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
        "line_name": line_name,
        "\uacf5\uc815\uad70": group_name,
        "OPER_NUM": f"{index_value + 1:03d}",
        "MODE": mode,
        "DEN": den,
        "TECH": tech,
        "PKG_TYPE1": pkg_type1,
        "PKG_TYPE2": pkg_type2,
        "LEAD": "AUTO" if index_value % 2 == 0 else "MANUAL",
        "MCP_NO": f"MCP-{family}-{index_value + 1:03d}",
        "FAMILY": family,
        "FACTORY": "FAB1" if family in {"DP", "DA"} else "PKG1",
        "ORG": "Back-End Process" if family in {"DP", "DA"} else "Package Assembly",
        "\ub77c\uc778": line_name,
        "product_name": f"{pkg_type1}-{mode}-{den}-{tech}",
    }


def _generate_rows(tool_name: str, dataset_key: str, params: dict[str, Any], registry: dict[str, Any], result_label: str | None) -> list[dict[str, Any]]:
    process_names = _normalize_list(params.get("process_name")) or _default_processes()
    line_names = _normalize_list(params.get("line_name")) or _default_joinable_lines()
    date_value = str(params.get("date") or datetime.now().strftime("%Y-%m-%d"))
    rng = _rng_for(tool_name, dataset_key, date_value, ",".join(process_names), str(result_label or ""))
    rows: list[dict[str, Any]] = []

    for process_index, process_name in enumerate(process_names):
        for line_index, line_name in enumerate(line_names):
            base = _base_row(date_value, process_name, line_name, process_index + line_index, registry)
            row = dict(base)
            production = rng.randint(800, 1800)
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
                row["LOT_ID"] = f"LOT-{date_value.replace('-', '')}-{process_index + line_index + 1:03d}"
                row["\uc0c1\ud0dc"] = rng.choice(["WAIT", "RUNNING", "MOVE_OUT", "HOLD", "REWORK", "COMPLETE"])
            rows.append(row)
    return rows


def _filter_rows(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if _normalize_list(params.get("process_name")) and str(row.get("process_name")) not in _normalize_list(params.get("process_name")):
            continue
        if _normalize_list(params.get("mode")) and str(row.get("MODE")) not in _normalize_list(params.get("mode")):
            continue
        if _normalize_list(params.get("den")) and str(row.get("DEN")) not in _normalize_list(params.get("den")):
            continue
        if _normalize_list(params.get("tech")) and str(row.get("TECH")) not in _normalize_list(params.get("tech")):
            continue
        if _normalize_list(params.get("pkg_type1")) and str(row.get("PKG_TYPE1")) not in _normalize_list(params.get("pkg_type1")):
            continue
        if _normalize_list(params.get("pkg_type2")) and str(row.get("PKG_TYPE2")) not in _normalize_list(params.get("pkg_type2")):
            continue
        if _normalize_list(params.get("line_name")) and str(row.get("line_name")) not in _normalize_list(params.get("line_name")):
            continue
        product_name = str(params.get("product_name") or "").strip()
        if product_name and str(row.get("product_name") or "") != product_name:
            continue
        filtered.append(row)
    return filtered


class PortableManufacturingToolExecutorComponent(Component):
    display_name = "Portable Manufacturing Tool Executor"
    description = "Execute registry-aware synthetic retrieval jobs with core-like tool names and row schema."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Wrench"
    name = "portable_manufacturing_tool_executor"

    inputs = [
        DataInput(name="state", display_name="State", info="Jobs state from a retrieval-planning node"),
        DataInput(name="domain_registry", display_name="Domain Registry", advanced=False, info="Optional registry JSON for tool manifest and groups"),
    ]

    outputs = [
        Output(name="state_with_source_results", display_name="State With Source Results", method="state_with_source_results", types=["Data"], selected="Data"),
    ]

    def state_with_source_results(self) -> Data | None:
        state = _as_payload(getattr(self, "state", None))
        retrieval_jobs = state.get("retrieval_jobs") if isinstance(state.get("retrieval_jobs"), list) else []
        if not retrieval_jobs:
            self.status = "No retrieval jobs"
            return None

        registry = _merge_registry(getattr(self, "domain_registry", None))
        source_results: dict[str, list[dict[str, Any]]] = {}
        tool_results: list[dict[str, Any]] = []
        tool_calls: list[dict[str, Any]] = []
        selected_dataset_keys: list[str] = []

        for job in retrieval_jobs:
            if not isinstance(job, dict):
                continue
            dataset_key = str(job.get("dataset_key") or "").strip()
            if not dataset_key:
                continue
            params = _job_params(job)
            result_label = str(job.get("result_label") or "").strip() or None
            tool_name = str(registry.get("tool_manifest", {}).get(dataset_key) or f"get_{dataset_key}_data")
            rows = _filter_rows(_generate_rows(tool_name, dataset_key, params, registry, result_label), params)
            source_results.setdefault(dataset_key, []).extend(rows)
            tool_results.append({"dataset_key": dataset_key, "tool_name": tool_name, "row_count": len(rows)})
            tool_calls.append({"tool_name": tool_name, "dataset_key": dataset_key, "params": params, "result_label": result_label})
            if dataset_key not in selected_dataset_keys:
                selected_dataset_keys.append(dataset_key)

        overview_rows = [
            {"dataset_key": item["dataset_key"], "tool_name": item["tool_name"], "row_count": item["row_count"]}
            for item in tool_results
        ]
        updated_state = {
            **state,
            "source_results": source_results,
            "tool_results": tool_results,
            "tool_calls": tool_calls,
            "selected_dataset_keys": selected_dataset_keys,
            "retrieval_result_overview": {
                "title": "retrieval_overview",
                "columns": ["dataset_key", "tool_name", "row_count"],
                "rows": overview_rows,
            },
        }
        self.status = f"Executed {len(tool_results)} dataset tools"
        return Data(data=updated_state)
