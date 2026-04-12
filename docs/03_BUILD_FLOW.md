# 구현 흐름과 LangGraph 설계

이 문서는 이 프로젝트가 어떤 순서로 동작하고, 왜 그런 구조로 나뉘어 있는지 한 번에 설명합니다.
새 기능을 추가하거나 기존 흐름을 이해할 때 가장 먼저 보면 좋은 설계 문서입니다.

## 1. 전체 실행 흐름

코어 실행 흐름은 아래처럼 이해하면 가장 쉽습니다.

```text
질문 해석
-> 새 조회인지 / 현재 결과 후처리인지 판단
-> 필요한 데이터셋 계획
-> 단일 조회 또는 다중 조회
-> 필요 시 후처리 분석
-> 최종 응답 정리
```

LangGraph 기준으로는 아래 순서에 가깝습니다.

```text
resolve_request
  -> plan_retrieval 또는 followup_analysis
  -> single_retrieval 또는 multi_retrieval
  -> finish
```

## 2. 왜 LangGraph 구조를 유지하는가

이 프로젝트는 Langflow로 화면과 노드를 옮겼지만, 실행 흐름의 정본은 여전히 LangGraph 구조입니다.

이렇게 나누는 이유:

- 단계별 책임을 더 명확하게 유지할 수 있습니다.
- 중간 상태를 추적하기 쉽습니다.
- follow-up / retrieval / single / multi 분기를 일관되게 다룰 수 있습니다.
- Langflow와 Streamlit이 같은 코어 로직을 재사용하기 쉬워집니다.

즉, Langflow는 표현 계층이고, LangGraph 구조는 실행 설계의 기준점입니다.

## 3. 주요 분기점

### 1차 분기: follow-up vs retrieval

질문이 현재 결과를 다시 가공하는 요청인지, 새 데이터를 다시 조회해야 하는 요청인지 먼저 나눕니다.

예:

- follow-up
  - `MODE별로 묶어줘`
  - `상위 5개만 보여줘`
- retrieval
  - `오늘 생산과 목표를 같이 보여줘`
  - `WB공정 WIP 얼마야`

### 2차 분기: finish vs single vs multi

retrieval 경로에서는 다시 아래처럼 나뉩니다.

- 바로 종료
  - 날짜 부족, 데이터셋 미확정 등으로 응답만 반환
- single retrieval
  - 한 데이터셋만으로 답할 수 있음
- multi retrieval
  - 여러 데이터셋을 함께 조회하거나 비교해야 함

### 3차 분기: direct response vs post analysis

조회가 끝난 뒤에는 원본 조회 결과를 바로 응답할지, pandas 후처리를 더 수행할지 판단합니다.

예:

- direct response
  - `오늘 DA공정 생산량 보여줘`
- post analysis
  - `오늘 DA공정에서 MODE별 생산량 보여줘`
  - `오늘 생산과 목표를 같이 보여줘`

## 4. 노드별 역할

### `resolve_request`

- 질문에서 날짜, 공정, 제품, 그룹 조건을 뽑습니다.
- 새 조회인지 follow-up인지 판단합니다.

### `plan_retrieval`

- 필요한 데이터셋을 계획합니다.
- 복수 데이터셋이 필요한지 판단합니다.
- 등록된 도메인 규칙을 보고 필요한 데이터셋을 보강할 수 있습니다.

예:

- `생산량` -> `production`
- `생산 달성률` -> `production + target`
- `홀드 부하지수` -> `hold + production`

### `single_retrieval`

- 단일 조회 job을 실행합니다.
- 필요하면 바로 후처리 분석으로 이어집니다.

### `multi_retrieval`

- 여러 데이터셋을 함께 조회합니다.
- 같은 데이터셋을 날짜별로 반복 조회하는 경우도 여기에 해당할 수 있습니다.

### `followup_analysis`

- `current_data`를 기반으로 현재 표를 다시 가공합니다.

### `finish`

- 최종 응답 payload를 UI가 받기 좋은 형태로 정리합니다.

## 5. 도메인 규칙은 어디에 반영되는가

도메인 지식은 별도 기능처럼 보이지만 실제로는 그래프 내부 의사결정과 직접 연결됩니다.

- 파라미터 해석
  - 별칭을 실제 값 목록으로 확장
- retrieval planning
  - 계산/판정 규칙에 필요한 데이터셋 자동 보강
- analysis planning
  - 계산식, 조건식, 출력 컬럼 힌트 제공

즉, 도메인 등록은 UI 바깥 메모 기능이 아니라 실행 흐름의 일부입니다.

## 6. 새 기능을 추가할 때 권장 순서

이 프로젝트에서는 아래 순서를 권장합니다.

```text
요구사항 정리
-> 코어 서비스 함수 구현
-> state 계약 확인
-> Langflow 노드 래핑
-> 캔버스 연결
-> 검증
```

핵심 원칙은 Langflow 노드부터 만들지 말고, 먼저 `manufacturing_agent` 안의 코어 로직을 안정시키는 것입니다.

## 7. Langflow 노드를 만들 때 원칙

노드는 되도록 얇게 유지하는 것이 좋습니다.

좋은 구조:

- 입력 포트 정의
- `state` unwrap
- 서비스 함수 호출
- 결과를 `{"state": ...}` 형태로 다시 감싸기

피해야 할 구조:

- 노드 안에 복잡한 비즈니스 로직 재구현
- LangGraph와 다른 기준으로 분기 판단
- 노드마다 다른 payload 형식 사용

## 8. 분기형 캔버스를 만들 때

분기를 눈에 보이게 하려면 router node를 둡니다.

예:

- query mode router
- retrieval plan router
- single/multi post-processing router

이때 중요한 점:

- 비선택 분기에서는 `None`을 반환
- 선택 분기만 payload를 emit
- `group_outputs=True`로 포트를 분리

## 9. 확장하기 쉬운 방향

현재 구조는 앞으로 아래 확장에 유리합니다.

- 실제 DB 조회 노드 추가
- 검증 전용 노드 추가
- 승인/사람 확인 노드 추가
- 응답 생성과 분석 생성 분리
- 프로세스형 Agent 확장

## 10. 한 줄 요약

이 프로젝트의 설계 핵심은 "질문 해석 -> 조회 계획 -> 단일/복수 조회 -> 후처리 -> 마무리"를 LangGraph 기준으로 유지하고, Langflow와 Streamlit은 그 흐름을 재사용하는 방식으로 얹는 것입니다.
