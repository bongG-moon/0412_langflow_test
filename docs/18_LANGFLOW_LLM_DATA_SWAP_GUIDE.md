# Langflow LLM / Data Swap Guide

이 문서는 Langflow Desktop 에서 사용하는 standalone custom component 기준으로,

- LLM 모듈을 다른 것으로 바꿀 때 어디를 수정해야 하는지
- 데이터 tool 을 실제 DB 조회 방식으로 바꿀 때 어디를 수정해야 하는지

를 한 번에 정리한 가이드입니다.

중요한 전제는 아래와 같습니다.

- Langflow Desktop 이 실제로 실행하는 코드는 `langflow_custom_component/*.py` 입니다.
- `langflow_custom_component/_runtime/*.py` 는 읽기 쉬운 참조본입니다.
- standalone 구조 때문에 `_runtime` 만 고치면 Langflow 에 바로 반영되지 않습니다.
- 실제 반영은 `langflow_custom_component/*.py` 노드 코드에도 같은 변경이 들어가야 합니다.
- `paste_ready/*.py` 도 mirror 이므로 같이 맞춰두는 것이 안전합니다.

## 1. 수정할 때의 기본 원칙

가장 안전한 작업 순서는 아래입니다.

1. 먼저 `langflow_custom_component/_runtime/*.py` 에서 읽기 쉬운 참조 코드를 수정합니다.
2. 같은 변경을 `langflow_custom_component/*.py` standalone 노드들에도 반영합니다.
3. `langflow_custom_component/paste_ready/*.py` mirror 도 동일하게 맞춥니다.
4. Langflow Desktop 에서는 기존 custom component 를 수정 저장하기보다 삭제 후 새로 붙여넣는 편이 안전합니다.

standalone runtime 이 각 노드 파일 안에 embed 되어 있기 때문에, 일부 노드만 새 코드이고 일부 노드가 옛 코드를 계속 들고 있으면 stale runtime 문제가 생길 수 있습니다.

## 2. LLM 로더의 실제 위치

LLM 클라이언트를 실제로 만드는 핵심 함수는 아래입니다.

- 참조본: `langflow_custom_component/_runtime/shared/config.py`
- 핵심 함수: `get_llm(task: str = "general", temperature: float = 0.0)`

현재 구현은 아래 방식입니다.

- 환경변수: `LLM_API_KEY`, `LLM_FAST_MODEL`, `LLM_STRONG_MODEL`
- 현재 provider: `langchain_google_genai.ChatGoogleGenerativeAI`
- task 별 모델 선택:
  - fast: `parameter_extract`, `query_mode_review`, `response_summary`
  - strong: `retrieval_plan`, `sufficiency_review`, `analysis_code`, `analysis_retry`, `domain_registry_parse`

즉, 다른 LLM 모듈로 교체할 때 가장 먼저 바꿔야 하는 곳은 `config.py` 의 `get_llm()` 입니다.

### LLM 교체 시 바꿔야 하는 항목

- import 문
- API key 환경변수 이름
- client constructor 인자명
- 모델명 선택 로직
- 응답 객체 shape 가 다르면 `response.content` 처리 방식

현재 active flow 에서는 `Domain Registry` 노드가 JSON 을 직접 받기 때문에, `domain_registry_parse` task 는 예약만 되어 있고 실제 노드 흐름에서 직접 쓰이지는 않습니다.

## 3. 어느 노드가 LLM 을 쓰는가

아래 표는 Langflow 화면 기준 노드와 실제 내부 참조 함수를 같이 적은 것입니다.

| Langflow 노드 | 내부 참조 함수 | LLM task | 수정 필요 여부 |
| --- | --- | --- | --- |
| `Extract Params` | `parameter_service.resolve_required_params()` | `parameter_extract` | 예 |
| `Decide Mode` | `request_context.review_query_mode_with_llm()` | `query_mode_review` | 예 |
| `Plan Datasets` | `retrieval_planner.plan_retrieval_request()` | `retrieval_plan` | 예 |
| `Plan Datasets` | `retrieval_planner._review_missing_base_dataset_keys()` | `retrieval_plan` | 예 |
| `Analyze Single` | `analysis.llm_planner.build_llm_plan()` | `analysis_code`, `analysis_retry` | 예 |
| `Analyze Multi` | `analysis.llm_planner.build_llm_plan()` | `analysis_code`, `analysis_retry` | 예 |
| `Run Followup` | `analysis.llm_planner.build_llm_plan()` | `analysis_code`, `analysis_retry` | 예 |
| `Build Single` | `response_service.generate_response()` | `response_summary` | 예 |
| `Build Multi` | `response_service.generate_response()` | `response_summary` | 예 |
| `Analyze Single` | `response_service.generate_response()` | `response_summary` | 예 |
| `Analyze Multi` | `response_service.generate_response()` | `response_summary` | 예 |
| `Run Followup` | `response_service.generate_response()` | `response_summary` | 예 |

아래 노드들은 현재 기준으로 LLM 을 직접 호출하지 않습니다.

- `Domain Rules`
- `Domain Registry`
- `Session Memory`
- `Route Mode`
- `Build Jobs`
- `Route Plan`
- `Execute Jobs`
- `Route Single`
- `Route Multi`
- `Merge Result`

## 4. LLM 교체 시 실제로 다시 붙여넣어야 하는 노드

최소 반영 기준은 아래 노드들입니다.

- `langflow_custom_component/extract_params.py`
- `langflow_custom_component/decide_mode.py`
- `langflow_custom_component/plan_datasets.py`
- `langflow_custom_component/build_single.py`
- `langflow_custom_component/build_multi.py`
- `langflow_custom_component/analyze_single.py`
- `langflow_custom_component/analyze_multi.py`
- `langflow_custom_component/run_followup.py`

하지만 standalone runtime 중복 구조 때문에, 실제 운영에서는 아래처럼 하는 것을 권장합니다.

- `langflow_custom_component/*.py` 전체를 다시 반영
- Langflow Desktop 에서 기존 custom component 를 삭제 후 새로 생성

## 5. 데이터 tool / DB 조회 로직의 실제 위치

실제 데이터 조회 함수는 아래 파일에 모여 있습니다.

- 참조본: `langflow_custom_component/_runtime/data/retrieval.py`

현재는 샘플 데이터를 생성하는 mock 형태이고, 실제 DB 연동 시 아래 함수들을 교체하면 됩니다.

- `get_production_data(params)`
- `get_target_data(params)`
- `get_defect_rate(params)`
- `get_equipment_status(params)`
- `get_wip_status(params)`
- `get_yield_data(params)`
- `get_hold_lot_data(params)`
- `get_scrap_data(params)`
- `get_recipe_condition_data(params)`
- `get_lot_trace_data(params)`

조회 함수 dispatch 는 아래가 기준입니다.

- `DATASET_TOOL_FUNCTIONS`
- `DATASET_REGISTRY`

dataset 별 필수 파라미터는 아래가 기준입니다.

- `DATASET_REQUIRED_PARAM_FIELDS`

질문 키워드로 dataset 을 고르는 기본 fallback 은 아래 함수가 담당합니다.

- `pick_retrieval_tools(query_text)`

## 6. 실제 DB 연동 시 어느 노드를 수정해야 하는가

### A. 실제 조회 함수만 DB 로 바꾸는 경우

반드시 반영해야 하는 노드:

- `langflow_custom_component/exec_jobs.py`

이 노드는 내부적으로 `runtime_service.prepare_retrieval_source_results()` 를 타고, 그 안에서 `execute_retrieval_jobs()` -> `execute_retrieval_tools()` -> 각 dataset 조회 함수가 호출됩니다.

### B. dataset 종류, label, keyword, 필수 파라미터도 같이 바꾸는 경우

반드시 같이 반영해야 하는 노드:

- `langflow_custom_component/decide_mode.py`
- `langflow_custom_component/plan_datasets.py`
- `langflow_custom_component/build_jobs.py`
- `langflow_custom_component/exec_jobs.py`

이유는 아래와 같습니다.

- `Decide Mode` 는 `pick_retrieval_tools()` 와 현재 source dataset 비교를 사용합니다.
- `Plan Datasets` 는 `DATASET_REGISTRY` 와 dataset catalog 를 기반으로 retrieval plan 을 짭니다.
- `Build Jobs` 는 `DATASET_REQUIRED_PARAM_FIELDS` 기준으로 job 을 만들고 누락 파라미터를 검사합니다.
- `Execute Jobs` 가 실제 tool dispatch 를 수행합니다.

### C. DB 컬럼명이 현재 mock 컬럼명과 다를 수 있는 경우

추가로 같이 맞춰야 하는 참조 파일:

- `langflow_custom_component/_runtime/domain/knowledge.py`
  - `DATASET_COLUMN_ALIAS_SPECS`
  - `PARAMETER_FIELD_SPECS`
  - `DATASET_METADATA`
- `langflow_custom_component/_runtime/shared/column_resolver.py`

이 부분은 실제 DB 컬럼명을 내부 표준 컬럼명으로 맞추는 레이어입니다.

예를 들면:

- DB 에서는 `WORK_DATE` 인데 내부에서는 `WORK_DT` 로 써야 할 수 있음
- DB 에서는 `PROCESS_NAME` 인데 내부에서는 `OPER_NAME` 으로 맞춰야 할 수 있음
- DB 에서는 `QTY` 인데 내부에서는 `production` 으로 맞춰야 할 수 있음

이 alias 정규화가 안 맞으면 후속 분석, 응답 요약, follow-up 재활용이 전부 흔들릴 수 있습니다.

## 7. 데이터 조회 함수가 지켜야 하는 반환 계약

각 dataset 조회 함수는 최소한 아래 형태를 유지하는 것이 안전합니다.

```python
{
    "success": True,
    "tool_name": "get_production_data",
    "data": [
        {"WORK_DT": "20260415", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 1234}
    ],
    "summary": "총 10건, 총 생산량 12.3K"
}
```

그 뒤에 `execute_retrieval_tools()` 가 자동으로 아래를 붙입니다.

- `dataset_key`
- `dataset_label`

즉, DB 함수 쪽에서는 보통 아래 4개만 안정적으로 맞추면 됩니다.

- `success`
- `tool_name`
- `data`
- `summary`

## 8. DB 연동 시 같이 확인할 보조 포인트

### 필터 적용

조회 함수 내부에서 실제 SQL 조건으로 필터링하더라도, 아래 안전장치가 한 번 더 돌 수 있습니다.

- `data/retrieval.py` 의 `_apply_common_filters()`
- `data/retrieval.py` 의 `filter_rows_by_params()`
- `runtime_service.py` 의 `ensure_filtered_result_rows()`

즉, DB 조건절과 후처리 안전장치가 서로 충돌하지 않게 컬럼명을 맞춰두는 것이 중요합니다.

### 필수 파라미터 변경

예를 들어 `production` dataset 이 이제 `date` 뿐 아니라 `factory` 도 필수라면,
아래를 같이 맞춰야 합니다.

- `DATASET_REQUIRED_PARAM_FIELDS`
- `PARAMETER_FIELD_SPECS`
- `Build Jobs` 노드
- `Extract Params` 노드

## 9. 실무에서 추천하는 수정 단위

### LLM provider 만 교체

최소 수정:

- `config.py`
- `extract_params.py`
- `decide_mode.py`
- `plan_datasets.py`
- `build_single.py`
- `build_multi.py`
- `analyze_single.py`
- `analyze_multi.py`
- `run_followup.py`

### DB 조회만 교체

최소 수정:

- `retrieval.py`
- `exec_jobs.py`

### dataset 구조, 필수 파라미터, 컬럼 alias 까지 교체

권장 수정:

- `retrieval.py`
- `knowledge.py`
- `column_resolver.py`
- `extract_params.py`
- `decide_mode.py`
- `plan_datasets.py`
- `build_jobs.py`
- `exec_jobs.py`
- `build_single.py`
- `build_multi.py`
- `analyze_single.py`
- `analyze_multi.py`
- `run_followup.py`

## 10. 최종 반영 체크리스트

1. 참조본 `_runtime` 코드 수정
2. 같은 변경을 `langflow_custom_component/*.py` standalone 노드에도 반영
3. `paste_ready/*.py` mirror 동기화
4. Langflow Desktop 에서 기존 custom component 삭제
5. 최신 코드로 새 custom component 생성
6. 아래 질문으로 smoke test

- `오늘 da공정 생산량 알려줘`
- `그 결과를 mode별로 정리해줘`
- `오늘 생산과 목표를 같이 보여줘`
- `오늘 wb공정 생산량 알려줘`

## 11. 같이 보면 좋은 문서

- `docs/15_LANGFLOW_IMPORT_GUIDE.md`
- `docs/16_LANGFLOW_DOMAIN_INPUTS.md`
- `docs/17_LANGFLOW_DOMAIN_PARITY_VALUES.md`
