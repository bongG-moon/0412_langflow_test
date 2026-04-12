"""Langflow custom component: Run Manufacturing Branch."""

from __future__ import annotations

import os
import sys
from pathlib import Path


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
from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output



class RunWorkflowBranchComponent(Component):
    display_name = "Run Manufacturing Branch"
    description = "Run the next internal branch from the current manufacturing state."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitBranch"
    name = "run_manufacturing_branch"

    inputs = [DataInput(name="state", display_name="State", info="State after request resolution or retrieval planning")]
    outputs = [Output(name="updated_state", display_name="Updated State", method="run_branch", types=["Data"], selected="Data")]

    def run_branch(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from langflow_version.workflow import run_next_branch

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        updated = run_next_branch(state)
        has_result = bool(updated.get("result"))
        self.status = "Branch execution complete" if has_result else "Branch execution complete; awaiting next step"
        return make_data({"state": updated})


