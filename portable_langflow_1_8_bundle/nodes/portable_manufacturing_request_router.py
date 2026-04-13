"""Portable Langflow node: extract parameters and route follow-up vs retrieval."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


PROCESS_ALIASES = {
    "D/A3": ["d/a3", "da3", "da-3", "da 3", "d a3"],
    "WB": ["wb", "wirebond", "wire bond"],
    "FCB": ["fcb", "flipchip", "flip chip"],
    "BM": ["bm"],
    "SAT": ["sat"],
    "PL": ["pl"],
    "QC": ["qc"],
}

FOLLOWUP_KEYWORDS = [
    "그 결과",
    "그거",
    "위 결과",
    "정리",
    "상위",
    "평균",
    "합계",
    "비교",
    "공정별",
    "라인별",
    "제품별",
    "다시",
    "차트",
    "그래프",
    "top",
    "average",
    "sum",
    "group",
]

RESET_KEYWORDS = [
    "오늘",
    "어제",
    "yesterday",
    "today",
    "생산",
    "불량",
    "불량률",
    "달성률",
    "목표",
    "재고",
    "wip",
    "설비",
    "장비",
]


def _as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return dict(data)
    return {}


def _detect_date(text: str) -> str:
    lowered = text.lower()
    now = datetime.now()
    if "어제" in text or "yesterday" in lowered:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if "오늘" in text or "today" in lowered:
        return now.strftime("%Y-%m-%d")

    compact = re.search(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?(0[1-9]|[12]\d|3[01])", text)
    if compact:
        return f"{compact.group(1)}-{compact.group(2)}-{compact.group(3)}"

    korean = re.search(r"(20\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if korean:
        return f"{int(korean.group(1)):04d}-{int(korean.group(2)):02d}-{int(korean.group(3)):02d}"
    return ""


def _detect_processes(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for canonical, aliases in PROCESS_ALIASES.items():
        if canonical.lower() in lowered or any(alias in lowered for alias in aliases):
            found.append(canonical)
    return found


def _detect_group_by(text: str) -> str:
    lowered = text.lower()
    if "공정별" in text or "by process" in lowered:
        return "process_name"
    if "라인별" in text or "by line" in lowered:
        return "line_name"
    if "제품별" in text or "by product" in lowered:
        return "product_name"
    return ""


def _detect_top_n(text: str) -> int:
    match = re.search(r"(?:상위|top)\s*(\d+)", text.lower())
    return int(match.group(1)) if match else 0


def _detect_metric_intent(text: str) -> str:
    lowered = text.lower()
    if "불량률" in text or "defect rate" in lowered:
        return "defect_rate"
    if "달성률" in text or "목표 대비" in text or "achievement" in lowered:
        return "achievement_rate"
    if "재고" in text or "wip" in lowered:
        return "wip"
    if "설비" in text or "장비" in text or "uptime" in lowered or "alarm" in lowered:
        return "equipment"
    if "불량" in text or "defect" in lowered:
        return "defect"
    if "목표" in text or "target" in lowered:
        return "target"
    return "production"


class PortableManufacturingRequestRouterComponent(Component):
    display_name = "Portable Manufacturing Request Router"
    description = "Extract manufacturing query parameters and route follow-up vs retrieval."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitBranch"
    name = "portable_manufacturing_request_router"

    inputs = [
        DataInput(name="state", display_name="State", info="Session state from Portable Manufacturing Session State"),
    ]

    outputs = [
        Output(name="followup_state", display_name="Followup State", method="followup_state", group_outputs=True, types=["Data"], selected="Data"),
        Output(name="retrieval_state", display_name="Retrieval State", method="retrieval_state", group_outputs=True, types=["Data"], selected="Data"),
    ]

    _cached_state: dict[str, Any] | None = None
    _cached_mode: str | None = None

    def _resolve(self) -> tuple[dict[str, Any], str]:
        if self._cached_state is not None and self._cached_mode is not None:
            return self._cached_state, self._cached_mode

        state = _as_payload(getattr(self, "state", None))
        user_input = str(state.get("user_input") or "").strip()
        current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else None

        extracted_params = {
            "date": _detect_date(user_input),
            "process_names": _detect_processes(user_input),
            "group_by": _detect_group_by(user_input),
            "top_n": _detect_top_n(user_input),
            "metric_intent": _detect_metric_intent(user_input),
            "needs_post_processing": any(keyword in user_input.lower() for keyword in ["top", "average", "sum"])
            or any(keyword in user_input for keyword in ["상위", "평균", "합계", "정리", "비교", "공정별", "라인별", "제품별"]),
        }

        lowered = user_input.lower()
        explicit_followup = any(keyword in lowered for keyword in FOLLOWUP_KEYWORDS)
        explicit_reset = bool(extracted_params["date"]) or any(keyword in lowered for keyword in RESET_KEYWORDS)

        if current_data and explicit_followup and not explicit_reset:
            query_mode = "followup"
        elif current_data and not explicit_reset and extracted_params["group_by"]:
            query_mode = "followup"
        else:
            query_mode = "retrieval"

        updated_state = {**state, "extracted_params": extracted_params, "query_mode": query_mode}
        self._cached_state = updated_state
        self._cached_mode = query_mode
        self.status = f"Routed to {query_mode}"
        return updated_state, query_mode

    def followup_state(self) -> Data | None:
        state, mode = self._resolve()
        if mode != "followup":
            return None
        return Data(data=state)

    def retrieval_state(self) -> Data | None:
        state, mode = self._resolve()
        if mode != "retrieval":
            return None
        return Data(data=state)
