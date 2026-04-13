"""Portable Langflow node: determine dataset jobs or early finish."""

from __future__ import annotations

from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


class PortableManufacturingRetrievalPlannerComponent(Component):
    display_name = "Portable Manufacturing Retrieval Planner"
    description = "Build retrieval jobs and early finish conditions for manufacturing queries."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "ListTree"
    name = "portable_manufacturing_retrieval_planner"

    inputs = [
        DataInput(name="state", display_name="State", info="Retrieval state from Portable Manufacturing Request Router"),
    ]

    outputs = [
        Output(name="finish_result", display_name="Finish Result", method="finish_result", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="jobs_state", display_name="Jobs State", method="jobs_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _cached_finish: dict[str, Any] | None = None
    _cached_jobs_state: dict[str, Any] | None = None

    def _resolve(self) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if self._cached_finish is not None or self._cached_jobs_state is not None:
            return self._cached_finish, self._cached_jobs_state

        state = _as_payload(getattr(self, "state", None))
        params = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
        metric_intent = str(params.get("metric_intent") or "production")

        if metric_intent == "defect_rate":
            dataset_keys = ["production", "defect"]
        elif metric_intent == "achievement_rate":
            dataset_keys = ["production", "target"]
        elif metric_intent == "wip":
            dataset_keys = ["production", "wip"]
        elif metric_intent == "equipment":
            dataset_keys = ["equipment"]
        elif metric_intent == "defect":
            dataset_keys = ["defect"]
        elif metric_intent == "target":
            dataset_keys = ["target"]
        else:
            dataset_keys = ["production"]

        date_value = str(params.get("date") or "").strip()
        needs_date = any(key in dataset_keys for key in ["production", "defect", "target", "wip"])
        if needs_date and not date_value:
            self._cached_finish = {
                "response": "조회 기준 날짜가 필요합니다. 예: 오늘, 어제, 2026-04-12",
                "tool_results": [],
                "current_data": state.get("current_data"),
                "extracted_params": params,
                "failure_type": "missing_date",
                "awaiting_analysis_choice": False,
            }
            self._cached_jobs_state = None
            self.status = "Missing date"
            return self._cached_finish, self._cached_jobs_state

        retrieval_jobs = [
            {
                "dataset_key": dataset_key,
                "date": date_value,
                "process_names": params.get("process_names") or [],
            }
            for dataset_key in dataset_keys
        ]

        retrieval_plan = {
            "dataset_keys": dataset_keys,
            "analysis_goal": metric_intent,
            "needs_post_processing": len(dataset_keys) > 1 or bool(params.get("group_by")) or bool(params.get("top_n")) or bool(params.get("needs_post_processing")),
        }

        jobs_state = {
            **state,
            "retrieval_plan": retrieval_plan,
            "retrieval_jobs": retrieval_jobs,
        }
        self._cached_finish = None
        self._cached_jobs_state = jobs_state
        self.status = f"Built {len(retrieval_jobs)} jobs"
        return self._cached_finish, self._cached_jobs_state

    def finish_result(self) -> Data | None:
        finish_payload, _ = self._resolve()
        return Data(data=finish_payload) if finish_payload else None

    def jobs_state(self) -> Data | None:
        _, jobs_state = self._resolve()
        return Data(data=jobs_state) if jobs_state else None
