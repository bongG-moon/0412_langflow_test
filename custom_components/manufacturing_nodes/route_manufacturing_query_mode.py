"""Langflow custom component: Route Manufacturing Query Mode."""

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



class RouteManufacturingQueryModeComponent(Component):
    display_name = "Route Manufacturing Query Mode"
    description = "Expose the LangGraph query-mode branch as visible Langflow output ports."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitFork"
    name = "route_manufacturing_query_mode"

    inputs = [DataInput(name="state", display_name="State", info="State with query_mode already decided")]
    outputs = [
        Output(name="followup_state", display_name="Followup State", method="followup_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="retrieval_state", display_name="Retrieval State", method="retrieval_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _cached: Tuple[Dict[str, Any], str] | None = None

    def _resolve(self) -> Tuple[Dict[str, Any], str]:
        if self._cached is not None:
            return self._cached

        _ensure_repo_root()
        from langflow_version.component_base import read_state_payload
        from manufacturing_agent.graph.builder import route_after_resolve

        state = read_state_payload(getattr(self, "state", None))
        route = route_after_resolve(state) if state else ""
        self.status = f"Query route: {route or 'inactive'}"
        self._cached = (state, route)
        return self._cached

    def followup_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "followup_analysis", {"state": state})

    def retrieval_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_branch_data

        state, route = self._resolve()
        return make_branch_data(route == "plan_retrieval", {"state": state})


