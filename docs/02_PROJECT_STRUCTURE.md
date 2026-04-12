# 프로젝트 구조 설명

이 문서는 디렉터리 단위로 프로젝트 구조를 설명합니다.

## 최상위 디렉터리

```text
langflow_local_manufacturing_project/
├─ custom_components/
├─ manufacturing_agent/
├─ langflow_version/
├─ reference_materials/
├─ docs/
├─ .env.example
├─ requirements.txt
├─ PROJECT_STRUCTURE.md
└─ README.md
```

## `custom_components`

Langflow가 직접 읽는 커스텀 노드가 들어 있습니다.

현재 핵심 노드는 `custom_components/manufacturing_nodes` 아래에 모여 있습니다.

여기에는 아래 종류의 노드가 있습니다.

### 입력/초기화 노드

- `manufacturing_state_input.py`

### 요청 해석 노드

- `extract_manufacturing_params.py`
- `decide_manufacturing_query_mode.py`
- `resolve_manufacturing_request.py`

### retrieval 준비 노드

- `plan_manufacturing_datasets.py`
- `plan_manufacturing_retrieval.py`
- `build_manufacturing_jobs.py`

### 실행 노드

- `execute_manufacturing_jobs.py`
- `run_manufacturing_followup.py`
- `run_manufacturing_branch.py`

### 분기 노드

- `route_manufacturing_query_mode.py`
- `route_manufacturing_retrieval_plan.py`
- `route_single_post_processing.py`
- `route_multi_post_processing.py`

### 결과 생성/마무리 노드

- `build_single_retrieval_response.py`
- `run_single_retrieval_post_analysis.py`
- `build_multi_retrieval_response.py`
- `run_multi_retrieval_analysis.py`
- `finish_manufacturing_result.py`
- `manufacturing_agent_component.py`

## `manufacturing_agent`

실제 제조 분석 에이전트의 코어 로직이 들어 있습니다.

### `graph/`

LangGraph 상태와 분기 구조가 있습니다.

- `state.py`
  - 상태 타입 정의
- `builder.py`
  - 노드 연결과 분기 기준 정의
- `nodes/`
  - LangGraph 각 노드 구현

### `services/`

핵심 판단과 실행이 모여 있는 레이어입니다.

- 파라미터 추출
- query mode 판단
- retrieval planning
- 응답 생성
- 후처리/분석
- 다중 dataset 병합

### `data/`

dataset 선택과 retrieval 관련 기능이 있습니다.

현재는 실제 DB 연결이 아니라 synthetic/mock 데이터 생성 기반입니다.

### `analysis/`

분석용 쿼리 생성과 안전 실행이 들어 있습니다.

- LLM이 pandas 코드를 만들고
- safe executor가 제한된 환경에서 실행하는 구조입니다.

### `domain/`

도메인 규칙과 registry를 읽어오는 부분입니다.

## `langflow_version`

Langflow가 쓰기 좋은 형태로 감싼 helper 레이어입니다.

주요 파일:

- `workflow.py`
  - LangGraph와 유사한 순서로 단계를 실행하는 래퍼
- `component_base.py`
  - Langflow `Data` payload 호환 helper
- `components.py`
  - 통합형 컴포넌트 모음
- `README.md`
  - 이 레이어 설명

## `reference_materials`

도메인 registry와 참고 자료가 들어 있습니다.

이 자료는 dataset 선택, 규칙 기반 매핑, 값 그룹 해석 등에 영향을 줍니다.

## `docs`

프로젝트 구조, Langflow 개념, 구현 방식, 캔버스 배선까지 설명하는 문서 모음입니다.

## 구조를 볼 때 중요한 관점

아래 기준만 기억하면 구조가 훨씬 쉽게 보입니다.

- Langflow 화면에 보이는 것
  - `custom_components`
- Langflow용 접착제
  - `langflow_version`
- 실제 비즈니스 로직
  - `manufacturing_agent`
