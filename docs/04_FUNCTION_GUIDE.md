# 핵심 함수와 코드 읽기 가이드

이 문서는 중요한 함수와 파일을 빠르게 찾고, 처음 코드를 읽을 때 어디서부터 보면 좋은지 정리한 안내서입니다.

## 1. 전체 흐름 한눈에 보기

```text
app.py
  -> 화면 선택
     -> 채팅 분석 화면
        -> manufacturing_agent/agent.py::run_agent_with_progress()
           -> StateGraph 실행
              -> resolve_request
              -> plan_retrieval 또는 followup_analysis
              -> single_retrieval 또는 multi_retrieval
              -> finish
        -> ui_renderer.py
     -> 도메인 관리 화면
        -> ui_domain_knowledge.py
        -> manufacturing_agent/domain/registry.py
```

## 2. 가장 먼저 볼 파일

### `app.py`

- Streamlit 진입점입니다.
- 화면 전환, 채팅 턴 실행, 상태 출력이 여기서 시작됩니다.

### `manufacturing_agent/agent.py`

- 전체 실행을 오케스트레이션하는 핵심 파일입니다.
- `run_agent`
- `run_agent_with_progress`

### `manufacturing_agent/domain/registry.py`

- 사용자 등록 도메인 규칙의 중심입니다.
- 줄글을 구조화하고, 저장하고, 삭제하고, 실행용 프롬프트로 바꿉니다.

## 3. LangGraph 분기 구조

### `manufacturing_agent/graph/builder.py`

중요 함수:

- `get_agent_graph`
- `route_after_resolve`
- `route_after_retrieval_plan`

이 파일은 분기 구조의 정본입니다.

### `manufacturing_agent/graph/nodes/`

주요 파일:

- `resolve_request.py`
- `plan_retrieval.py`
- `retrieve_single.py`
- `retrieve_multi.py`
- `followup_analysis.py`
- `finish.py`

각 파일은 LangGraph의 한 단계에 대응합니다.

## 4. Langflow 어댑터

### `langflow_version/workflow.py`

중요 함수:

- `build_initial_state`
- `resolve_request_step`
- `plan_retrieval_step`
- `run_next_branch`
- `finish_step`
- `run_langflow_workflow`

Langflow에서는 이 파일이 코어 흐름을 순서대로 재사용하는 접점입니다.

### `langflow_version/component_base.py`

중요 함수:

- `make_data`
- `make_branch_data`
- `read_data_payload`
- `read_state_payload`

커스텀 노드들이 공통 payload 규칙을 맞추는 기준 helper입니다.

## 5. 질문 해석과 planning

### `manufacturing_agent/services/parameter_service.py`

중요 함수:

- `resolve_required_params`

질문, 최근 대화, 현재 테이블 컬럼, context를 기반으로
조회에 필요한 파라미터를 추출합니다.

### `manufacturing_agent/services/query_mode.py`

중요 함수:

- `choose_query_mode`
- `needs_post_processing`
- `prune_followup_params`

신규 조회인지 follow-up인지, 조회 후 후처리가 필요한지 판단합니다.

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

분기형 Langflow 노드와 직접 연결되는 함수:

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

## 7. 데이터와 분석 엔진

### `manufacturing_agent/data/retrieval.py`

- dataset key 선택
- mock retrieval
- 현재 dataset 구성

현재 프로젝트에서 실제 DB 연결 대신 가장 많은 데이터 관련 기능이 모여 있는 파일입니다.

### `manufacturing_agent/analysis/engine.py`

중요 함수:

- `execute_analysis_query`

LLM이 만든 분석 의도를 실제 데이터 연산으로 연결하는 핵심 함수입니다.

### `manufacturing_agent/analysis/llm_planner.py`

- pandas 코드 생성 프롬프트를 구성합니다.
- 도메인 규칙의 계산식과 조건식을 프롬프트에 반영합니다.

### `manufacturing_agent/analysis/safe_executor.py`

- 분석용 코드 실행을 제한된 환경에서 수행합니다.

## 8. 도메인 등록 관련 핵심 파일

### `ui_domain_knowledge.py`

- 도메인 관리 화면 UI를 렌더링합니다.

### `manufacturing_agent/domain/registry.py`

중요 함수:

- `load_domain_registry()`
- `parse_domain_text_to_payload()`
- `preview_domain_submission()`
- `register_domain_submission()`
- `delete_domain_entry()`
- `get_dataset_keyword_map()`
- `match_registered_analysis_rules()`
- `build_registered_domain_prompt()`

## 9. 문제 상황별로 먼저 볼 위치

### 질문 해석이 이상하다

1. `manufacturing_agent/services/parameter_service.py`
2. `manufacturing_agent/domain/knowledge.py`
3. `manufacturing_agent/domain/registry.py`

### 잘못된 데이터셋을 불러온다

1. `manufacturing_agent/graph/builder.py`
2. `manufacturing_agent/services/retrieval_planner.py`
3. `manufacturing_agent/data/retrieval.py`

### 계산 로직이 반영되지 않는다

1. `manufacturing_agent/domain/registry.py`
2. `manufacturing_agent/analysis/llm_planner.py`
3. `manufacturing_agent/analysis/engine.py`

### Langflow 분기가 이상하다

1. `manufacturing_agent/graph/builder.py`
2. `langflow_version/workflow.py`
3. `custom_components/manufacturing_nodes/`

## 10. 처음 읽는 순서 추천

초보자라면 아래 순서를 추천합니다.

1. `app.py`
2. `manufacturing_agent/agent.py`
3. `manufacturing_agent/graph/builder.py`
4. `manufacturing_agent/domain/registry.py`
5. `manufacturing_agent/services/parameter_service.py`
6. `manufacturing_agent/services/runtime_service.py`

## 11. 한 줄 요약

이 프로젝트를 읽을 때는 `app.py -> agent.py -> builder.py -> registry.py -> services` 순서로 보면 전체 흐름과 세부 책임을 가장 빠르게 파악할 수 있습니다.
