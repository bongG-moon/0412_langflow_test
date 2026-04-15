"""질문을 해석하고 첫 분기 결정을 준비하는 노드."""

from ...graph.state import AgentGraphState
from ...services.parameter_service import (
    adjust_retrieval_params_for_context_reset,
    apply_context_inheritance,
    resolve_required_params,
)
from ...services.query_mode import choose_query_mode
from ...services.request_context import build_recent_chat_text, get_current_table_columns


def resolve_request_node(state: AgentGraphState) -> AgentGraphState:
    """현재 질문에서 필터를 추출하고 query_mode 를 결정한다."""

    chat_history = state.get("chat_history", [])
    context = state.get("context", {})
    current_data = state.get("current_data")

    raw_extracted_params = resolve_required_params(
        user_input=state["user_input"],
        chat_history_text=build_recent_chat_text(chat_history),
        current_data_columns=get_current_table_columns(current_data),
        context=context,
        inherit_context=False,
    )
    extracted_params = apply_context_inheritance(raw_extracted_params, context)
    query_mode = choose_query_mode(state["user_input"], current_data, raw_extracted_params)
    if query_mode == "retrieval":
        extracted_params = adjust_retrieval_params_for_context_reset(
            raw_extracted_params=raw_extracted_params,
            extracted_params=extracted_params,
            current_data=current_data,
        )
    return {
        "raw_extracted_params": raw_extracted_params,
        "extracted_params": extracted_params,
        "query_mode": query_mode,
    }
