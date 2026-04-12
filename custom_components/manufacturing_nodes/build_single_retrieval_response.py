"""Langflow custom component: Build Single Retrieval Response."""

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



class BuildSingleRetrievalResponseComponent(Component):
    display_name = "Build Single Retrieval Response"
    description = "Create the direct final response for a single retrieval path without post analysis."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "MessageSquareText"
    name = "build_single_retrieval_response"

    inputs = [DataInput(name="state", display_name="State", info="Single retrieval state after execute_jobs")]
    outputs = [Output(name="response_state", display_name="Response State", method="build_response", types=["Data"], selected="Data")]

    def build_response(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.services.runtime_service import build_single_retrieval_response

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        jobs = state.get("retrieval_jobs", [])
        extracted_params = jobs[0]["params"] if jobs else state.get("extracted_params", {})
        result = build_single_retrieval_response(
            user_input=state.get("user_input", ""),
            chat_history=state.get("chat_history", []),
            source_results=state.get("source_results", []),
            current_data=state.get("current_data"),
            extracted_params=extracted_params,
        )
        self.status = "Built single direct response"
        return make_data({"state": {**state, "result": result}})


