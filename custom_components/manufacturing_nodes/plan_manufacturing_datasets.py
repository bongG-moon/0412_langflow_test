"""Langflow custom component: Plan Manufacturing Datasets."""

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



class PlanManufacturingDatasetsComponent(Component):
    display_name = "Plan Manufacturing Datasets"
    description = "Select which manufacturing datasets are needed for the current question."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "TableProperties"
    name = "plan_manufacturing_datasets"

    inputs = [DataInput(name="state", display_name="State", info="State after query mode has been decided")]
    outputs = [Output(name="state_with_plan", display_name="State With Plan", method="plan_datasets", types=["Data"], selected="Data")]

    def plan_datasets(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.data.retrieval import pick_retrieval_tools
        from manufacturing_agent.services.retrieval_planner import plan_retrieval_request

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        retrieval_plan = plan_retrieval_request(
            state.get("user_input", ""),
            state.get("chat_history", []),
            state.get("current_data"),
        )
        retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(state.get("user_input", ""))
        updated_state = {
            **state,
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": retrieval_keys,
        }
        self.status = f"Planned {len(retrieval_keys)} dataset key(s)"
        return make_data({"state": updated_state})


