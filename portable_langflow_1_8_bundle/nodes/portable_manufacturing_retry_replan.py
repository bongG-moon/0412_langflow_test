"""Portable Langflow node: rebuild retrieval jobs after sufficiency review indicates missing datasets."""

from __future__ import annotations

from datetime import datetime, timedelta
import re
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


def _extract_date_slices(text: str, default_date: str | None) -> list[dict[str, str]]:
    lowered = str(text or "").lower()
    now = datetime.now()
    slices: list[dict[str, str]] = []
    if "어제" in str(text or "") or "yesterday" in lowered:
        slices.append({"label": "어제", "date": (now - timedelta(days=1)).strftime("%Y-%m-%d")})
    if "오늘" in str(text or "") or "today" in lowered:
        slices.append({"label": "오늘", "date": now.strftime("%Y-%m-%d")})
    for year, month, day in re.findall(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?(0[1-9]|[12]\d|3[01])", str(text or "")):
        value = f"{year}-{month}-{day}"
        if value not in [item["date"] for item in slices]:
            slices.append({"label": value, "date": value})
    if not slices and default_date:
        slices.append({"label": default_date, "date": default_date})
    return slices


class PortableManufacturingRetryReplanComponent(Component):
    display_name = "Portable Manufacturing Retry Replan"
    description = "Merge missing dataset keys and rebuild retrieval jobs for a retry run."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "RotateCcw"
    name = "portable_manufacturing_retry_replan"

    inputs = [
        DataInput(name="state", display_name="State", info="Retry state from Portable Manufacturing Sufficiency Parser"),
    ]

    outputs = [
        Output(name="replanned_state", display_name="Replanned State", method="replanned_state", types=["Data"], selected="Data"),
    ]

    def replanned_state(self) -> Data | None:
        state = _as_payload(getattr(self, "state", None))
        review = state.get("sufficiency_review") if isinstance(state.get("sufficiency_review"), dict) else {}
        if not review.get("missing_dataset_keys"):
            self.status = "No retry datasets"
            return None

        retry_count = int(state.get("retry_count") or 0)
        merged_dataset_keys = []
        existing = (state.get("retrieval_plan") or {}).get("dataset_keys", [])
        for item in [*existing, *(review.get("missing_dataset_keys") or [])]:
            if item not in merged_dataset_keys:
                merged_dataset_keys.append(item)

        extracted_params = state.get("extracted_params") if isinstance(state.get("extracted_params"), dict) else {}
        date_slices = _extract_date_slices(str(state.get("user_input") or ""), str(extracted_params.get("date") or ""))
        retrieval_jobs = []
        if len(merged_dataset_keys) == 1 and len(date_slices) > 1:
            for date_slice in date_slices:
                job_params = dict(extracted_params)
                job_params["date"] = date_slice["date"]
                retrieval_jobs.append({"dataset_key": merged_dataset_keys[0], "params": job_params, "result_label": date_slice["label"]})
        else:
            for dataset_key in merged_dataset_keys:
                job_params = dict(extracted_params)
                if len(date_slices) == 1:
                    job_params["date"] = date_slices[0]["date"]
                retrieval_jobs.append({"dataset_key": dataset_key, "params": job_params, "result_label": None})

        updated_state = {
            **state,
            "retry_count": retry_count + 1,
            "selected_dataset_keys": merged_dataset_keys,
            "retrieval_plan": {
                **(state.get("retrieval_plan") if isinstance(state.get("retrieval_plan"), dict) else {}),
                "dataset_keys": merged_dataset_keys,
                "needs_post_processing": True,
            },
            "retrieval_jobs": retrieval_jobs,
        }
        self.status = f"Retry re-plan #{retry_count + 1}"
        return Data(data=updated_state)
