"""Langflow custom component: Build Manufacturing Jobs."""

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



class BuildManufacturingJobsComponent(Component):
    display_name = "Build Manufacturing Jobs"
    description = "Build concrete retrieval jobs from dataset keys and extracted parameters."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "ListChecks"
    name = "build_manufacturing_jobs"

    inputs = [DataInput(name="state", display_name="State", info="State with retrieval planning information")]
    outputs = [Output(name="state_with_jobs", display_name="State With Jobs", method="build_jobs", types=["Data"], selected="Data")]

    def build_jobs(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.data.retrieval import dataset_requires_date
        from manufacturing_agent.services.request_context import build_unknown_retrieval_message, has_current_data
        from manufacturing_agent.services.retrieval_planner import build_missing_date_message, build_retrieval_jobs

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        retrieval_keys = state.get("retrieval_keys", [])
        extracted_params = state.get("extracted_params", {})
        current_data = state.get("current_data")
        user_input = state.get("user_input", "")

        if not retrieval_keys:
            updated_state = {
                **state,
                "retrieval_jobs": [],
                "result": {
                    "response": build_unknown_retrieval_message(),
                    "tool_results": [],
                    "current_data": current_data,
                    "extracted_params": extracted_params,
                    "failure_type": "unknown_dataset",
                    "awaiting_analysis_choice": bool(has_current_data(current_data)),
                },
            }
            self.status = "No dataset keys found; stopping job build"
            return make_data({"state": updated_state})

        jobs = build_retrieval_jobs(user_input, extracted_params, retrieval_keys)
        missing_date_jobs = [job for job in jobs if dataset_requires_date(job["dataset_key"]) and not job["params"].get("date")]

        if missing_date_jobs:
            updated_state = {
                **state,
                "retrieval_jobs": jobs,
                "result": {
                    "response": build_missing_date_message([job["dataset_key"] for job in missing_date_jobs]),
                    "tool_results": [],
                    "current_data": current_data,
                    "extracted_params": extracted_params,
                    "failure_type": "missing_date",
                    "awaiting_analysis_choice": bool(has_current_data(current_data)),
                },
            }
            self.status = "Missing required date filters; job build paused"
            return make_data({"state": updated_state})

        updated_state = {**state, "retrieval_jobs": jobs}
        self.status = f"Built {len(jobs)} retrieval job(s)"
        return make_data({"state": updated_state})


