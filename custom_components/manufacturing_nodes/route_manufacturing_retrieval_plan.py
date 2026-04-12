"""Langflow custom component: Route Manufacturing Retrieval Plan."""

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



class RouteManufacturingRetrievalPlanComponent(Component):
    display_name = "Route Manufacturing Retrieval Plan"
    description = "Expose finish / single / multi retrieval branches after planning."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitFork"
    name = "route_manufacturing_retrieval_plan"

    inputs = [DataInput(name="state", display_name="State", info="State after dataset planning and job build")]
    outputs = [
        Output(name="finish_state", display_name="Finish State", method="finish_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="single_state", display_name="Single Retrieval State", method="single_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="multi_state", display_name="Multi Retrieval State", method="multi_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _cached: Tuple[Dict[str, Any], str] | None = None

    def _resolve(self) -> Tuple[Dict[str, Any], str]:
        if self._cached is not None:
            return self._cached

        _ensure_repo_root()
        from langflow_version.component_base import read_state_payload
        from manufacturing_agent.graph.builder import route_after_retrieval_plan

        state = read_state_payload(getattr(self, "state", None))
        route = route_after_retrieval_plan(state) if state else ""
        self.status = f"Retrieval route: {route or 'inactive'}"
        self._cached = (state, route)
        return self._cached

    def finish_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "finish", {"state": state})

    def single_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "single_retrieval", {"state": state})

    def multi_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "multi_retrieval", {"state": state})

