# Langflow V2 Manufacturing Flow

`langflow_v2/`는 실제 Langflow standalone custom component 등록을 기준으로
정리한 제조 에이전트 flow입니다. 각 `.py` 파일은 Langflow에 단독 등록될 수
있도록 필요한 helper를 파일 내부에 포함합니다.

중요 원칙:

- `langflow_v2.*` 같은 sibling module import를 사용하지 않습니다.
- 편의형 통합 노드는 제거했고, 실제 연결용 split 노드만 남겼습니다.
- `V2 LLM JSON Caller`는 같은 파일을 두 개의 Langflow node instance로 배치합니다.

## Python File Order

| 순서 | 파일 | Langflow Node | 역할 |
| --- | --- | --- | --- |
| 00 | `00_state_loader.py` | `V2 State Loader` | 질문과 이전 상태를 canonical `state`로 구성 |
| 01 | `01_mongodb_domain_loader.py` | `V2 MongoDB Domain Loader` | MongoDB domain rule 로드 |
| 02 | `02_domain_json_loader.py` | `V2 Domain JSON Loader` | JSON 직접 입력 domain rule 로드 |
| 03 | `03_table_catalog_loader.py` | `V2 Table Catalog Loader` | dataset/tool catalog 로드 |
| 04 | `04_build_intent_prompt.py` | `V2 Build Intent Prompt` | intent 분류용 prompt 생성 |
| 05 | `05_llm_json_caller.py` | `V2 LLM JSON Caller` | LLM 호출, JSON text 반환 |
| 06 | `06_normalize_intent_plan.py` | `V2 Normalize Intent Plan` | intent JSON 정규화 및 retrieval jobs 생성 |
| 07 | `07_dummy_data_retriever.py` | `V2 Dummy Data Retriever` | dummy data 조회 |
| 08 | `08_oracle_data_retriever.py` | `V2 Oracle Data Retriever` | Oracle DB 조회 |
| 09 | `09_build_pandas_prompt.py` | `V2 Build Pandas Prompt` | pandas 분석용 prompt 생성 |
| 10 | `10_normalize_pandas_plan.py` | `V2 Normalize Pandas Plan` | pandas code plan 정규화 |
| 11 | `11_pandas_analysis_executor.py` | `V2 Pandas Analysis Executor` | pandas code 실행 |
| 12 | `12_final_answer_builder.py` | `V2 Final Answer Builder` | final payload, chat message, next state 생성 |

제거한 통합 노드:

- `01_intent_planner.py`: `04 -> 05 -> 06`으로 분리됨
- `04_pandas_analysis.py`: `09 -> 05 -> 10 -> 11`로 분리됨

## Exact Connection Map

아래 표가 Langflow canvas에서 연결해야 하는 정확한 IN/OUT입니다.

| Step | From Node Output | To Node Input | 필수 여부 | 설명 |
| --- | --- | --- | --- | --- |
| 1 | `Chat Input.message` 또는 text | `00 V2 State Loader.user_question` | 필수 | 사용자 질문 |
| 2 | `12 V2 Final Answer Builder.next_state` | `00 V2 State Loader.previous_state` | 선택 | 멀티턴 연결 시 사용 |
| 3A | `01 V2 MongoDB Domain Loader.domain_payload` | `04 V2 Build Intent Prompt.domain_payload` | 택1 | MongoDB domain 사용 |
| 3B | `02 V2 Domain JSON Loader.domain_payload` | `04 V2 Build Intent Prompt.domain_payload` | 택1 | JSON 직접 입력 domain 사용 |
| 4 | `03 V2 Table Catalog Loader.table_catalog_payload` | `04 V2 Build Intent Prompt.table_catalog_payload` | 필수 | dataset/tool 설명 |
| 5 | `00 V2 State Loader.state_payload` | `04 V2 Build Intent Prompt.state_payload` | 필수 | 현재 질문과 상태 |
| 6 | `04 V2 Build Intent Prompt.prompt_payload` | `05A V2 LLM JSON Caller.prompt_payload` | 필수 | intent LLM 호출 |
| 7 | `05A V2 LLM JSON Caller.llm_result` | `06 V2 Normalize Intent Plan.llm_result` | 필수 | intent JSON 후처리 |
| 8A | `06 V2 Normalize Intent Plan.intent_plan` | `07 V2 Dummy Data Retriever.intent_plan` | 택1 | local/demo 조회 |
| 8B | `06 V2 Normalize Intent Plan.intent_plan` | `08 V2 Oracle Data Retriever.intent_plan` | 택1 | 실제 Oracle 조회 |
| 9 | `07` 또는 `08 .retrieval_payload` | `09 V2 Build Pandas Prompt.retrieval_payload` | 필수 | 조회 결과 |
| 10A | `01 V2 MongoDB Domain Loader.domain_payload` | `09 V2 Build Pandas Prompt.domain_payload` | 택1 | pandas 해석용 domain |
| 10B | `02 V2 Domain JSON Loader.domain_payload` | `09 V2 Build Pandas Prompt.domain_payload` | 택1 | pandas 해석용 domain |
| 11 | `09 V2 Build Pandas Prompt.prompt_payload` | `05B V2 LLM JSON Caller.prompt_payload` | 필수 | pandas LLM 호출 |
| 12 | `05B V2 LLM JSON Caller.llm_result` | `10 V2 Normalize Pandas Plan.llm_result` | 필수 | pandas JSON 후처리 |
| 13 | `10 V2 Normalize Pandas Plan.analysis_plan_payload` | `11 V2 Pandas Analysis Executor.analysis_plan_payload` | 필수 | 실행할 분석 계획 |
| 14 | `07` 또는 `08 .retrieval_payload` | `11 V2 Pandas Analysis Executor.retrieval_payload` | 선택 | 보통 불필요. override/debug용 |
| 15 | `11 V2 Pandas Analysis Executor.analysis_result` | `12 V2 Final Answer Builder.analysis_result` | 필수 | 최종 응답 재료 |
| 16A | `12 V2 Final Answer Builder.answer_message` | `Chat Output` | 필수 | 사용자에게 보여줄 답변 |
| 16B | `12 V2 Final Answer Builder.final_result` | API/저장 노드 | 선택 | 전체 payload 필요 시 |
| 16C | `12 V2 Final Answer Builder.next_state` | 다음 turn의 `00.previous_state` | 선택 | 세션 상태 feedback |

`05A`와 `05B`는 같은 파일 `05_llm_json_caller.py`를 Langflow canvas에 두 번
올린 것입니다. 첫 번째는 intent용, 두 번째는 pandas용입니다.

## Canvas Shape

```text
Chat Input
  -> 00 V2 State Loader
        state_payload -> 04 V2 Build Intent Prompt

01 V2 MongoDB Domain Loader
  OR 02 V2 Domain JSON Loader
        domain_payload -> 04 V2 Build Intent Prompt
        domain_payload -> 09 V2 Build Pandas Prompt

03 V2 Table Catalog Loader
        table_catalog_payload -> 04 V2 Build Intent Prompt

04 V2 Build Intent Prompt
  -> 05A V2 LLM JSON Caller
  -> 06 V2 Normalize Intent Plan
  -> 07 V2 Dummy Data Retriever
     OR 08 V2 Oracle Data Retriever
  -> 09 V2 Build Pandas Prompt
  -> 05B V2 LLM JSON Caller
  -> 10 V2 Normalize Pandas Plan
  -> 11 V2 Pandas Analysis Executor
  -> 12 V2 Final Answer Builder
  -> Chat Output
```

## Node Detail

| 파일 | Input name | Output name | Payload key |
| --- | --- | --- | --- |
| `00_state_loader.py` | `user_question`, `previous_state`, `session_id` | `state_payload` | `{user_question, state}` |
| `01_mongodb_domain_loader.py` | `mongo_uri`, `db_name`, `collection_name`, `status`, `limit` | `domain_payload` | `{domain_payload: {domain, domain_source, domain_errors}}` |
| `02_domain_json_loader.py` | `domain_json` | `domain_payload` | `{domain_payload: {domain, domain_source, domain_errors}}` |
| `03_table_catalog_loader.py` | `table_catalog_json` | `table_catalog_payload` | `{table_catalog_payload: {table_catalog, table_catalog_errors}}` |
| `04_build_intent_prompt.py` | `state_payload`, `domain_payload`, `table_catalog_payload`, `reference_date` | `prompt_payload` | `{prompt_payload: {prompt, state, domain, table_catalog}}` |
| `05_llm_json_caller.py` | `prompt_payload`, `llm_api_key`, `model_name`, `temperature` | `llm_result` | `{llm_result: {llm_text, errors, prompt_payload}}` |
| `06_normalize_intent_plan.py` | `llm_result`, `reference_date` | `intent_plan` | `{intent_plan, retrieval_jobs, state, domain, table_catalog}` |
| `07_dummy_data_retriever.py` | `intent_plan` | `retrieval_payload` | `{retrieval_payload: {source_results, intent_plan, state}}` |
| `08_oracle_data_retriever.py` | `intent_plan`, `db_config`, `fetch_limit` | `retrieval_payload` | `{retrieval_payload: {source_results, intent_plan, state}}` |
| `09_build_pandas_prompt.py` | `retrieval_payload`, `domain_payload` | `prompt_payload` | `{prompt_payload: {prompt, retrieval_payload, table, columns}}` |
| `10_normalize_pandas_plan.py` | `llm_result` | `analysis_plan_payload` | `{analysis_plan_payload: {analysis_plan, retrieval_payload, table}}` |
| `11_pandas_analysis_executor.py` | `analysis_plan_payload`, `retrieval_payload` | `analysis_result` | `{analysis_result: {success, data, source_results, intent_plan, state}}` |
| `12_final_answer_builder.py` | `analysis_result`, `answer_text`, `output_row_limit`, `display_row_limit` | `answer_message`, `final_result`, `next_state` | final contract |

## Minimal Required Inputs

로컬 dummy 테스트에서 최소로 넣을 값:

- `00.user_question`: 사용자 질문
- `02.domain_json`: 비워도 동작하지만 metric/domain rule을 넣는 것을 권장
- `03.table_catalog_json`: dataset/tool catalog
- `05.llm_api_key`: 비워도 fallback 동작

실제 Oracle 조회에서 추가로 필요한 값:

- `08.db_config`
- `08.fetch_limit`

## Table Catalog Input

Table catalog는 dataset/tool 설명입니다. SQL을 넣지 않습니다. SQL은
`08_oracle_data_retriever.py` 안의 개별 조회 함수가 소유합니다.

예시 파일: `examples/table_catalog_example.json`

권장 형태:

```json
{
  "datasets": {
    "production": {
      "display_name": "Production",
      "description": "Daily production quantity by date, process, line, and product.",
      "keywords": ["production", "output", "actual", "실적", "생산"],
      "question_examples": ["오늘 D/A3 생산 보여줘"],
      "tool_name": "get_production_data",
      "db_key": "PKG_RPT",
      "required_params": ["date"],
      "param_format": {"date": "YYYYMMDD"},
      "grain": ["WORK_DT", "OPER_NAME", "MODE"]
    }
  }
}
```

컬럼 정보는 선택입니다. `09 V2 Build Pandas Prompt`가 조회 후 실제 컬럼을 보고
pandas prompt를 만들기 때문에 catalog는 tool 선택에 필요한 정보 위주로 두면
됩니다.

## Domain Input

Domain 정보는 중간 조회 노드에는 전달하지 않고 아래 두 노드에서만 사용합니다.

- `04 V2 Build Intent Prompt`: 의도, dataset, filter 판단
- `09 V2 Build Pandas Prompt`: 컬럼/값 해석, metric/formula 힌트

MongoDB는 두 형태를 지원합니다.

Aggregate document:

```json
{
  "domain_id": "manufacturing_default",
  "status": "active",
  "metadata": {"version": "v2"},
  "domain": {
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  }
}
```

Item documents:

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "Achievement Rate",
    "aliases": ["달성률", "목표 대비", "achievement"],
    "required_datasets": ["production", "target"],
    "formula": "sum(production) / sum(target) * 100",
    "output_column": "achievement_rate"
  }
}
```

예시 파일:

- `examples/domain_payload_example.json`
- `examples/mongodb_domain_items_example.json`
- `examples/mongodb_domain_document_example.json`

## Oracle DB Config Input

`08 V2 Oracle Data Retriever.db_config`는 strict JSON과 JSON-ish triple-quoted
DSN을 모두 받습니다.

Strict JSON:

```json
{
  "PKG_RPT": {
    "user": "PKG_USER",
    "password": "PKG_PASSWORD",
    "dsn": "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=svc)))"
  }
}
```

Triple quote form:

```python
{
  "PKG_RPT": {
    "user": "PKG_USER",
    "password": "PKG_PASSWORD",
    "dsn": """(DESCRIPTION=
      (ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))
      (CONNECT_DATA=(SERVICE_NAME=svc))
    )"""
  }
}
```

parser는 strict JSON, `ast.literal_eval`, triple-quote normalization 순서로
시도하며 입력 문자열을 실행하지 않습니다.

## Final Contract

`12 V2 Final Answer Builder.final_result`는 아래 key를 유지합니다.

- `response`
- `tool_results`
- `current_data`
- `extracted_params`
- `awaiting_analysis_choice`
- `state_json`

멀티턴 테스트를 할 때는 `12.next_state`를 다음 turn의 `00.previous_state`에
연결하세요.
