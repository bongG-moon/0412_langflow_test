# langflow_version 안내

이 디렉터리는 `manufacturing_agent`의 공용 로직을 재사용하면서,
Langflow에서 연결하기 쉬운 형태로 감싼 helper 레이어입니다.

## 역할

여기 코드는 아래 목적을 가집니다.

- Langflow 입력값을 공통 state로 변환
- LangGraph 없이도 비슷한 단계 흐름을 실행
- Langflow 런타임 유무와 관계없이 최소한의 payload 호환 유지

## 주요 파일

- `workflow.py`
  - LangGraph와 유사한 순서로 단계를 실행하는 workflow helper
- `component_base.py`
  - Langflow `Data` payload 호환 helper
- `components.py`
  - 통합형 컴포넌트 묶음

## 추천 사용 방식

### 빠른 전체 실행 확인

- `Manufacturing Agent`

### 압축형 단계 연결

- `Manufacturing State Input`
- `Resolve Manufacturing Request`
- `Run Manufacturing Branch`
- `Finish Manufacturing Result`

### 분기까지 드러내는 연결

- query mode router
- retrieval plan router
- post-processing router

이 구조는 `docs/06`, `docs/07` 문서를 함께 보면 더 이해하기 쉽습니다.

## 왜 이 레이어가 필요한가

Langflow 노드가 곧바로 `manufacturing_agent`의 모든 내부 로직을 직접 다루면,

- state 변환 코드가 노드마다 반복되고
- 테스트 환경에 따라 import가 까다로워지고
- Langflow 전용 glue code가 코어 레이어를 오염시킬 수 있습니다.

그래서 이 디렉터리는 Langflow용 접착제 역할만 맡고,
실제 비즈니스 로직은 `manufacturing_agent`에 남겨두는 구조를 취합니다.
