"""조회 계획을 실제 실행 가능한 job 목록으로 바꾸는 노드."""

from ...data.retrieval import pick_retrieval_tools
from ...graph.state import AgentGraphState
from ...services.retrieval_planner import build_retrieval_jobs, plan_retrieval_request
from ...services.runtime_service import validate_retrieval_jobs


def plan_retrieval_node(state: AgentGraphState) -> AgentGraphState:
    """질문을 바탕으로 retrieval plan 과 retrieval job 을 만든다."""

    user_input = state["user_input"]
    current_data = state.get("current_data")
    extracted_params = state.get("extracted_params", {})
    retrieval_plan = plan_retrieval_request(user_input, state.get("chat_history", []), current_data)
    retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(user_input)

    if not retrieval_keys:
        validation_error = validate_retrieval_jobs(
            retrieval_keys=retrieval_keys,
            jobs=[],
            current_data=current_data,
            extracted_params=extracted_params,
        )
        return {
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": [],
            "retrieval_jobs": [],
            "result": validation_error,
        }

    jobs = build_retrieval_jobs(user_input, extracted_params, retrieval_keys)
    validation_error = validate_retrieval_jobs(
        retrieval_keys=retrieval_keys,
        jobs=jobs,
        current_data=current_data,
        extracted_params=extracted_params,
    )
    if validation_error is not None:
        return {
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": retrieval_keys,
            "retrieval_jobs": jobs,
            "result": validation_error,
        }

    return {
        "retrieval_plan": retrieval_plan,
        "retrieval_keys": retrieval_keys,
        "retrieval_jobs": jobs,
    }
