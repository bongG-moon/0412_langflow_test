"""Portable Langflow node: expose embedded manufacturing domain registry as JSON/Data."""

from __future__ import annotations

import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.message import Message


def _tool_manifest() -> dict[str, str]:
    return {
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
    }


def _dataset_metadata() -> dict[str, dict[str, Any]]:
    return {
        "production": {
            "label": "production",
            "description": "Production quantity and input/output records by process.",
            "requires_date": True,
            "primary_metrics": ["production", "quantity"],
        },
        "target": {
            "label": "target",
            "description": "Target or plan quantity by process.",
            "requires_date": True,
            "primary_metrics": ["target"],
        },
        "defect": {
            "label": "defect",
            "description": "Defect quantity and defect rate records.",
            "requires_date": True,
            "primary_metrics": ["defect_qty", "defect_rate"],
        },
        "equipment": {
            "label": "equipment",
            "description": "Equipment uptime, alarm minutes, and status.",
            "requires_date": True,
            "primary_metrics": ["uptime_pct", "alarm_minutes"],
        },
        "wip": {
            "label": "wip",
            "description": "Work-in-progress quantity and status.",
            "requires_date": True,
            "primary_metrics": ["wip_qty"],
        },
        "yield": {
            "label": "yield",
            "description": "Yield/pass-rate records with tested/pass quantities.",
            "requires_date": True,
            "primary_metrics": ["yield_rate", "pass_qty", "tested_qty"],
        },
        "hold": {
            "label": "hold",
            "description": "Hold quantity and hold status records.",
            "requires_date": True,
            "primary_metrics": ["hold_qty"],
        },
        "scrap": {
            "label": "scrap",
            "description": "Scrap quantity and scrap reason records.",
            "requires_date": True,
            "primary_metrics": ["scrap_qty"],
        },
        "recipe": {
            "label": "recipe",
            "description": "Recipe parameters such as temperature, pressure, and time.",
            "requires_date": True,
            "primary_metrics": ["temp_c", "pressure_kpa", "process_time_sec"],
        },
        "lot_trace": {
            "label": "lot_trace",
            "description": "Lot tracking and lot status transitions.",
            "requires_date": True,
            "primary_metrics": ["LOT_ID"],
        },
    }


def _process_groups() -> dict[str, dict[str, Any]]:
    return {
        "DP": {"group_name": "DP", "synonyms": ["DP", "D/P"], "actual_values": ["WET1", "WET2", "L/T1", "L/T2", "B/G1", "B/G2", "H/S1", "H/S2", "W/S1", "W/S2", "WSD1", "WSD2", "WEC1", "WEC2", "WLS1", "WLS2", "WVI", "UV", "C/C1"]},
        "WET": {"group_name": "WET", "synonyms": ["WET"], "actual_values": ["WET1", "WET2"]},
        "LT": {"group_name": "L/T", "synonyms": ["LT", "L/T"], "actual_values": ["L/T1", "L/T2"]},
        "BG": {"group_name": "B/G", "synonyms": ["BG", "B/G"], "actual_values": ["B/G1", "B/G2"]},
        "HS": {"group_name": "H/S", "synonyms": ["HS", "H/S"], "actual_values": ["H/S1", "H/S2"]},
        "WS": {"group_name": "W/S", "synonyms": ["WS", "W/S"], "actual_values": ["W/S1", "W/S2"]},
        "DA": {"group_name": "D/A", "synonyms": ["D/A", "DA", "Die Attach", "DIE ATTACH", "\ub2e4\uc774\uc5b4\ud0dc\uce58", "\ub2e4\uc774\ubcf8\ub529"], "actual_values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"]},
        "PCO": {"group_name": "PCO", "synonyms": ["PCO"], "actual_values": ["PCO1", "PCO2", "PCO3", "PCO4", "PCO5", "PCO6"]},
        "DC": {"group_name": "D/C", "synonyms": ["D/C", "DC"], "actual_values": ["D/C1", "D/C2", "D/C3", "D/C4"]},
        "DI": {"group_name": "D/I", "synonyms": ["D/I", "DI"], "actual_values": ["D/I"]},
        "DS": {"group_name": "D/S", "synonyms": ["D/S", "DS"], "actual_values": ["D/S1"]},
        "FCB": {"group_name": "FCB", "synonyms": ["FCB", "Flip Chip", "\ud50c\ub9bd\uce69"], "actual_values": ["FCB1", "FCB2", "FCB/H"]},
        "FCBH": {"group_name": "FCB/H", "synonyms": ["FCB/H", "FCBH"], "actual_values": ["FCB/H"]},
        "BM": {"group_name": "B/M", "synonyms": ["B/M", "BN", "\ube44\uc5e0"], "actual_values": ["B/M"]},
        "PC": {"group_name": "P/C", "synonyms": ["P/C", "PC"], "actual_values": ["P/C1", "P/C2", "P/C3", "P/C4", "P/C5"]},
        "WB": {"group_name": "W/B", "synonyms": ["W/B", "WB", "Wire Bonding", "\uc640\uc774\uc5b4\ubcf8\ub529"], "actual_values": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"]},
        "QCSPC": {"group_name": "QCSPC", "synonyms": ["QCSPC"], "actual_values": ["QCSPC1", "QCSPC2", "QCSPC3", "QCSPC4"]},
        "SAT": {"group_name": "SAT", "synonyms": ["SAT"], "actual_values": ["SAT1", "SAT2"]},
        "PL": {"group_name": "P/L", "synonyms": ["P/L", "PL"], "actual_values": ["PLH"]},
    }


def _attribute_groups() -> dict[str, dict[str, Any]]:
    return {
        "mode": {
            "DDR4": {"synonyms": ["DDR4", "\ub514\ub514\uc54c4", "DDR 4"], "actual_values": ["DDR4"]},
            "DDR5": {"synonyms": ["DDR5", "\ub514\ub514\uc54c5", "DDR 5"], "actual_values": ["DDR5"]},
            "LPDDR5": {"synonyms": ["LPDDR5", "LP DDR5", "\uc5d8\ud53c\ub514\ub514\uc54c5", "LP5", "\uc800\uc804\ub825DDR5"], "actual_values": ["LPDDR5"]},
        },
        "den": {
            "256G": {"synonyms": ["256G", "256\uae30\uac00", "256Gb", "256gb"], "actual_values": ["256G"]},
            "512G": {"synonyms": ["512G", "512\uae30\uac00", "512Gb", "512gb"], "actual_values": ["512G"]},
            "1T": {"synonyms": ["1T", "1\ud14c\ub77c", "1Tb", "1tb", "1TB"], "actual_values": ["1T"]},
        },
        "tech": {
            "LC": {"synonyms": ["LC", "\uc5d8\uc528", "LC\uc81c\ud488", "\uc5d8\uc2dc"], "actual_values": ["LC"]},
            "FO": {"synonyms": ["FO", "\ud32c\uc544\uc6c3", "FO\uc81c\ud488", "fan-out", "Fan-Out", "\uc5d0\ud504\uc624"], "actual_values": ["FO"]},
            "FC": {"synonyms": ["FC", "\ud50c\ub9bd\uce69", "FC\uc81c\ud488", "\uc5d0\ud504\uc528"], "actual_values": ["FC"]},
        },
        "pkg_type1": {
            "FCBGA": {"synonyms": ["FCBGA", "fcbga"], "actual_values": ["FCBGA"]},
            "LFBGA": {"synonyms": ["LFBGA", "lfbga"], "actual_values": ["LFBGA"]},
        },
        "pkg_type2": {
            "ODP": {"synonyms": ["ODP", "odp"], "actual_values": ["ODP"]},
            "16DP": {"synonyms": ["16DP", "16dp"], "actual_values": ["16DP"]},
            "SDP": {"synonyms": ["SDP", "sdp"], "actual_values": ["SDP"]},
        },
    }


def _dataset_keyword_map() -> dict[str, list[str]]:
    return {
        "production": ["\uc0dd\uc0b0", "production", "\uc2e4\uc801", "\ud22c\uc785", "input", "\uc778\ud48b", "\uc0dd\uc0b0\ub7c9"],
        "target": ["\ubaa9\ud45c", "target", "\uacc4\ud68d", "\ubaa9\ud45c\ub7c9"],
        "defect": ["\ubd88\ub7c9", "defect", "\uacb0\ud568"],
        "equipment": ["\uc124\ube44", "\uac00\ub3d9\ub960", "equipment", "downtime"],
        "wip": ["wip", "\uc7ac\uacf5", "\ub300\uae30"],
        "yield": ["\uc218\uc728", "yield", "pass rate", "\ud569\uaca9\ub960", "\uc591\ud488\ub960"],
        "hold": ["hold", "\ud640\ub4dc", "\ubcf4\ub958 lot", "hold lot"],
        "scrap": ["scrap", "\uc2a4\ud06c\ub7a9", "\ud3d0\uae30", "loss cost", "\uc190\uc2e4\ube44\uc6a9"],
        "recipe": ["recipe", "\ub808\uc2dc\ud53c", "\uacf5\uc815 \uc870\uac74", "\uc870\uac74\uac12", "parameter", "\ud30c\ub77c\ubbf8\ud130"],
        "lot_trace": ["lot", "lot trace", "lot \uc774\ub825", "\ucd94\uc801", "traceability", "\ub85c\ud2b8"],
    }


def _custom_registry() -> dict[str, Any]:
    return {
        "entries": [
            {
                "id": "20260401213410268242",
                "title": "WIP HOLD \uc774\uc0c1\uc5ec\ubd80 \uc815\uc758",
                "dataset_keywords": [{"dataset_key": "wip", "keywords": ["wip", "\uc7ac\uacf5"]}],
                "analysis_rules": [
                    {
                        "name": "hold_anomaly_check",
                        "display_name": "HOLD \uc774\uc0c1\uc5ec\ubd80",
                        "synonyms": ["hold_anomaly_check", "HOLD \uc774\uc0c1\uc5ec\ubd80", "\ud640\ub4dc \uccb4\ud06c"],
                        "required_datasets": ["wip"],
                        "required_columns": ["\uc0c1\ud0dc"],
                        "source_columns": [{"dataset_key": "wip", "column": "\uc0c1\ud0dc", "role": "status_field"}],
                        "calculation_mode": "condition_flag",
                        "output_column": "hold_anomaly_flag",
                        "default_group_by": [],
                        "formula": "",
                        "description": "Flag HOLD or REWORK status as anomaly.",
                    }
                ],
            },
            {
                "id": "20260405203508711153",
                "title": "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728 \uc815\uc758",
                "dataset_keywords": [{"dataset_key": "production", "keywords": ["\uc0dd\uc0b0", "\uc0dd\uc0b0\ub7c9"]}, {"dataset_key": "target", "keywords": ["\ubaa9\ud45c", "\ubaa9\ud45c\ub7c9"]}],
                "analysis_rules": [
                    {
                        "name": "plan_gap_rate",
                        "display_name": "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728",
                        "synonyms": ["plan_gap_rate", "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728", "\ubaa9\ud45c \ucc28\uc774\uc728", "\uacc4\ud68d \ucc28\uc774\uc728"],
                        "required_datasets": ["production", "target"],
                        "required_columns": ["production", "target"],
                        "source_columns": [{"dataset_key": "production", "column": "production", "role": "production_value"}, {"dataset_key": "target", "column": "target", "role": "target_value"}],
                        "calculation_mode": "custom_ratio_gap",
                        "output_column": "plan_gap_rate",
                        "default_group_by": ["process_name"],
                        "formula": "(production - target) / target",
                        "description": "Compute the ratio gap between production and target.",
                    }
                ],
                "join_rules": [{"name": "production_target_join", "base_dataset": "production", "join_dataset": "target", "join_type": "left", "join_keys": ["OPER_NAME"]}],
            },
            {
                "id": "20260405203527771918",
                "title": "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218 \uc815\uc758",
                "dataset_keywords": [{"dataset_key": "hold", "keywords": ["\ud640\ub4dc"]}, {"dataset_key": "production", "keywords": ["\uc0dd\uc0b0"]}],
                "analysis_rules": [
                    {
                        "name": "hold_load_index",
                        "display_name": "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218",
                        "synonyms": ["hold_load_index", "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218", "\ubd80\ud558\uc9c0\uc218"],
                        "required_datasets": ["hold", "production"],
                        "required_columns": ["hold_qty", "production"],
                        "source_columns": [{"dataset_key": "hold", "column": "hold_qty", "role": "numerator"}, {"dataset_key": "production", "column": "production", "role": "denominator"}],
                        "calculation_mode": "ratio",
                        "output_column": "hold_load_index",
                        "default_group_by": ["process_name"],
                        "formula": "hold_qty / production",
                        "description": "Compute hold quantity divided by production quantity.",
                    }
                ],
                "join_rules": [{"name": "production_hold_join", "base_dataset": "production", "join_dataset": "hold", "join_type": "left", "join_keys": ["OPER_NAME"]}],
            },
            {
                "id": "20260405203816176733",
                "title": "\uc591\ud488\ub960 \ub370\uc774\ud130\uc14b \ub9e4\ud551 \uc815\uc758",
                "dataset_keywords": [{"dataset_key": "yield", "keywords": ["\uc591\ud488\ub960"]}],
            },
            {
                "id": "20260405203827856128",
                "title": "\ud6c4\uacf5\uc815A \uacf5\uc815 \uadf8\ub8f9 \uc815\uc758",
                "value_groups": [{"field": "process_name", "canonical": "\ud6c4\uacf5\uc815A", "synonyms": ["\ud6c4\uacf5\uc815A"], "values": ["D/A1", "D/A2"], "description": "\ud6c4\uacf5\uc815A \uc138\ubd80 \uacf5\uc815"}],
            },
        ],
        "value_groups": [
            {"field": "process_name", "canonical": "\ud6c4\uacf5\uc815A", "synonyms": ["\ud6c4\uacf5\uc815A"], "values": ["D/A1", "D/A2"], "description": "\ud6c4\uacf5\uc815A \uc138\ubd80 \uacf5\uc815"},
        ],
        "analysis_rules": [
            {
                "name": "hold_anomaly_check",
                "display_name": "HOLD \uc774\uc0c1\uc5ec\ubd80",
                "synonyms": ["hold_anomaly_check", "HOLD \uc774\uc0c1\uc5ec\ubd80", "\ud640\ub4dc \uccb4\ud06c"],
                "required_datasets": ["wip"],
                "required_columns": ["\uc0c1\ud0dc"],
                "source_columns": [{"dataset_key": "wip", "column": "\uc0c1\ud0dc", "role": "status_field"}],
                "calculation_mode": "condition_flag",
                "output_column": "hold_anomaly_flag",
                "default_group_by": [],
                "formula": "",
            },
            {
                "name": "plan_gap_rate",
                "display_name": "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728",
                "synonyms": ["plan_gap_rate", "\uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728", "\ubaa9\ud45c \ucc28\uc774\uc728", "\uacc4\ud68d \ucc28\uc774\uc728"],
                "required_datasets": ["production", "target"],
                "required_columns": ["production", "target"],
                "source_columns": [{"dataset_key": "production", "column": "production", "role": "production_value"}, {"dataset_key": "target", "column": "target", "role": "target_value"}],
                "calculation_mode": "custom_ratio_gap",
                "output_column": "plan_gap_rate",
                "default_group_by": ["process_name"],
                "formula": "(production - target) / target",
            },
            {
                "name": "hold_load_index",
                "display_name": "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218",
                "synonyms": ["hold_load_index", "\ud640\ub4dc \ubd80\ud558\uc9c0\uc218", "\ubd80\ud558\uc9c0\uc218"],
                "required_datasets": ["hold", "production"],
                "required_columns": ["hold_qty", "production"],
                "source_columns": [{"dataset_key": "hold", "column": "hold_qty", "role": "numerator"}, {"dataset_key": "production", "column": "production", "role": "denominator"}],
                "calculation_mode": "ratio",
                "output_column": "hold_load_index",
                "default_group_by": ["process_name"],
                "formula": "hold_qty / production",
            },
        ],
        "join_rules": [
            {"name": "production_target_join", "base_dataset": "production", "join_dataset": "target", "join_type": "left", "join_keys": ["OPER_NAME"]},
            {"name": "production_hold_join", "base_dataset": "production", "join_dataset": "hold", "join_type": "left", "join_keys": ["OPER_NAME"]},
        ],
    }


def build_domain_registry_payload() -> dict[str, Any]:
    return {
        "dataset_metadata": _dataset_metadata(),
        "dataset_keyword_map": _dataset_keyword_map(),
        "process_groups": _process_groups(),
        "attribute_groups": _attribute_groups(),
        "tool_manifest": _tool_manifest(),
        "custom_registry": _custom_registry(),
    }


class PortableManufacturingDomainRegistryJsonComponent(Component):
    display_name = "Portable Manufacturing Domain Registry JSON"
    description = "Expose the embedded manufacturing domain registry as Data/JSON for Prompt Template, LLM, or tool nodes."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Braces"
    name = "portable_manufacturing_domain_registry_json"

    outputs = [
        Output(name="registry_data", display_name="Registry Data", method="registry_data", types=["Data"], selected="Data"),
        Output(name="registry_message", display_name="Registry Message", method="registry_message", types=["Message"], selected="Message"),
    ]

    def _payload(self) -> dict[str, Any]:
        payload = build_domain_registry_payload()
        self.status = "Embedded registry snapshot ready"
        return payload

    def registry_data(self) -> Data:
        return Data(data=self._payload())

    def registry_message(self) -> Message:
        payload = self._payload()
        return Message(text=json.dumps(payload, ensure_ascii=False, indent=2), data=payload)
