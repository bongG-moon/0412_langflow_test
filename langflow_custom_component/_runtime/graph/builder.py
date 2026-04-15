"""Small routing helpers that mirror the LangGraph branch contract."""

from __future__ import annotations

from .state import AgentGraphState


def route_after_resolve(state: AgentGraphState) -> str:
    """Return the first visible branch after request resolution."""

    if state.get("query_mode") == "followup_transform" and isinstance(state.get("current_data"), dict):
        return "followup_analysis"
    return "plan_retrieval"


def route_after_retrieval_plan(state: AgentGraphState) -> str:
    """Return finish / single / multi after retrieval planning."""

    if state.get("result"):
        return "finish"

    jobs = state.get("retrieval_jobs", [])
    if len(jobs) > 1:
        return "multi_retrieval"
    return "single_retrieval"
