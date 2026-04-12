"""Langflow custom component: Execute Manufacturing Jobs."""

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



class ExecuteManufacturingJobsComponent(Component):
    display_name = "Execute Manufacturing Jobs"
    description = "Run prepared retrieval jobs and attach normalized source results to state."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Play"
    name = "execute_manufacturing_jobs"

    inputs = [DataInput(name="state", display_name="State", info="State with retrieval_jobs")]
    outputs = [Output(name="state_with_source_results", display_name="State With Source Results", method="execute_jobs", types=["Data"], selected="Data")]

    def execute_jobs(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.services.runtime_service import prepare_retrieval_source_results

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        jobs = state.get("retrieval_jobs", [])
        if not jobs:
            self.status = "No retrieval jobs; forwarding state"
            return make_data({"state": state})

        prepared = prepare_retrieval_source_results(jobs)
        updated_state = {
            **state,
            "source_results": prepared["source_results"],
            "current_datasets": prepared["current_datasets"],
        }
        self.status = f"Executed {len(prepared['source_results'])} retrieval result(s)"
        return make_data({"state": updated_state})


