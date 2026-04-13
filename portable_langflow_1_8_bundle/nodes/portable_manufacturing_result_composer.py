"""Portable Langflow node: compose follow-up or retrieval result payloads."""

from __future__ import annotations

from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


def _numeric_keys(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    keys: list[str] = []
    for key in rows[0]:
        if key == "date":
            continue
        if all(isinstance(row.get(key), (int, float)) for row in rows if key in row):
            keys.append(key)
    return keys


def _primary_numeric_key(rows: list[dict[str, Any]]) -> str:
    preferred = [
        "achievement_rate",
        "defect_rate",
        "quantity",
        "target_qty",
        "defect_qty",
        "wip_qty",
        "uptime_pct",
        "alarm_minutes",
    ]
    numeric_keys = _numeric_keys(rows)
    for key in preferred:
        if key in numeric_keys:
            return key
    return numeric_keys[0] if numeric_keys else ""


def _trim_rows(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return rows[:limit]


def _tabular_payload(rows: list[dict[str, Any]], title: str) -> dict[str, Any]:
    columns = list(rows[0].keys()) if rows else []
    return {"title": title, "columns": columns, "rows": rows}


def _aggregate_rows(rows: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    if not group_by:
        return rows
    numeric_keys = _numeric_keys(rows)
    bucket: dict[str, dict[str, Any]] = {}
    for row in rows:
        group_value = str(row.get(group_by) or "unknown")
        current = bucket.setdefault(group_value, {group_by: group_value})
        for numeric_key in numeric_keys:
            current[numeric_key] = round(float(current.get(numeric_key, 0)) + float(row.get(numeric_key, 0)), 2)
    return list(bucket.values())


def _sort_and_limit(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    metric_key = _primary_numeric_key(rows)
    sorted_rows = sorted(rows, key=lambda item: float(item.get(metric_key, 0) or 0), reverse=True) if metric_key else rows
    return sorted_rows[:top_n] if top_n else sorted_rows


def _join_metric_rows(production_rows: list[dict[str, Any]], secondary_rows: list[dict[str, Any]], secondary_key: str, output_key: str) -> list[dict[str, Any]]:
    index: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in secondary_rows:
        index[(row["date"], row["process_name"], row["line_name"], row["product_name"])] = row

    joined: list[dict[str, Any]] = []
    for row in production_rows:
        match = index.get((row["date"], row["process_name"], row["line_name"], row["product_name"]), {})
        quantity = float(row.get("quantity", 0) or 0)
        secondary_value = float(match.get(secondary_key, 0) or 0)
        new_row = dict(row)
        new_row[secondary_key] = secondary_value
        if output_key == "achievement_rate":
            new_row[output_key] = round((quantity / secondary_value) * 100, 2) if secondary_value else 0.0
        elif output_key == "defect_rate":
            new_row[output_key] = round((secondary_value / quantity) * 100, 2) if quantity else 0.0
        elif output_key == "wip_to_output":
            new_row[output_key] = round((secondary_value / quantity) * 100, 2) if quantity else 0.0
        joined.append(new_row)
    return joined


class PortableManufacturingResultComposerComponent(Component):
    display_name = "Portable Manufacturing Result Composer"
    description = "Build final manufacturing result payloads for follow-up or retrieval branches."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "FileOutput"
    name = "portable_manufacturing_result_composer"

    inputs = [
        DataInput(name="state", display_name="State", info="Follow-up state or executed retrieval state"),
    ]

    outputs = [
        Output(name="result_data", display_name="Result Data", method="result_data", types=["Data"], selected="Data"),
        Output(name="response_message", display_name="Response Message", method="response_message", types=["Message"], selected="Message"),
    ]

    _cached_result: dict[str, Any] | None = None

    def _compose(self) -> dict[str, Any]:
        if self._cached_result is not None:
            return self._cached_result

        state = _as_payload(getattr(self, "state", None))
        query_mode = str(state.get("query_mode") or "retrieval")
        params = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else None

        if query_mode == "followup":
            rows = list(current_data.get("rows") or []) if current_data else []
            if not rows:
                result = {
                    "response": "이전 조회 결과가 없어 후속 변환을 진행할 수 없습니다. 먼저 데이터를 조회해 주세요.",
                    "tool_results": [],
                    "current_data": current_data,
                    "extracted_params": params,
                    "failure_type": "missing_current_data",
                    "awaiting_analysis_choice": False,
                }
                self._cached_result = result
                self.status = "Missing current_data"
                return result

            grouped = _aggregate_rows(rows, str(params.get("group_by") or ""))
            transformed = _sort_and_limit(grouped, int(params.get("top_n") or 0))
            metric_key = _primary_numeric_key(transformed)
            summary = f"후속 분석 결과입니다. {len(transformed)}건을 반환했습니다."
            if metric_key:
                total_value = round(sum(float(row.get(metric_key, 0) or 0) for row in transformed), 2)
                summary += f" 주요 지표 `{metric_key}` 합계는 {total_value}입니다."

            result = {
                "response": summary,
                "tool_results": state.get("tool_results", []),
                "current_data": _tabular_payload(_trim_rows(transformed), "followup_result"),
                "extracted_params": params,
                "awaiting_analysis_choice": False,
            }
            self._cached_result = result
            self.status = "Follow-up result composed"
            return result

        source_results = state.get("source_results") if isinstance(state.get("source_results"), dict) else {}
        plan = state.get("retrieval_plan") if isinstance(state.get("retrieval_plan"), dict) else {}
        dataset_keys = plan.get("dataset_keys") if isinstance(plan.get("dataset_keys"), list) else []

        if not source_results:
            result = {
                "response": "조회 결과가 비어 있습니다.",
                "tool_results": state.get("tool_results", []),
                "current_data": current_data,
                "extracted_params": params,
                "failure_type": "missing_source_results",
                "awaiting_analysis_choice": False,
            }
            self._cached_result = result
            self.status = "No source results"
            return result

        if dataset_keys == ["production"]:
            rows = list(source_results.get("production") or [])
            grouped = _aggregate_rows(rows, str(params.get("group_by") or ""))
            transformed = _sort_and_limit(grouped, int(params.get("top_n") or 0))
            total_quantity = int(sum(float(row.get("quantity", 0) or 0) for row in transformed))
            response = f"{params.get('date') or '지정일'} 기준 생산 조회 결과입니다. 총 {len(transformed)}건, 생산량 합계는 {total_quantity}입니다."
            result_rows = _trim_rows(transformed)
        elif dataset_keys == ["defect"]:
            rows = list(source_results.get("defect") or [])
            grouped = _aggregate_rows(rows, str(params.get("group_by") or ""))
            transformed = _sort_and_limit(grouped, int(params.get("top_n") or 0))
            total_defect = int(sum(float(row.get("defect_qty", 0) or 0) for row in transformed))
            response = f"{params.get('date') or '지정일'} 기준 불량 조회 결과입니다. 총 {len(transformed)}건, 불량 수량 합계는 {total_defect}입니다."
            result_rows = _trim_rows(transformed)
        elif dataset_keys == ["target"]:
            rows = list(source_results.get("target") or [])
            grouped = _aggregate_rows(rows, str(params.get("group_by") or ""))
            transformed = _sort_and_limit(grouped, int(params.get("top_n") or 0))
            total_target = int(sum(float(row.get("target_qty", 0) or 0) for row in transformed))
            response = f"{params.get('date') or '지정일'} 기준 목표 조회 결과입니다. 총 {len(transformed)}건, 목표 수량 합계는 {total_target}입니다."
            result_rows = _trim_rows(transformed)
        elif dataset_keys == ["equipment"]:
            rows = list(source_results.get("equipment") or [])
            grouped = _aggregate_rows(rows, str(params.get("group_by") or ""))
            transformed = _sort_and_limit(grouped, int(params.get("top_n") or 0))
            avg_uptime = round(sum(float(row.get("uptime_pct", 0) or 0) for row in transformed) / max(len(transformed), 1), 2)
            response = f"설비 조회 결과입니다. 총 {len(transformed)}건이며 평균 가동률은 {avg_uptime}% 입니다."
            result_rows = _trim_rows(transformed)
        else:
            production_rows = list(source_results.get("production") or [])
            if "target" in dataset_keys:
                joined = _join_metric_rows(production_rows, list(source_results.get("target") or []), "target_qty", "achievement_rate")
                metric_label = "달성률"
                metric_key = "achievement_rate"
            elif "defect" in dataset_keys:
                joined = _join_metric_rows(production_rows, list(source_results.get("defect") or []), "defect_qty", "defect_rate")
                metric_label = "불량률"
                metric_key = "defect_rate"
            else:
                joined = _join_metric_rows(production_rows, list(source_results.get("wip") or []), "wip_qty", "wip_to_output")
                metric_label = "WIP 대비율"
                metric_key = "wip_to_output"

            grouped = _aggregate_rows(joined, str(params.get("group_by") or ""))
            transformed = _sort_and_limit(grouped, int(params.get("top_n") or 0))
            avg_metric = round(sum(float(row.get(metric_key, 0) or 0) for row in transformed) / max(len(transformed), 1), 2)
            response = f"{params.get('date') or '지정일'} 기준 {metric_label} 분석 결과입니다. 총 {len(transformed)}건이며 평균 {metric_label}은 {avg_metric} 입니다."
            result_rows = _trim_rows(transformed)

        result = {
            "response": response,
            "tool_results": state.get("tool_results", []),
            "current_data": _tabular_payload(result_rows, "manufacturing_result"),
            "extracted_params": params,
            "awaiting_analysis_choice": False,
        }
        self._cached_result = result
        self.status = "Retrieval result composed"
        return result

    def result_data(self) -> Data:
        return Data(data=self._compose())

    def response_message(self) -> Message:
        payload = self._compose()
        session_id = str(_as_payload(getattr(self, "state", None)).get("session_id") or "")
        return Message(text=str(payload.get("response") or ""), data=payload, session_id=session_id)
