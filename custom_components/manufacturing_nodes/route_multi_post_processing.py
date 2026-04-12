"""Langflow custom component: Route Multi Post Processing."""

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



class RouteMultiPostProcessingComponent(Component):
    display_name = "Route Multi Post Processing"
    description = "Expose overview vs post-analysis branch for multi retrieval results."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitFork"
    name = "route_multi_post_processing"

    inputs = [DataInput(name="state", display_name="State", info="Multi retrieval state after execute_jobs")]
    outputs = [
        Output(name="overview_state", display_name="Overview Response State", method="overview_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="post_analysis_state", display_name="Post Analysis State", method="post_analysis_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _cached: Tuple[Dict[str, Any], str] | None = None

    def _resolve(self) -> Tuple[Dict[str, Any], str]:
        if self._cached is not None:
            return self._cached

        _ensure_repo_root()
        from langflow_version.component_base import read_state_payload
        from manufacturing_agent.services.runtime_service import route_multi_post_processing

        state = read_state_payload(getattr(self, "state", None))
        jobs = state.get("retrieval_jobs", []) if state else []
        extracted_params = jobs[0]["params"] if jobs else state.get("extracted_params", {}) if state else {}
        route = (
            route_multi_post_processing(
                user_input=state.get("user_input", ""),
                source_results=state.get("source_results", []),
                extracted_params=extracted_params,
                retrieval_plan=state.get("retrieval_plan"),
            )
            if state
            else ""
        )
        self.status = f"Multi post-processing route: {route or 'inactive'}"
        self._cached = (state, route)
        return self._cached

    def overview_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "overview_response", {"state": state})

    def post_analysis_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "post_analysis", {"state": state})


