"""Langflow custom component: Merge Final Manufacturing Result."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output


def _ensure_repo_root() -> Path:
    def _is_repo_root(path: Path) -> bool:
        return (path / "langflow_version").is_dir() and (path / "manufacturing_agent").is_dir()

    candidates: list[Path] = []

    explicit_root = os.environ.get("MANUFACTURING_AGENT_PROJECT_ROOT")
    if explicit_root:
        candidates.append(Path(explicit_root).expanduser())

    components_path = os.environ.get("LANGFLOW_COMPONENTS_PATH")
    if components_path:
        candidates.append(Path(components_path).expanduser().resolve().parent)

    cwd = Path.cwd().resolve()
    candidates.append(cwd)
    candidates.extend(cwd.parents)

    for candidate in candidates:
        candidate = candidate.resolve()
        if not _is_repo_root(candidate):
            continue
        candidate_text = str(candidate)
        if candidate_text not in sys.path:
            sys.path.insert(0, candidate_text)
        return candidate

    raise ModuleNotFoundError(
        "Could not locate the project root for custom components. "
        "Set MANUFACTURING_AGENT_PROJECT_ROOT or LANGFLOW_COMPONENTS_PATH."
    )


class MergeFinalManufacturingResultComponent(Component):
    display_name = "Merge Final Manufacturing Result"
    description = "Merge the visible branch outputs into one final result payload."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitMerge"
    name = "merge_final_manufacturing_result"

    inputs = [
        DataInput(name="followup_result", display_name="Followup Result", info="Result payload from the follow-up branch"),
        DataInput(name="finish_result", display_name="Early Finish Result", info="Result payload from the planning finish branch"),
        DataInput(name="single_direct_result", display_name="Single Direct Result", info="Result payload from the single direct-response branch"),
        DataInput(name="single_analysis_result", display_name="Single Analysis Result", info="Result payload from the single post-analysis branch"),
        DataInput(name="multi_overview_result", display_name="Multi Overview Result", info="Result payload from the multi overview branch"),
        DataInput(name="multi_analysis_result", display_name="Multi Analysis Result", info="Result payload from the multi post-analysis branch"),
    ]
    outputs = [
        Output(name="merged_result", display_name="Merged Result", method="merged_result", types=["Data"], selected="Data"),
    ]

    _cached: Tuple[Dict[str, Any], str] | None = None

    @staticmethod
    def _unwrap_result_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        if "response" in payload or "tool_results" in payload or "current_data" in payload:
            return payload

        nested_result = payload.get("result")
        if isinstance(nested_result, dict):
            return nested_result

        state = payload.get("state")
        if isinstance(state, dict):
            nested_state_result = state.get("result")
            if isinstance(nested_state_result, dict):
                return nested_state_result

        return {}

    def _resolve(self) -> Tuple[Dict[str, Any], str]:
        if self._cached is not None:
            return self._cached

        _ensure_repo_root()
        from langflow_version.component_base import read_data_payload

        candidates = [
            ("followup_result", "followup", getattr(self, "followup_result", None)),
            ("finish_result", "early_finish", getattr(self, "finish_result", None)),
            ("single_direct_result", "single_direct", getattr(self, "single_direct_result", None)),
            ("single_analysis_result", "single_analysis", getattr(self, "single_analysis_result", None)),
            ("multi_overview_result", "multi_overview", getattr(self, "multi_overview_result", None)),
            ("multi_analysis_result", "multi_analysis", getattr(self, "multi_analysis_result", None)),
        ]

        for input_name, branch_name, raw_value in candidates:
            payload = self._unwrap_result_payload(read_data_payload(raw_value))
            if not payload:
                continue
            if not any(key in payload for key in ("response", "tool_results", "current_data", "failure_type")):
                continue
            payload = {**payload, "merged_from_branch": branch_name, "merged_from_input": input_name}
            self.status = f"Merged branch: {branch_name}"
            self._cached = (payload, branch_name)
            return self._cached

        self.status = "No active final branch"
        self._cached = ({}, "")
        return self._cached

    def merged_result(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data

        payload, _ = self._resolve()
        if not payload:
            return None
        return make_data(payload)
