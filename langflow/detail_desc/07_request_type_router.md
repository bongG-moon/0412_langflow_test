# 07. Request Type Router 상세 설명

대상 코드: `langflow/data_answer_flow/07_request_type_router.py`

이 노드는 정규화된 intent를 보고 다음 흐름을 어디로 보낼지 결정한다. Phase 1에서는 데이터 질문만 실제 구현 대상이고, 프로세스 실행은 추후 확장 대상이다.

## 전체 역할

입력으로 intent와 agent_state를 받는다.

그리고 request_type과 confidence를 기준으로 route를 결정한다.

가능한 route는 다음 세 가지다.

- `data_question`: 데이터 조회/분석 질문
- `process_execution`: 프로세스 실행 요청
- `clarification`: 질문이 너무 불명확해서 추가 확인 필요

출력 구조는 다음과 같다.

```json
{
  "route": "data_question",
  "request_type": "data_question",
  "intent": {},
  "agent_state": {},
  "response": ""
}
```

## import와 공통부

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 출력 text를 만들 때 사용한다. 나머지는 Langflow 호환 공통부와 타입 힌트용이다.

이 노드는 `DataInput`, `Output`, `Data`만 사용한다.

## payload 추출

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

입력값을 dict payload로 바꾼다.

`None`이면 `{}`.

dict면 그대로.

Langflow `Data`면 `.data`.

`.text`가 JSON 문자열이면 파싱해서 dict.

실패하면 `{}`.

이 노드는 JSON 구조만 다루므로 `.text`가 JSON이 아니면 버린다.

## intent 추출

```python
def _get_intent(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    intent = payload.get("intent")
    return intent if isinstance(intent, dict) else payload
```

`Normalize Intent With Domain` 출력은 보통 다음 구조다.

```json
{
  "intent": {}
}
```

따라서 `payload["intent"]`가 dict면 그것을 반환한다. 없으면 payload 자체를 intent로 본다.

## state 추출

```python
def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload
```

`Session State Loader` 출력에서 agent_state를 꺼낸다. `agent_state`가 없으면 `state`를 확인하고, 둘 다 없으면 payload 자체를 state로 본다.

## 핵심 함수: route_request_type

```python
def route_request_type(intent_value: Any, state_value: Any) -> Dict[str, Any]:
```

intent와 state를 받아 route payload를 만든다.

```python
intent = _get_intent(intent_value)
agent_state = _get_state(state_value)
```

입력값에서 실제 intent와 state dict를 꺼낸다.

```python
request_type = str(intent.get("request_type") or "unknown")
```

intent의 request_type을 읽는다. 없으면 unknown이다.

```python
try:
    confidence = float(intent.get("confidence") or 0.0)
except Exception:
    confidence = 0.0
```

confidence를 float으로 변환한다. 실패하면 0.0이다.

### process_execution 분기

```python
if request_type == "process_execution":
    route = "process_execution"
    response = "This request was classified as a process execution request. Phase 1 only supports data questions."
```

프로세스 실행 요청이면 route를 `process_execution`으로 둔다.

Phase 1에서는 아직 process end-to-end 기능을 구현하지 않으므로 안내 response를 넣는다.

### data_question 분기

```python
elif request_type == "data_question":
    route = "data_question"
    response = ""
```

데이터 질문이면 다음 데이터 조회 판단 flow로 넘긴다.

### clarification 분기

```python
elif confidence < 0.25 and not (intent.get("dataset_hints") or intent.get("metric_hints")):
    route = "clarification"
    response = "I could not classify this request as a manufacturing data question. Please include the dataset, metric, date, or process you want to analyze."
```

confidence가 낮고 dataset/metric 힌트도 없으면 질문이 불명확하다고 판단한다.

이 경우 route는 `clarification`이고, 사용자에게 더 구체적으로 질문해 달라는 response를 만든다.

### fallback data_question

```python
else:
    route = "data_question"
    response = ""
```

request_type이 unknown이어도 confidence가 아주 낮지 않거나 힌트가 있으면 data_question으로 진행시킨다.

보수적으로 데이터 질문 흐름을 태우는 구조다.

### 반환

```python
return {
    "route": route,
    "request_type": request_type,
    "intent": intent,
    "agent_state": agent_state,
    "response": response,
}
```

분기 결과와 원본 intent/state를 함께 반환한다.

## Component 입력

```python
DataInput(
    name="intent",
    display_name="Intent",
    input_types=["Data", "JSON"],
)
```

`Normalize Intent With Domain.intent`를 연결한다.

```python
DataInput(
    name="agent_state",
    display_name="Agent State",
    input_types=["Data", "JSON"],
)
```

`Session State Loader.agent_state`를 연결한다.

## Component 출력

이 노드는 output이 네 개다.

```python
Output(name="route_result", method="build_route", types=["Data"])
```

항상 전체 route 결과를 반환한다.

```python
Output(name="data_question", method="data_question_branch", group_outputs=True, types=["Data"])
```

route가 `data_question`일 때만 payload를 반환한다. 아니면 `None`을 반환한다.

```python
Output(name="process_execution", method="process_execution_branch", group_outputs=True, types=["Data"])
```

route가 `process_execution`일 때만 payload를 반환한다.

```python
Output(name="clarification", method="clarification_branch", group_outputs=True, types=["Data"])
```

route가 `clarification`일 때만 payload를 반환한다.

`group_outputs=True` 때문에 각 branch가 별도 포트처럼 보인다.

## 내부 payload 메서드

```python
def _payload(self) -> Dict[str, Any]:
    return route_request_type(getattr(self, "intent", None), getattr(self, "agent_state", None))
```

Component input을 읽어 route_request_type 결과를 반환한다.

여러 output 메서드가 같은 로직을 쓰므로 `_payload()`로 공통화했다.

## output 메서드들

```python
def build_route(self) -> Data:
    payload = self._payload()
return _make_data(payload)
```

항상 route payload를 반환한다.

```python
def data_question_branch(self) -> Data:
    payload = self._payload()
return _make_data(payload) if payload["route"] == "data_question" else None
```

data_question일 때만 Data를 반환한다. 아니면 `None`이다.

```python
def process_execution_branch(self) -> Data:
```

process_execution일 때만 Data를 반환한다.

```python
def clarification_branch(self) -> Data:
```

clarification일 때만 Data를 반환한다.

## 다음 노드 연결

Phase 1에서는 보통 다음처럼 연결한다.

```text
Request Type Router.data_question -> Query Mode Decider.intent
Session State Loader.agent_state -> Query Mode Decider.agent_state
Domain JSON Loader.domain_payload -> Query Mode Decider.domain_payload
```

추후 process 기능이 생기면 다음 branch가 별도 flow로 이어진다.

```text
Request Type Router.process_execution -> Process Flow
```

## 학습 포인트

이 노드는 “분기 노드” 패턴이다.

전체 결과를 항상 내보내는 `route_result`와, 조건에 맞을 때만 값이 나가는 branch output을 함께 제공한다. Langflow에서 branch를 시각적으로 나누고 싶을 때 이런 구조가 유용하다.
