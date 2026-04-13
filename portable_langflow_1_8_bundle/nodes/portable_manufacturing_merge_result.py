"""Portable Langflow node: merge branch outputs into one final payload."""

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


class PortableManufacturingMergeResultComponent(Component):
    display_name = "Portable Manufacturing Merge Result"
    description = "Select the active result payload from follow-up, finish, or retrieval branches."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitMerge"
    name = "portable_manufacturing_merge_result"

    inputs = [
        DataInput(name="followup_result", display_name="Followup Result"),
        DataInput(name="finish_result", display_name="Finish Result"),
        DataInput(name="retrieval_result", display_name="Retrieval Result"),
        DataInput(name="retry_result", display_name="Retry Result"),
    ]

    outputs = [
        Output(name="merged_result", display_name="Merged Result", method="merged_result", types=["Data"], selected="Data"),
    ]

    def merged_result(self) -> Data | None:
        candidates = [
            ("followup", _as_payload(getattr(self, "followup_result", None))),
            ("finish", _as_payload(getattr(self, "finish_result", None))),
            ("retry", _as_payload(getattr(self, "retry_result", None))),
            ("retrieval", _as_payload(getattr(self, "retrieval_result", None))),
        ]
        for branch_name, payload in candidates:
            if not payload:
                continue
            if not any(key in payload for key in ("response", "failure_type", "current_data")):
                continue
            merged = {**payload, "merged_from_branch": branch_name}
            self.status = f"Merged {branch_name} branch"
            return Data(data=merged)
        self.status = "No active result"
        return None
