"""단일 데이터셋 조회를 수행하는 노드."""

from ...graph.state import AgentGraphState
from ...services.runtime_service import (
    build_single_retrieval_response,
    prepare_retrieval_source_results,
    route_single_post_processing,
    run_analysis_after_retrieval,
)


def single_retrieval_node(state: AgentGraphState) -> AgentGraphState:
    """조회 job 하나를 실행하고, 필요하면 후처리 분석까지 이어간다."""

    extracted_params = state.get("extracted_params", {})
    chat_history = state.get("chat_history", [])
    current_data = state.get("current_data")
    jobs = state.get("retrieval_jobs", [])
    single_job = jobs[0]

    prepared = prepare_retrieval_source_results([single_job], current_data=current_data)
    source_results = prepared["source_results"]
    current_datasets = prepared["current_datasets"]
    source_snapshots = prepared["source_snapshots"]

    if route_single_post_processing(
        user_input=state["user_input"],
        source_results=source_results,
        extracted_params=single_job["params"],
        retrieval_plan=state.get("retrieval_plan"),
    ) == "post_analysis":
        post_processed = run_analysis_after_retrieval(
            user_input=state["user_input"],
            chat_history=chat_history,
            source_results=source_results,
            extracted_params=single_job["params"],
            retrieval_plan=state.get("retrieval_plan"),
            current_datasets=current_datasets,
            source_snapshots=source_snapshots,
        )
        if post_processed is not None:
            return {"result": post_processed}

    return {
        "result": build_single_retrieval_response(
            user_input=state["user_input"],
            chat_history=chat_history,
            source_results=source_results,
            current_data=current_data,
            extracted_params=single_job["params"] or extracted_params,
            current_datasets=current_datasets,
            source_snapshots=source_snapshots,
        )
    }
