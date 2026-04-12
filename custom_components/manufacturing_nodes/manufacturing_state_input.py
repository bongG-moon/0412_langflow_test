"""Langflow custom component: Manufacturing State Input."""

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
from lfx.io import MessageTextInput, MultilineInput, Output



class ManufacturingStateComponent(Component):
    display_name = "Manufacturing State Input"
    description = "Build the shared state payload used by the manufacturing agent."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Package"
    name = "manufacturing_state_input"

    inputs = [
        MessageTextInput(name="user_input", display_name="User Input", info="Natural-language manufacturing question"),
        MultilineInput(name="chat_history", display_name="Chat History JSON", info="Optional chat history as JSON"),
        MultilineInput(name="context", display_name="Context JSON", info="Optional accumulated context as JSON"),
        MultilineInput(name="current_data", display_name="Current Data JSON", info="Optional current table/result payload as JSON"),
    ]
    outputs = [Output(name="initial_state", display_name="Initial State", method="build_state", types=["Data"], selected="Data")]

    def build_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data
        from langflow_version.workflow import build_initial_state

        state = build_initial_state(
            user_input=getattr(self, "user_input", ""),
            chat_history=getattr(self, "chat_history", None),
            context=getattr(self, "context", None),
            current_data=getattr(self, "current_data", None),
        )
        self.status = "Initial state built"
        return make_data({"state": state})


