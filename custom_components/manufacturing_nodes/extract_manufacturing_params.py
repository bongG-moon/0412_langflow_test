"""Langflow custom component: Extract Manufacturing Params."""

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



class ExtractManufacturingParamsComponent(Component):
    display_name = "Extract Manufacturing Params"
    description = "Extract dates, process names, products, and other retrieval parameters."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Filter"
    name = "extract_manufacturing_params"

    inputs = [DataInput(name="state", display_name="State", info="Initial state or state from the previous step")]
    outputs = [Output(name="state_with_params", display_name="State With Params", method="extract_params", types=["Data"], selected="Data")]

    def extract_params(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_state_payload
        from manufacturing_agent.services.parameter_service import resolve_required_params
        from manufacturing_agent.services.request_context import build_recent_chat_text, get_current_table_columns

        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        chat_history = state.get("chat_history", [])
        context = state.get("context", {})
        current_data = state.get("current_data")

        extracted_params = resolve_required_params(
            user_input=state.get("user_input", ""),
            chat_history_text=build_recent_chat_text(chat_history),
            current_data_columns=get_current_table_columns(current_data),
            context=context,
        )
        updated_state = {**state, "extracted_params": extracted_params}
        self.status = "Manufacturing parameters extracted"
        return make_data({"state": updated_state})


