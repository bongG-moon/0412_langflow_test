"""Langflow custom component: Run Manufacturing Followup."""

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



class RunManufacturingFollowupComponent(Component):
    display_name = "Run Manufacturing Followup"
    description = "Execute only the follow-up analysis path on current_data."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "RefreshCw"
    name = "run_manufacturing_followup"

    inputs = [DataInput(name="state", display_name="State", info="State with current_data and extracted_params")]
    outputs = [Output(name="followup_state", display_name="Followup State", method="run_followup", types=["Data"], selected="Data")]

    def run_followup(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.services.runtime_service import run_followup_analysis

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        result = run_followup_analysis(
            user_input=state.get("user_input", ""),
            chat_history=state.get("chat_history", []),
            current_data=state.get("current_data", {}),
            extracted_params=state.get("extracted_params", {}),
        )
        updated_state = {**state, "result": result}
        self.status = "Follow-up analysis complete"
        return make_data({"state": updated_state})


