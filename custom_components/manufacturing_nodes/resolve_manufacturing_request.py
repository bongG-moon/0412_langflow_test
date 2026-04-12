"""Langflow custom component: Resolve Manufacturing Request."""

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



class ResolveRequestComponent(Component):
    display_name = "Resolve Manufacturing Request"
    description = "Resolve extracted parameters and query mode in one step."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Route"
    name = "resolve_manufacturing_request"

    inputs = [DataInput(name="state", display_name="State", info="State created by the previous component")]
    outputs = [Output(name="resolved_state", display_name="Resolved State", method="resolve_state", types=["Data"], selected="Data")]

    def resolve_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from langflow_version.workflow import resolve_request_step

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        resolved = resolve_request_step(state)
        self.status = f"Request resolved: mode={resolved.get('query_mode', 'unknown')}"
        return make_data({"state": resolved})


