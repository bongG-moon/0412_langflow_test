"""Langflow custom component: Finish Manufacturing Result."""

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



class FinishManufacturingResultComponent(Component):
    display_name = "Finish Manufacturing Result"
    description = "Finalize state and expose the result payload for downstream nodes."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "CheckCheck"
    name = "finish_manufacturing_result"

    inputs = [DataInput(name="state", display_name="State", info="State that already contains the final result")]
    outputs = [
        Output(name="finished_state", display_name="Finished State", method="finish_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="result", display_name="Result Payload", method="result_data", group_outputs=True, types=["Data"], selected="Data"),
    ]

    def finish_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from langflow_version.workflow import finish_step

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        finished = finish_step(state)
        self.status = "Final result prepared"
        return make_data({"state": finished})

    def result_data(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from langflow_version.workflow import finish_step

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            return None

        finished = finish_step(state)
        return make_data(finished.get("result", {}))


