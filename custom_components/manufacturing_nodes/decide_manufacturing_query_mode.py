"""Langflow custom component: Decide Manufacturing Query Mode."""

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



class DecideManufacturingQueryModeComponent(Component):
    display_name = "Decide Manufacturing Query Mode"
    description = "Decide whether the question is a new retrieval or a follow-up transformation."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitCompareArrows"
    name = "decide_manufacturing_query_mode"

    inputs = [DataInput(name="state", display_name="State", info="State with extracted parameters")]
    outputs = [Output(name="state_with_mode", display_name="State With Mode", method="decide_mode", types=["Data"], selected="Data")]

    def decide_mode(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.services.query_mode import choose_query_mode

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        query_mode = choose_query_mode(
            state.get("user_input", ""),
            state.get("current_data"),
            state.get("extracted_params", {}),
        )
        updated_state = {**state, "query_mode": query_mode}
        self.status = f"Query mode decided: {query_mode}"
        return make_data({"state": updated_state})


