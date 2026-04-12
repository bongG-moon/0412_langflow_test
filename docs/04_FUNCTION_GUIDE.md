# 핵심 함수와 코드 읽기 가이드

이 문서는 프로젝트에서 어떤 파일과 함수부터 보면 되는지 빠르게 찾기 위한 안내입니다.

## 1. 전체 실행 흐름

```text
Streamlit
  -> app.py
  -> manufacturing_agent/agent.py::run_agent_with_progress()
  -> LangGraph builder / nodes / services

Langflow
  -> custom_components/manufacturing_nodes/*
  -> langflow_version/component_base.py
  -> langflow_version/workflow.py::build_initial_state()
  -> manufacturing_agent/* core logic
```

## 2. 가장 먼저 볼 파일

### `app.py`

- Streamlit 진입점입니다.
- 채팅 화면과 도메인 관리 화면을 엽니다.

### `manufacturing_agent/agent.py`

- 현재 코어 실행 진입점입니다.
- 중요 함수:
  - `run_agent`
  - `run_agent_with_progress`

### `manufacturing_agent/graph/builder.py`

- LangGraph 분기 구조의 기준 파일입니다.
- 중요 함수:
  - `get_agent_graph`
  - `route_after_resolve`
  - `route_after_retrieval_plan`

## 3. LangGraph 단계별 핵심 파일

### `manufacturing_agent/graph/nodes/`

- `resolve_request.py`
- `plan_retrieval.py`
- `retrieve_single.py`
- `retrieve_multi.py`
- `followup_analysis.py`
- `finish.py`

각 파일이 LangGraph의 한 단계에 대응합니다.

## 4. Langflow에서 실제로 보는 파일

### `custom_components/manufacturing_nodes/`

현재 Langflow는 분기 가시형 노드만 사용합니다.

중요 노드:

- `manufacturing_session_memory.py`
- `extract_manufacturing_params.py`
- `decide_manufacturing_query_mode.py`
- `plan_manufacturing_datasets.py`
- `build_manufacturing_jobs.py`
- `route_manufacturing_query_mode.py`
- `route_manufacturing_retrieval_plan.py`
- `execute_manufacturing_jobs.py`
- `route_single_post_processing.py`
- `route_multi_post_processing.py`
- `build_single_retrieval_response.py`
- `run_single_retrieval_post_analysis.py`
- `build_multi_retrieval_response.py`
- `run_multi_retrieval_analysis.py`
- `run_manufacturing_followup.py`
- `merge_final_manufacturing_result.py`

### `langflow_version/component_base.py`

Langflow 공통 payload helper입니다.

중요 함수:

- `make_data`
- `make_branch_data`
- `read_data_payload`
- `read_state_payload`

### `langflow_version/workflow.py`

현재는 세션 메모리 노드가 초기 state를 만들 때 쓰는 helper만 남아 있습니다.

중요 함수:

- `build_initial_state`

## 5. 질문 해석과 planning

### `manufacturing_agent/services/parameter_service.py`

중요 함수:

- `resolve_required_params`

질문, 최근 대화, 현재 테이블, context를 기반으로 조회에 필요한 파라미터를 추출합니다.

### `manufacturing_agent/services/query_mode.py`

중요 함수:

- `choose_query_mode`
- `needs_post_processing`
- `prune_followup_params`

신규 조회인지 follow-up인지, 후처리가 필요한지 판단합니다.

### `manufacturing_agent/services/retrieval_planner.py`

중요 함수:

- `plan_retrieval_request`
- `build_retrieval_jobs`
- `execute_retrieval_jobs`
- `review_retrieval_sufficiency`
- `should_retry_retrieval_plan`

무엇을 조회할지 결정하는 planning 중심 파일입니다.

## 6. 실행과 후처리

### `manufacturing_agent/services/runtime_service.py`

중요 함수:

- `run_retrieval`
- `run_followup_analysis`
- `run_multi_retrieval_jobs`
- `run_analysis_after_retrieval`

분기형 Langflow 노드가 직접 연결하는 함수:

- `route_single_post_processing`
- `route_multi_post_processing`
- `build_single_retrieval_response`
- `build_multi_retrieval_response`
- `run_multi_retrieval_analysis`
- `prepare_retrieval_source_results`

### `manufacturing_agent/services/response_service.py`

중요 함수:

- `generate_response`

최종 자연어 응답을 생성합니다.

## 7. 데이터 분석 엔진

### `manufacturing_agent/data/retrieval.py`

- dataset key 선택
- mock retrieval
- 현재 dataset 구성

현재 프로젝트에서 실제 DB 연결 대신 mock/synthetic 데이터를 다루는 중심 파일입니다.

### `manufacturing_agent/analysis/engine.py`

중요 함수:

- `execute_analysis_query`

LLM이 만든 분석 의도를 실제 데이터 계산으로 연결합니다.

### `manufacturing_agent/analysis/llm_planner.py`

- pandas 코드 생성 프롬프트를 구성합니다.
- 도메인 규칙과 계산 조건을 프롬프트에 반영합니다.

### `manufacturing_agent/analysis/safe_executor.py`

- 분석용 코드를 제한된 환경에서 실행합니다.

## 8. 도메인 등록 관련 파일

### `manufacturing_agent/domain/registry.py`

중요 함수:

- `load_domain_registry`
- `parse_domain_text_to_payload`
- `preview_domain_submission`
- `register_domain_submission`
- `delete_domain_entry`
- `get_dataset_keyword_map`
- `match_registered_analysis_rules`
- `build_registered_domain_prompt`

## 9. 문제 상황별로 먼저 볼 위치

### 질문 해석이 이상하다

1. `manufacturing_agent/services/parameter_service.py`
2. `manufacturing_agent/services/query_mode.py`
3. `manufacturing_agent/domain/registry.py`

### 잘못된 dataset을 불러온다

1. `manufacturing_agent/graph/builder.py`
2. `manufacturing_agent/services/retrieval_planner.py`
3. `manufacturing_agent/data/retrieval.py`

### 계산 로직이 반영되지 않는다

1. `manufacturing_agent/domain/registry.py`
2. `manufacturing_agent/analysis/llm_planner.py`
3. `manufacturing_agent/analysis/engine.py`

### Langflow 분기가 이상하다

1. `manufacturing_agent/graph/builder.py`
2. `manufacturing_agent/services/runtime_service.py`
3. `custom_components/manufacturing_nodes/`
4. `langflow_version/component_base.py`
