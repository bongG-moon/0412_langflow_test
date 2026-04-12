# 구현 흐름 가이드

이 문서는 새 기능이나 새 Langflow 노드를 추가할 때 어떤 순서로 작업하면
좋은지 설명합니다.

## 기본 원칙

이 프로젝트에서는 항상 아래 순서를 추천합니다.

```text
요구사항 정리
-> 코어 서비스 함수 구현
-> state 계약 확인
-> Langflow 노드 래핑
-> 캔버스 연결
-> 검증
```

즉, Langflow 노드부터 만들지 말고 먼저 코어 로직을 안정시키는 것이 중요합니다.

## 1단계. 요구사항을 상태 변화로 바꿔서 본다

새 기능을 추가할 때는 먼저 아래를 정리합니다.

- 입력으로 무엇이 필요한가
- state에 어떤 값이 새로 추가되는가
- 기존 분기 구조 어디에 끼어드는가
- 최종적으로 어떤 `result`를 만들 것인가

예를 들어 새 분석 기능을 추가한다면:

- `source_results`가 있어야 하는지
- `current_data`를 재사용하는지
- 단일 조회 뒤인지, 다중 조회 뒤인지

를 먼저 분명히 해야 합니다.

## 2단계. 코어 로직은 `manufacturing_agent`에 먼저 구현한다

가능하면 먼저 서비스 함수 단위로 구현합니다.

예:

- 파라미터 추출
- query mode 판단
- retrieval planning
- 후처리 분기 판단
- 최종 응답 생성

이 단계에서는 Langflow를 의식하지 않는 것이 좋습니다.

## 3단계. LangGraph와 충돌하지 않는지 확인한다

기존 분기 기준이 이미 있다면 그대로 재사용하는 편이 가장 안전합니다.

예:

- `route_after_resolve`
- `route_after_retrieval_plan`

새 기능 때문에 LangGraph 기준과 Langflow 기준이 달라지면,
나중에 디버깅이 매우 어려워집니다.

## 4단계. Langflow 노드는 얇은 래퍼로 만든다

노드에서는 아래 정도만 처리하는 것이 좋습니다.

- 입력 포트 정의
- `state` unwrap
- 서비스 함수 호출
- 결과를 `{"state": ...}` 형태로 다시 감싸기

즉, 노드 안에서는 긴 분기 로직을 새로 쓰지 않는 것이 원칙입니다.

## 5단계. 분기를 캔버스에 보이게 만들고 싶다면 router node를 만든다

분기형 표현이 필요할 때는 단순 실행 노드가 아니라 router node를 둡니다.

예:

- query mode router
- retrieval plan router
- single/multi post-processing router

이때 중요한 점은:

- 비선택 분기에서는 `None`을 반환
- 선택 분기만 payload를 emit
- `group_outputs=True`로 포트를 분리

## 6단계. 결과 생성 노드와 마무리 노드를 분리한다

특히 분기형 캔버스에서는 아래 구분이 중요합니다.

- 결과를 실제로 만드는 노드
- 최종 state를 정리하는 노드

이 프로젝트에서는 보통:

- `Build ... Response`
- `Run ... Analysis`
- `Finish Manufacturing Result`

처럼 나누는 방식이 읽기 쉽습니다.

## 7단계. 검증한다

최소한 아래는 확인하는 것이 좋습니다.

- 파이썬 문법 오류가 없는지
- 분기 helper가 기대한 문자열을 반환하는지
- inactive branch가 값을 내보내지 않는지
- Langflow 없이도 최소 helper import가 가능한지
- Langflow 앱에서 노드 검색이 되는지

## 추천 작업 방식

### 작은 기능 추가일 때

1. 서비스 함수 추가
2. 기존 노드 수정
3. 문서 보완

### 분기 구조를 드러내야 할 때

1. 서비스 함수 분리
2. router node 추가
3. 결과 노드 추가
4. 캔버스 문서 갱신

## 피해야 할 방식

- Langflow 노드 안에 복잡한 비즈니스 로직을 직접 구현
- LangGraph와 다른 분기 기준을 Langflow에서 따로 만들기
- payload 구조를 노드마다 다르게 쓰기
- follow-up 경로와 retrieval 경로를 한 노드에서 애매하게 섞기
