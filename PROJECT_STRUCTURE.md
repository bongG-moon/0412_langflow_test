# 프로젝트 구조 가이드

이 문서는 이 저장소에서 어떤 코드를 어디에 두는지 빠르게 판단할 수 있도록
정리한 구조 가이드입니다.

## 큰 원칙

이 프로젝트는 아래 3개 층으로 나뉩니다.

1. `custom_components`
   - Langflow가 직접 읽는 노드 레이어
2. `langflow_version`
   - Langflow가 쓰기 쉬운 형태로 state와 workflow를 감싼 어댑터 레이어
3. `manufacturing_agent`
   - 실제 제조 분석 비즈니스 로직이 들어 있는 코어 레이어

즉, 화면에 보이는 노드와 실제 로직을 분리해서 관리하는 구조입니다.

## 어디에 무엇을 넣어야 하는가

### `custom_components/manufacturing_nodes`

여기에 두는 것:

- Langflow 캔버스에 실제로 보일 커스텀 컴포넌트
- `Component`를 상속한 노드 정의
- 입력과 출력 포트 정의
- state payload를 읽고 서비스 함수를 호출하는 얇은 래퍼

여기에 두지 않는 것:

- 복잡한 비즈니스 규칙
- 데이터 처리 핵심 로직
- 분석/병합/후처리의 본체 구현

핵심 원칙은 간단합니다.

- 노드는 얇게 유지
- 실제 판단은 코어 서비스에 위임

### `langflow_version`

여기에 두는 것:

- Langflow 전용 state 변환 helper
- Langflow에서 쓰기 쉬운 workflow wrapper
- Langflow 런타임이 없어도 최소한의 import/test가 가능하도록 돕는 유틸

대표 파일:

- `workflow.py`
- `component_base.py`
- `components.py`

### `manufacturing_agent`

여기에 두는 것:

- 제조 질의 해석
- dataset 선택과 retrieval 계획
- 실제 retrieval 실행
- 분석/병합/후처리
- LangGraph 상태 정의와 노드 연결

세부 역할은 대략 아래처럼 나뉩니다.

- `graph/`
  - LangGraph 상태와 분기 구조
- `services/`
  - 핵심 판단 로직과 실행 서비스
- `data/`
  - dataset 정의와 retrieval 계층
- `analysis/`
  - 분석 쿼리 생성과 안전 실행
- `domain/`
  - 도메인 규칙과 registry
- `shared/`
  - 공통 유틸

## 추천 개발 흐름

새 기능을 추가할 때는 아래 순서를 추천합니다.

1. 먼저 `manufacturing_agent`에 코어 로직을 추가합니다.
2. Langflow에서 노드가 필요하면 `custom_components`에 얇은 래퍼를 추가합니다.
3. 여러 노드가 공유하는 Langflow helper가 필요하면 `langflow_version`에 추가합니다.

즉, 순서는 항상 아래처럼 가는 편이 안전합니다.

```text
코어 로직 설계
-> 서비스 함수 구현
-> Langflow 노드 래핑
-> 캔버스 연결
```

## 어떤 작업을 어디에 둘지 빠르게 판단하는 기준

### `custom_components`에 두기 좋은 것

- 입력/출력 포트 정의
- Langflow 표시 이름과 설명
- state payload를 읽고 쓰는 얇은 glue code
- 분기 포트를 노출하는 router component

### `manufacturing_agent`에 두기 좋은 것

- 파라미터 추출
- query mode 판단
- retrieval plan 생성
- retrieval job 생성/실행
- 후처리 판단
- 다중 dataset 병합과 분석
- 최종 응답 생성

### `langflow_version`에 두기 좋은 것

- `Data` payload 호환 helper
- `state` unwrap helper
- LangGraph와 유사한 단계 실행 wrapper

## 실무 팁

- Langflow 노드에서 비즈니스 로직을 다시 구현하지 않는 것이 중요합니다.
- 분기 기준이 이미 LangGraph에 있다면, Langflow에서는 그 함수를 재사용하는 쪽이 좋습니다.
- 한 노드에서 여러 분기를 보여주고 싶으면 `group_outputs=True`를 사용하는 구조가 적합합니다.
