# 시작하기

이 문서는 이 프로젝트를 처음 보는 사람이 전체 구조를 빠르게 이해할 수 있도록
정리한 입문 문서입니다.

## 이 프로젝트를 한 문장으로 요약하면

기존 LangGraph 기반 제조 분석 에이전트를, 코어 로직은 유지하면서
Langflow에서도 같은 흐름으로 실행할 수 있게 옮겨 놓은 프로젝트입니다.

## 가장 먼저 기억하면 좋은 3가지

1. 화면에 보이는 Langflow 노드는 `custom_components`에 있습니다.
2. 실제 제조 분석 로직은 `manufacturing_agent`에 있습니다.
3. Langflow가 쓰기 쉬운 형태로 감싼 어댑터는 `langflow_version`에 있습니다.

## Langflow와 LangGraph의 관계

이 프로젝트에서 LangGraph와 Langflow는 경쟁 관계가 아니라 역할이 다릅니다.

- LangGraph
  - 분기와 실행 흐름의 정본
- Langflow
  - 그 흐름을 시각적으로 배치하고 실험하기 위한 캔버스

즉, 이 프로젝트는 LangGraph를 버리고 Langflow로만 다시 만든 것이 아니라,
LangGraph 로직을 Langflow에서 재사용할 수 있도록 구조를 나눈 형태입니다.

## 전체 구조를 쉽게 보는 방법

아래처럼 한 줄로 이해하면 가장 쉽습니다.

```text
Langflow 화면
-> custom_components
-> langflow_version
-> manufacturing_agent
-> reference_materials
```

뜻은 아래와 같습니다.

- Langflow는 `custom_components`를 읽습니다.
- 각 컴포넌트는 필요한 헬퍼를 `langflow_version`에서 가져옵니다.
- 실제 판단과 실행은 `manufacturing_agent`가 담당합니다.
- 도메인 지식은 `reference_materials`를 참고합니다.

## 지금 프로젝트에서 중요한 실행 방식

현재는 크게 3가지 방식으로 사용할 수 있습니다.

### 1. 단일 통합 노드 방식

- `Manufacturing Agent`

가장 빠르게 전체 실행을 확인할 수 있습니다.

### 2. 압축형 단계 노드 방식

- `Manufacturing State Input`
- `Resolve Manufacturing Request`
- `Run Manufacturing Branch`
- `Finish Manufacturing Result`

LangGraph 흐름을 비교적 그대로 유지하면서 캔버스에서 보기 쉬운 구조입니다.

### 3. 분기 가시형 노드 방식

- query mode router
- retrieval plan router
- single/multi post-processing router

중간 분기까지 캔버스에서 눈으로 보고 싶을 때 적합합니다.

## 이 프로젝트를 볼 때 추천 순서

1. 루트 `README.md`를 봅니다.
2. `docs/01_LANGFLOW_CONCEPT.md`를 봅니다.
3. `docs/02_PROJECT_STRUCTURE.md`로 폴더 역할을 확인합니다.
4. 실제 Langflow 배선은 `docs/06`, `docs/07`을 봅니다.

## 주의할 점

- 현재 retrieval은 실제 제조 DB가 아니라 mock/synthetic 데이터 기반입니다.
- follow-up 질문을 Langflow에서 재현하려면 `Current Data JSON`에 이전 결과를 넣어야 합니다.
- Langflow에서 노드가 안 보이면 대부분 `LANGFLOW_COMPONENTS_PATH` 또는 Python 의존성 문제입니다.
