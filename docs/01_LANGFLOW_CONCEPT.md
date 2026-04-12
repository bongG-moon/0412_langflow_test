# Langflow 개념 정리

이 문서는 이 프로젝트 관점에서 Langflow를 어떻게 이해하면 좋은지 설명합니다.

## Langflow에서 중요한 개념

### 노드

Langflow의 기본 단위는 노드입니다.

- 입력을 받습니다.
- 어떤 함수를 실행합니다.
- 출력을 다음 노드로 넘깁니다.

이 프로젝트에서는 대부분의 노드가 아래 역할을 합니다.

- state를 입력으로 받기
- 코어 서비스 함수를 호출하기
- 결과 state를 다시 감싸서 출력하기

### 포트

각 노드는 입력 포트와 출력 포트를 가집니다.

- 입력 포트
  - 이전 노드의 결과를 받습니다.
- 출력 포트
  - 다음 노드로 넘길 값을 내보냅니다.

분기를 눈에 보이게 만들려면 출력 포트가 여러 개여야 합니다.

### Data payload

Langflow는 보통 `Data` 객체 또는 그와 비슷한 payload를 노드 사이에 전달합니다.

이 프로젝트에서는 주로 아래 형태를 씁니다.

```python
{"state": {...}}
```

즉, 실제 핵심 데이터는 `state` 딕셔너리이고, Langflow는 그것을 감싸는
껍데기 역할을 합니다.

## 왜 state 하나로 통일하는가

state 기반으로 통일하면 장점이 큽니다.

- 여러 단계를 지나도 데이터 구조가 일관됩니다.
- LangGraph와 Langflow가 같은 상태 모델을 공유할 수 있습니다.
- 디버깅할 때 어느 단계에서 어떤 값이 추가됐는지 보기 쉽습니다.

이 프로젝트의 state에는 보통 아래 값들이 들어갑니다.

- `user_input`
- `chat_history`
- `context`
- `current_data`
- `extracted_params`
- `query_mode`
- `retrieval_plan`
- `retrieval_jobs`
- `source_results`
- `result`

## 얇은 래퍼 노드 패턴

이 프로젝트의 Langflow 노드는 되도록 얇게 유지하는 것이 원칙입니다.

좋은 구조:

- 노드에서는 입력/출력 포트만 정의
- state를 읽고 정리
- 실제 판단은 서비스 함수에 위임

좋지 않은 구조:

- 노드 안에 복잡한 분기 로직을 다시 구현
- LangGraph와 다른 기준으로 판단
- 다른 노드에서도 같은 로직을 중복 작성

## 압축형 노드와 분해형 노드

이 프로젝트에는 두 가지 스타일이 공존합니다.

### 압축형 노드

예:

- `Resolve Manufacturing Request`
- `Run Manufacturing Branch`

특징:

- LangGraph의 여러 단계를 한 노드 안에서 감쌉니다.
- 실행 결과를 빨리 확인하기 좋습니다.
- 캔버스는 단순해지지만 내부 분기는 덜 보입니다.

### 분해형 노드

예:

- `Extract Manufacturing Params`
- `Decide Manufacturing Query Mode`
- `Plan Manufacturing Retrieval`
- `Route Manufacturing Query Mode`

특징:

- 단계별 책임이 분리돼 있습니다.
- 분기와 상태 변화를 눈으로 확인하기 좋습니다.
- 디버깅과 설명에 유리합니다.

## 분기형 포트가 왜 중요한가

예전 구조에서는 분기가 코드 안에 숨어 있고, 캔버스에는 직선 흐름처럼 보일 수 있었습니다.

지금은 router node를 통해 아래 분기가 포트로 보이게 만들었습니다.

- follow-up vs retrieval
- finish vs single vs multi
- direct response vs post analysis

이렇게 하면 Langflow 캔버스가 단순 데모가 아니라,
실제 분기 구조를 보여주는 시각화 도구 역할도 하게 됩니다.

## 이 프로젝트에서 Langflow를 볼 때 핵심 태도

Langflow는 이 프로젝트에서 로직의 주인이 아니라 표현 계층입니다.

즉, 좋은 Langflow 설계란:

- 코어 로직을 중복 구현하지 않고
- 기존 LangGraph 기준을 재사용하면서
- 캔버스에서는 더 잘 보이게 정리하는 것

입니다.
