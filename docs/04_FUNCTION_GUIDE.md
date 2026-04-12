# 핵심 함수 가이드

이 문서는 이 프로젝트에서 중요한 함수와 진입점을 빠르게 찾기 위한 안내서입니다.

## 1. 전체 에이전트 진입점

### `manufacturing_agent/agent.py`

중요 함수:

- `run_agent`
  - LangGraph 기반 전체 실행 진입점
- `run_agent_with_progress`
  - 단계별 진행 메시지를 주면서 실행하는 진입점

이 파일은 “전체 흐름을 한 번에 실행하고 싶다”는 관점에서 가장 먼저 보면 좋습니다.

## 2. LangGraph 분기 구조

### `manufacturing_agent/graph/builder.py`

중요 함수:

- `get_agent_graph`
  - LangGraph 전체 그래프를 만듭니다.
- `route_after_resolve`
  - follow-up인지 retrieval인지 결정합니다.
- `route_after_retrieval_plan`
  - finish / single / multi 분기를 결정합니다.

이 파일은 분기 구조의 정본입니다.

## 3. LangGraph 노드 단위 실행

### `manufacturing_agent/graph/nodes/`

주요 파일:

- `resolve_request.py`
- `plan_retrieval.py`
- `retrieve_single.py`
- `retrieve_multi.py`
- `followup_analysis.py`
- `finish.py`

각 파일은 LangGraph의 한 단계에 대응합니다.

## 4. Langflow workflow 어댑터

### `langflow_version/workflow.py`

중요 함수:

- `build_initial_state`
  - Langflow 입력값을 초기 state로 정리합니다.
- `resolve_request_step`
  - 요청 해석 단계만 실행합니다.
- `plan_retrieval_step`
  - retrieval planning 단계만 실행합니다.
- `run_next_branch`
  - 현재 state 기준 다음 분기 하나를 실행합니다.
- `finish_step`
  - 최종 state를 Langflow 쪽 결과 형식에 맞게 정리합니다.
- `run_langflow_workflow`
  - LangGraph 없이 전체 흐름을 순서대로 실행합니다.

## 5. 파라미터 추출

### `manufacturing_agent/services/parameter_service.py`

중요 함수:

- `resolve_required_params`

질문, 최근 대화, 현재 테이블 컬럼, context를 기반으로
조회에 필요한 파라미터를 추출합니다.

## 6. query mode 판단

### `manufacturing_agent/services/query_mode.py`

중요 함수:

- `choose_query_mode`
  - 신규 조회인지 follow-up인지 판단합니다.
- `needs_post_processing`
  - 조회 후 추가 분석이 필요한지 판단합니다.
- `prune_followup_params`
  - follow-up 경로에서 필요한 파라미터만 정리합니다.

## 7. retrieval planning

### `manufacturing_agent/services/retrieval_planner.py`

중요 함수:

- `plan_retrieval_request`
  - 어떤 dataset이 필요한지 계획합니다.
- `build_retrieval_jobs`
  - 실제 실행 가능한 retrieval job 리스트를 만듭니다.
- `execute_retrieval_jobs`
  - retrieval job을 실행합니다.
- `review_retrieval_sufficiency`
  - 현재 결과로 충분한지 검토합니다.
- `should_retry_retrieval_plan`
  - 다른 dataset으로 재계획이 필요한지 판단합니다.

## 8. retrieval 및 후처리 실행

### `manufacturing_agent/services/runtime_service.py`

중요 함수:

- `run_retrieval`
  - retrieval 흐름의 메인 엔트리입니다.
- `run_followup_analysis`
  - current_data 기반 follow-up 분석을 수행합니다.
- `run_multi_retrieval_jobs`
  - 다중 retrieval 실행 후 다음 경로로 이어갑니다.
- `run_analysis_after_retrieval`
  - 단일 retrieval 뒤 후처리 분석을 수행합니다.

분기형 Langflow 노드 추가 후 중요해진 함수:

- `route_single_post_processing`
  - 단일 조회 뒤 direct/post-analysis 분기를 판단합니다.
- `route_multi_post_processing`
  - 다중 조회 뒤 overview/post-analysis 분기를 판단합니다.
- `build_single_retrieval_response`
  - 단일 조회 direct 응답 payload를 만듭니다.
- `build_multi_retrieval_response`
  - 다중 조회 overview 응답 payload를 만듭니다.
- `run_multi_retrieval_analysis`
  - 다중 조회 병합/분석 경로를 수행합니다.
- `prepare_retrieval_source_results`
  - retrieval 결과를 normalize해서 state에 붙이기 쉽게 만듭니다.

## 9. 응답 생성

### `manufacturing_agent/services/response_service.py`

중요 함수:

- `generate_response`

최종적으로 사용자가 읽는 자연어 응답을 생성합니다.

## 10. 도메인/컨텍스트 보조

### `manufacturing_agent/services/request_context.py`

중요 함수:

- `build_recent_chat_text`
- `get_current_table_columns`
- `has_current_data`
- `attach_result_metadata`
- `attach_source_dataset_metadata`

state를 보강하고, 이전 대화/현재 데이터 문맥을 다루는 데 중요합니다.

## 11. dataset 선택과 mock retrieval

### `manufacturing_agent/data/retrieval.py`

이 파일은 dataset key 선택, mock retrieval, 현재 dataset 구성과 관련된
기능을 포함합니다.

현재 이 프로젝트에서 실제 DB 연결 대신 가장 많은 데이터 관련 기능이
모여 있는 파일입니다.

## 12. 분석 엔진

### `manufacturing_agent/analysis/engine.py`

중요 함수:

- `execute_analysis_query`

LLM이 만든 분석 의도를 실제 데이터 연산으로 연결하는 핵심 함수입니다.

### `manufacturing_agent/analysis/safe_executor.py`

분석용 코드 실행을 제한된 환경에서 수행하는 helper가 들어 있습니다.

## 13. Langflow 공통 helper

### `langflow_version/component_base.py`

중요 함수:

- `make_data`
  - Langflow Data-like payload를 만듭니다.
- `make_branch_data`
  - 활성 branch에서만 값을 내보냅니다.
- `read_data_payload`
  - Langflow payload를 dict로 읽습니다.
- `read_state_payload`
  - `{"state": ...}`를 자동으로 unwrap합니다.

이 helper를 기준으로 커스텀 노드들이 공통 payload 규칙을 맞춥니다.
