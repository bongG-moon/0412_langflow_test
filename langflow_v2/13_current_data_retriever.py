from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


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
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _rows_columns(rows: list[Dict[str, Any]]) -> list[str]:
    return [str(key) for key in rows[0].keys()] if rows and isinstance(rows[0], dict) else []


def _build_current_datasets(source_results: list[Dict[str, Any]]) -> Dict[str, Any]:
    current: Dict[str, Any] = {}
    for result in source_results:
        dataset_key = str(result.get("dataset_key") or result.get("tool_name") or "current_data")
        rows = [row for row in result.get("data", []) if isinstance(row, dict)] if isinstance(result.get("data"), list) else []
        data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
        current[dataset_key] = {
            "success": bool(result.get("success")),
            "summary": result.get("summary", ""),
            "row_count": result.get("row_count") or data_ref.get("row_count") or len(rows),
            "columns": _rows_columns(rows) or data_ref.get("columns", []),
        }
    return current


def _source_result_from_current_data(current_data: Dict[str, Any]) -> Dict[str, Any]:
    rows = [row for row in current_data.get("data", []) if isinstance(row, dict)] if isinstance(current_data.get("data"), list) else []
    dataset_keys = current_data.get("source_dataset_keys") if isinstance(current_data.get("source_dataset_keys"), list) else []
    result = {
        "success": True,
        "tool_name": current_data.get("tool_name") or current_data.get("original_tool_name") or "current_data",
        "dataset_key": dataset_keys[0] if dataset_keys else current_data.get("dataset_key", "current_data"),
        "dataset_label": current_data.get("dataset_label", "Current Data"),
        "data": deepcopy(rows),
        "row_count": current_data.get("row_count") or len(rows),
        "summary": current_data.get("summary", f"current data {len(rows)} rows reused"),
        "applied_params": deepcopy(current_data.get("source_required_params", current_data.get("retrieval_applied_params", {}))),
        "applied_filters": deepcopy(current_data.get("source_filters", {})),
        "applied_column_filters": deepcopy(current_data.get("source_column_filters", {})),
        "reused_current_data": True,
    }
    if isinstance(current_data.get("data_ref"), dict):
        result["data_ref"] = deepcopy(current_data["data_ref"])
        result["data_is_reference"] = True
    return result


def retrieve_current_data(intent_plan_value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(intent_plan_value)
    plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    if payload.get("skipped"):
        return {
            "retrieval_payload": {
                "skipped": True,
                "skip_reason": payload.get("skip_reason", "route skipped"),
                "route": "followup_transform",
                "intent_plan": plan,
                "state": state,
                "source_results": [],
            }
        }

    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    if not current_data:
        source_results = [{
            "success": False,
            "tool_name": "current_data",
            "dataset_key": "current_data",
            "data": [],
            "summary": "",
            "error_message": "No current_data is available for follow-up analysis.",
            "failure_type": "missing_current_data",
        }]
    else:
        source_results = [_source_result_from_current_data(current_data)]

    return {
        "retrieval_payload": {
            "route": "followup_transform",
            "source_results": source_results,
            "current_datasets": _build_current_datasets(source_results),
            "source_snapshots": deepcopy(current_data.get("source_snapshots", [])) if isinstance(current_data, dict) else [],
            "intent_plan": plan,
            "state": state,
            "used_current_data": True,
        },
        "intent_plan": plan,
        "state": state,
    }


class CurrentDataRetriever(Component):
    display_name = "Current Data Retriever"
    description = "Reuse state.current_data for visible follow-up transform branches."
    icon = "History"
    name = "CurrentDataRetriever"

    inputs = [
        DataInput(name="intent_plan", display_name="Follow-up Intent Plan", info="Output from Intent Route Router.followup_transform.", input_types=["Data", "JSON"])
    ]
    outputs = [Output(name="retrieval_payload", display_name="Retrieval Payload", method="build_payload", types=["Data"])]

    def build_payload(self):
        payload = retrieve_current_data(getattr(self, "intent_plan", None))
        retrieval = payload.get("retrieval_payload", {})
        source_results = retrieval.get("source_results", []) if isinstance(retrieval.get("source_results"), list) else []
        self.status = {"route": retrieval.get("route"), "source_count": len(source_results), "skipped": retrieval.get("skipped", False)}
        return _make_data(payload)

