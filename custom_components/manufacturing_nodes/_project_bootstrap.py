"""Helpers for making project modules importable from Langflow custom nodes."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_repo_root(path: Path) -> bool:
    return (path / "langflow_version").is_dir() and (path / "manufacturing_agent").is_dir()


def ensure_project_root(component_file: str) -> Path:
    """Insert the project root into sys.path."""

    candidates: list[Path] = []

    explicit_root = os.environ.get("MANUFACTURING_AGENT_PROJECT_ROOT")
    if explicit_root:
        candidates.append(Path(explicit_root).expanduser())

    components_path = os.environ.get("LANGFLOW_COMPONENTS_PATH")
    if components_path:
        components_dir = Path(components_path).expanduser()
        candidates.append(components_dir.parent)

    current_file = Path(component_file).resolve()
    candidates.extend(current_file.parents)
    candidates.append(Path.cwd())

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
