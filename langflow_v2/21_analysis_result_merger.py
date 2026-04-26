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


def _analysis_result(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("analysis_result") if isinstance(payload.get("analysis_result"), dict) else payload


def merge_analysis_results(early_result_value: Any = None, direct_result_value: Any = None, pandas_result_value: Any = None) -> Dict[str, Any]:
    candidates = [
        ("early_result", _analysis_result(early_result_value)),
        ("direct_result", _analysis_result(direct_result_value)),
        ("pandas_result", _analysis_result(pandas_result_value)),
    ]
    skipped = []
    for source, result in candidates:
        if not isinstance(result, dict) or not result:
            continue
        if result.get("skipped"):
            skipped.append({"source": source, "skip_reason": result.get("skip_reason", "")})
            continue
        merged = deepcopy(result)
        merged["merged_from"] = source
        if skipped:
            merged["skipped_branches"] = skipped
        return {"analysis_result": merged}
    return {
        "analysis_result": {
            "success": False,
            "tool_name": "analysis_result_merger",
            "data": [],
            "summary": "No active branch produced an analysis result.",
            "error_message": "No active branch produced an analysis result.",
            "analysis_logic": "merge_no_active_branch",
            "skipped_branches": skipped,
            "awaiting_analysis_choice": False,
        }
    }


class AnalysisResultMerger(Component):
    display_name = "Analysis Result Merger"
    description = "Merge early, direct, and pandas branch outputs before the final answer node."
    icon = "Merge"
    name = "AnalysisResultMerger"

    inputs = [
        DataInput(name="early_result", display_name="Early Result", info="Output from Early Result Adapter.", input_types=["Data", "JSON"]),
        DataInput(name="direct_result", display_name="Direct Result", info="Output from Direct Result Adapter.", input_types=["Data", "JSON"]),
        DataInput(name="pandas_result", display_name="Pandas Result", info="Output from Pandas Analysis Executor.", input_types=["Data", "JSON"]),
    ]
    outputs = [Output(name="analysis_result", display_name="Analysis Result", method="build_result", types=["Data"])]

    def build_result(self):
        payload = merge_analysis_results(getattr(self, "early_result", None), getattr(self, "direct_result", None), getattr(self, "pandas_result", None))
        result = payload.get("analysis_result", {})
        self.status = {"merged_from": result.get("merged_from"), "logic": result.get("analysis_logic"), "success": result.get("success")}
        return _make_data(payload)

