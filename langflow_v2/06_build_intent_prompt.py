from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    return deepcopy(data) if isinstance(data, dict) else {}


def _unwrap_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("state") if isinstance(payload.get("state"), dict) else {}


def _unwrap_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("domain_payload"), dict):
        payload = payload["domain_payload"]
    return payload.get("domain") if isinstance(payload.get("domain"), dict) else {}


def _unwrap_catalog(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("table_catalog_payload"), dict):
        payload = payload["table_catalog_payload"]
    return payload.get("table_catalog") if isinstance(payload.get("table_catalog"), dict) else payload


def _unwrap_main_flow_filters(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("main_flow_filters_payload"), dict):
        payload = payload["main_flow_filters_payload"]
    return payload.get("main_flow_filters") if isinstance(payload.get("main_flow_filters"), dict) else payload


def _current_data_summary(current: Dict[str, Any]) -> Dict[str, Any]:
    rows = current.get("data") if isinstance(current.get("data"), list) else []
    data_ref = current.get("data_ref") if isinstance(current.get("data_ref"), dict) else {}
    columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else data_ref.get("columns", [])
    return {
        "has_current_data": bool(rows) or bool(data_ref),
        "current_columns": [str(column) for column in columns] if isinstance(columns, list) else [],
        "current_row_count": current.get("row_count") or data_ref.get("row_count") or len(rows),
        "current_has_data_ref": bool(data_ref),
        "current_source_dataset_keys": current.get("source_dataset_keys", []),
        "current_source_required_params": current.get("source_required_params", current.get("retrieval_applied_params", {})),
        "current_source_filters": current.get("source_filters", {}),
        "current_source_column_filters": current.get("source_column_filters", {}),
    }


def build_intent_prompt(state_payload: Any, domain_payload: Any, table_catalog_payload: Any, main_flow_filters_payload: Any = None, reference_date: str = "") -> Dict[str, Any]:
    if isinstance(main_flow_filters_payload, str) and not reference_date:
        reference_date = main_flow_filters_payload
        main_flow_filters_payload = None
    state = _unwrap_state(state_payload)
    question = str(_payload_from_value(state_payload).get("user_question") or state.get("pending_user_question") or "")
    domain = _unwrap_domain(domain_payload)
    table_catalog = _unwrap_catalog(table_catalog_payload)
    main_flow_filters = _unwrap_main_flow_filters(main_flow_filters_payload)
    current = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    filter_defs = main_flow_filters.get("filters") if isinstance(main_flow_filters.get("filters"), dict) else {}
    prompt = f"""You are the intent planner for a manufacturing data-analysis Langflow.
Return JSON only.

Decide:
- query_mode: retrieval or followup_transform
- needed_datasets for retrieval
- required_params such as date as YYYYMMDD
- filters using standard semantic keys from main_flow_filters
- column_filters for explicit data columns that are not defined in main_flow_filters
- needs_pandas
- group_by, sort, top_n when requested

Rules:
- Use only dataset keys in the table catalog.
- Use main_flow_filters keys for common conditions such as process_name, mode,
  line, product_name, equipment_id, den, tech, and mcp_no.
- If a requested condition is not defined in main_flow_filters but is an actual
  table/current-data column, put it in column_filters as the real column name.
- Table catalog filter_mappings map standard semantic keys to each dataset's
  real columns. Do not invent a table column when a mapping exists.
- Treat table catalog entries like tool descriptions. Do not create SQL.
- If a metric requires several datasets, include all of them.
- Metric aliases may appear inside a compound phrase. For example,
  "생산달성률" or "생산달성율" should match a metric alias such as "달성률"
  and include that metric's required_datasets.
- If current_data is available and the user refers to the previous/current result
  ("이때", "그때", "위 결과", "앞선 결과", "방금 결과", "그 결과",
  "that result", "current result") while asking to aggregate, rank, filter,
  compare, sort, or summarize it, set query_mode to followup_transform.
- In a followup_transform, dataset/metric words such as "생산량", "production",
  "목표", or "target" describe columns or measures in current_data. They do not
  by themselves mean a new retrieval.
- If the user asks for a different date, a different dataset scope, a reload
  ("다시 조회", "새로", "new data"), or current_data is not available, set
  query_mode to retrieval.
- If a required_param such as date or lot_id changes from the previous turn,
  set query_mode to retrieval even if the question sounds like a follow-up.
- In follow-up questions, inherit previous required_params and filters unless
  the user overrides them. If the new filter is outside the current_data source
  scope, set query_mode to retrieval.
- For followup_transform, set needed_datasets to [] unless the question clearly
  asks to fetch an additional dataset that is not in current_data.
- Use current_columns to infer group_by, filters, sort.column, and top_n when
  the user asks for current-data analysis.

Examples:
Current state: has_current_data=true, current_columns include MODE and production.
Question: "이때 가장 생산량이 많았던 mode를 알려줘"
Answer:
{{
  "request_type": "data_question",
  "query_mode": "followup_transform",
  "needed_datasets": [],
  "required_params": {{}},
  "filters": {{}},
  "column_filters": {{}},
  "group_by": ["MODE"],
  "sort": {{"column": "production", "ascending": false}},
  "top_n": 1,
  "needs_pandas": true,
  "analysis_goal": "Find the MODE with the highest production in current_data.",
  "reason": "The user refers to the previous result and asks for a ranking."
}}

Current state: has_current_data=true.
Question: "오늘 생산량 다시 조회해줘"
Answer:
{{
  "request_type": "data_question",
  "query_mode": "retrieval",
  "needed_datasets": ["production"],
  "required_params": {{"date": "YYYYMMDD"}},
  "filters": {{}},
  "column_filters": {{}},
  "group_by": [],
  "sort": null,
  "top_n": null,
  "needs_pandas": false,
  "analysis_goal": "Retrieve today's production again.",
  "reason": "The user explicitly asks to query data again."
}}

Question: "어제 wb공정 생산달성율을 mode별로 알려줘"
Domain metric: achievement_rate requires production and target.
Answer:
{{
  "request_type": "data_question",
  "query_mode": "retrieval",
  "needed_datasets": ["production", "target"],
  "required_params": {{"date": "YYYYMMDD"}},
  "filters": {{"process_name": ["W/B1", "W/B2"]}},
  "column_filters": {{}},
  "group_by": ["MODE"],
  "sort": null,
  "top_n": null,
  "needs_pandas": true,
  "analysis_goal": "Calculate achievement_rate by MODE for yesterday WB process.",
  "reason": "The metric requires multiple datasets and pandas calculation."
}}

Table catalog:
{json.dumps(datasets, ensure_ascii=False, default=str, indent=2)}

Main flow filters:
{json.dumps(filter_defs, ensure_ascii=False, default=str, indent=2)}

Domain/metric hints:
{json.dumps(domain, ensure_ascii=False, default=str, indent=2)}

Current state:
{json.dumps({
    **_current_data_summary(current),
    "last_intent": state.get("last_intent", {}),
    "last_retrieval_plan": state.get("last_retrieval_plan", {}),
}, ensure_ascii=False, default=str, indent=2)}

Reference date:
{reference_date or "(runtime Asia/Seoul today)"}

User question:
{question}

Return only:
{{
  "request_type": "data_question",
  "query_mode": "retrieval",
  "needed_datasets": ["production"],
  "required_params": {{"date": "YYYYMMDD"}},
  "filters": {{"process_name": ["D/A3"], "mode": ["DDR5"]}},
  "column_filters": {{"PKG_TYPE1": ["PKG_A"]}},
  "group_by": [],
  "sort": null,
  "top_n": null,
  "needs_pandas": true,
  "analysis_goal": "short goal",
  "reason": "short reason"
}}"""
    return {"prompt_payload": {"prompt_type": "intent", "prompt": prompt, "state": state, "domain": domain, "table_catalog": table_catalog, "main_flow_filters": main_flow_filters, "user_question": question, "reference_date": reference_date}}


class BuildIntentPrompt(Component):
    display_name = "Build Intent Prompt"
    description = "Build the intent-planning prompt from state, domain, and table catalog."
    icon = "FileText"
    name = "BuildIntentPrompt"

    inputs = [
        DataInput(name="state_payload", display_name="State Payload", input_types=["Data", "JSON"]),
        DataInput(name="domain_payload", display_name="Domain Payload", input_types=["Data", "JSON"]),
        DataInput(name="table_catalog_payload", display_name="Table Catalog Payload", input_types=["Data", "JSON"]),
        DataInput(name="main_flow_filters_payload", display_name="Main Flow Filters Payload", input_types=["Data", "JSON"]),
        MessageTextInput(name="reference_date", display_name="Reference Date", value="", advanced=True),
    ]
    outputs = [Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt", types=["Data"])]

    def build_prompt(self):
        payload = build_intent_prompt(getattr(self, "state_payload", None), getattr(self, "domain_payload", None), getattr(self, "table_catalog_payload", None), getattr(self, "main_flow_filters_payload", None), getattr(self, "reference_date", ""))
        self.status = {"prompt_type": "intent", "chars": len(payload["prompt_payload"]["prompt"])}
        return _make_data(payload)

