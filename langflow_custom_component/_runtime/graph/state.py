"""Shared state typing for standalone Langflow runtime."""

from typing import Any, Dict, List, Literal, TypedDict


QueryMode = Literal["retrieval", "followup_transform"]


class AgentGraphState(TypedDict, total=False):
    user_input: str
    chat_history: List[Dict[str, str]]
    context: Dict[str, Any]
    current_data: Dict[str, Any] | None
    domain_rules_text: str
    domain_registry_payload: Dict[str, Any] | List[Any]
    raw_extracted_params: Dict[str, Any]
    extracted_params: Dict[str, Any]
    query_mode: QueryMode
    retrieval_plan: Dict[str, Any]
    retrieval_keys: List[str]
    retrieval_jobs: List[Dict[str, Any]]
    source_results: List[Dict[str, Any]]
    current_datasets: Dict[str, Any]
    source_snapshots: List[Dict[str, Any]]
    result: Dict[str, Any]

