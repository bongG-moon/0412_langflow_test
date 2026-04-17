"""Public entrypoints for the manufacturing data-analysis agent."""

from typing import Any, Callable, Dict, List

from .graph.builder import get_agent_graph
from .graph.nodes.followup_analysis import followup_analysis_node
from .graph.nodes.plan_retrieval import plan_retrieval_node
from .graph.nodes.resolve_request import resolve_request_node
from .graph.nodes.retrieve_multi import multi_retrieval_node
from .graph.nodes.retrieve_single import single_retrieval_node
from .graph.state import AgentGraphState


def run_agent(
    user_input: str,
    chat_history: List[Dict[str, str]] | None = None,
    context: Dict[str, Any] | None = None,
    current_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Run the canonical LangGraph agent once and return its final result."""

    initial_state: AgentGraphState = {
        "user_input": user_input,
        "chat_history": chat_history or [],
        "context": context or {},
        "current_data": current_data if isinstance(current_data, dict) else None,
    }
    final_state = get_agent_graph().invoke(initial_state)
    return dict(final_state.get("result", {}))


def run_agent_with_progress(
    user_input: str,
    chat_history: List[Dict[str, str]] | None = None,
    context: Dict[str, Any] | None = None,
    current_data: Dict[str, Any] | None = None,
    progress_callback: Callable[[str, str], None] | None = None,
) -> Dict[str, Any]:
    """Run the agent in UI-friendly steps and emit progress updates."""

    def notify(title: str, detail: str) -> None:
        if progress_callback is not None:
            progress_callback(title, detail)

    state: AgentGraphState = {
        "user_input": user_input,
        "chat_history": chat_history or [],
        "context": context or {},
        "current_data": current_data if isinstance(current_data, dict) else None,
    }

    notify(
        "1/3 Resolving request",
        "Extracting date, process, product, and grouping conditions.",
    )
    state.update(resolve_request_node(state))

    if state.get("query_mode") == "followup_transform" and isinstance(state.get("current_data"), dict):
        notify(
            "3/3 Analyzing current data",
            "Reusing the current table for a follow-up transform.",
        )
        state.update(followup_analysis_node(state))
        return dict(state.get("result", {}))

    notify(
        "2/3 Planning retrieval",
        "Selecting required datasets and building retrieval jobs.",
    )
    state.update(plan_retrieval_node(state))
    if state.get("result"):
        return dict(state.get("result", {}))

    jobs = state.get("retrieval_jobs", [])
    if len(jobs) > 1:
        notify(
            "3/3 Running multi retrieval",
            "Retrieving multiple datasets, merging results, and analyzing them.",
        )
        state.update(multi_retrieval_node(state))
    else:
        notify(
            "3/3 Running single retrieval",
            "Retrieving one dataset and running any required post-processing.",
        )
        state.update(single_retrieval_node(state))

    return dict(state.get("result", {}))
