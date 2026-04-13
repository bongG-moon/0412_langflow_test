"""Portable Langflow node: dependency bootstrap for Add Custom Node environments."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, MessageTextInput, MultilineInput, Output, StrInput
from lfx.schema.data import Data
from lfx.schema.message import Message


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    text = getattr(value, "text", None)
    if text is not None:
        return str(text)
    if isinstance(value, dict) and "text" in value:
        return str(value.get("text") or "")
    return str(value)


def _normalize_packages(raw: str) -> list[str]:
    packages: list[str] = []
    for line in str(raw or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        packages.extend(shlex.split(stripped))
    return packages


class PortableDependencyBootstrapComponent(Component):
    display_name = "Portable Dependency Bootstrap"
    description = "Install optional Python dependencies with uv or pip inside Langflow runtime."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Download"
    name = "portable_dependency_bootstrap"

    inputs = [
        MultilineInput(
            name="packages",
            display_name="Packages",
            info="One package spec per line. Example: pandas==2.2.3",
            value="",
        ),
        BoolInput(
            name="use_uv",
            display_name="Use uv",
            value=True,
            info="If True and uv is available, runs `uv pip install` first.",
        ),
        MessageTextInput(
            name="uv_index_url",
            display_name="UV_INDEX_URL Override",
            advanced=True,
            info="Optional private index URL. If empty, the current environment variable is reused.",
        ),
        StrInput(
            name="python_executable",
            display_name="Python Executable",
            value="",
            advanced=True,
            info="Optional Python path for the pip fallback. Defaults to the current runtime.",
        ),
    ]

    outputs = [
        Output(name="installation_result", display_name="Installation Result", method="installation_result", types=["Data"], selected="Data"),
        Output(name="installation_message", display_name="Installation Message", method="installation_message", types=["Message"], selected="Message"),
    ]

    _cached_result: dict[str, Any] | None = None

    def _run_install(self) -> dict[str, Any]:
        if self._cached_result is not None:
            return self._cached_result

        packages = _normalize_packages(_coerce_text(getattr(self, "packages", "")))
        if not packages:
            self._cached_result = {
                "success": True,
                "skipped": True,
                "reason": "No packages requested.",
                "command": [],
                "stdout": "",
                "stderr": "",
                "returncode": 0,
            }
            self.status = "No packages requested"
            return self._cached_result

        env = os.environ.copy()
        override_index = _coerce_text(getattr(self, "uv_index_url", "")).strip()
        if override_index:
            env["UV_INDEX_URL"] = override_index

        if bool(getattr(self, "use_uv", True)) and shutil.which("uv"):
            command = [shutil.which("uv"), "pip", "install", *packages]
            installer = "uv"
        else:
            python_executable = _coerce_text(getattr(self, "python_executable", "")).strip() or sys.executable
            command = [python_executable, "-m", "pip", "install", *packages]
            installer = "pip"

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        result = {
            "success": completed.returncode == 0,
            "skipped": False,
            "installer": installer,
            "packages": packages,
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
            "uv_index_url": env.get("UV_INDEX_URL", ""),
            "filesystem_note": "Requires writable filesystem. Set readOnlyRootFilesystem=false if installs must persist.",
        }
        self._cached_result = result
        self.status = f"{installer} install {'ok' if result['success'] else 'failed'}"
        return result

    def installation_result(self) -> Data:
        return Data(data=self._run_install())

    def installation_message(self) -> Message:
        payload = self._run_install()
        if payload.get("skipped"):
            text = "설치 요청 패키지가 없어 실행을 건너뛰었습니다."
        elif payload.get("success"):
            text = f"{payload.get('installer', 'pip')}로 패키지 설치를 완료했습니다."
        else:
            text = f"{payload.get('installer', 'pip')} 설치가 실패했습니다. stderr를 확인해 주세요."
        return Message(text=text, data=payload)
