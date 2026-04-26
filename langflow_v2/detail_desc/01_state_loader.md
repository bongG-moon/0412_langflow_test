# 01. State Loader

## 한 줄 역할

사용자 질문과 이전 상태를 합쳐서 이번 턴의 표준 `state_payload`를 만드는 노드입니다.

## 왜 필요한가

Langflow에서는 Chat Input, Message History, 직접 입력값이 서로 다른 형태로 들어올 수 있습니다.
뒤 노드들이 매번 다른 형태를 처리하면 복잡해지므로, 이 노드에서 한 번 정리합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `chat_input` | Chat Input 노드 출력입니다. 실제 Playground 질문을 연결합니다. |
| `user_question` | Chat Input을 연결하지 않을 때 쓰는 수동 질문 입력입니다. 테스트용입니다. |
| `previous_state` | `State Memory Extractor.previous_state`를 연결합니다. |
| `session_id` | 수동 세션 ID입니다. Message History를 쓰면 비워도 됩니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `state_payload` | 이번 질문과 이전 기억을 합친 상태입니다. |

대표 구조:

```json
{
  "user_question": "오늘 da공정 생산량 알려줘",
  "state": {
    "session_id": "default",
    "chat_history": [],
    "context": {},
    "current_data": {}
  }
}
```

## 주요 함수 설명

- `_payload_from_value`: Langflow `Data`, `Message`, dict 등에서 실제 dict를 꺼냅니다.
- `_text_from_value`: Chat Input에서 질문 문자열을 꺼냅니다.
- `_as_dict_state`: 이전 상태가 문자열/JSON/dict 중 무엇이든 dict로 바꿉니다.
- `load_state`: 질문, 세션, 이전 상태를 합쳐 표준 state를 만듭니다.

## 초보자 포인트

이 노드는 "이번 턴의 출발점"입니다.

후속 질문이 잘못 새 조회로 라우팅된다면 먼저 확인할 것은 다음입니다.

- `previous_state`가 비어 있지 않은가?
- `current_data`가 이전 결과를 가지고 있는가?
- 같은 Playground 세션에서 질문하고 있는가?

## 연결

```text
Chat Input.message
-> State Loader.chat_input

State Memory Extractor.previous_state
-> State Loader.previous_state

State Loader.state_payload
-> Build Intent Prompt.state_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "chat_input": {
    "text": "이때 가장 생산량이 많았던 mode 알려줘",
    "metadata": {
      "session_id": "playground-1"
    }
  },
  "previous_state": {
    "state": {
      "session_id": "playground-1",
      "chat_history": [],
      "context": {"last_route": "single_retrieval"},
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 10},
          {"MODE": "B", "production": 20}
        ]
      }
    }
  }
}
```

### 출력 예시

```json
{
  "user_question": "이때 가장 생산량이 많았던 mode 알려줘",
  "state": {
    "session_id": "playground-1",
    "chat_history": [],
    "context": {"last_route": "single_retrieval"},
    "current_data": {
      "rows": [
        {"MODE": "A", "production": 10},
        {"MODE": "B", "production": 20}
      ]
    },
    "source_snapshots": [],
    "last_intent": {},
    "last_retrieval_plan": {},
    "pending_user_question": "이때 가장 생산량이 많았던 mode 알려줘"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_session_id_from_value` | `{"metadata": {"session_id": "abc"}}` | `"abc"` | Playground나 Chat Input 객체 안에 숨은 session id를 찾아 후속 질문을 같은 세션으로 묶습니다. |
| `_text_from_value` | `Message(text="오늘 생산량")` | `"오늘 생산량"` | Chat Input이 Message든 dict든 문자열이든 질문 문장만 꺼냅니다. |
| `_as_dict_state` | `{"state_json": "{\"current_data\":{}}"}` | `{"current_data": {}}` | 이전 state가 dict 또는 JSON 문자열로 들어와도 같은 dict 형태로 맞춥니다. |
| `_as_list` | `None` | `[]` | `chat_history`처럼 list가 필요한 값이 비어 있어도 다음 코드가 깨지지 않게 합니다. |
| `load_state` | `user_question`, `previous_state`, `session_id` | `{"user_question": "...", "state": {...}}` | 현재 질문과 이전 상태를 합쳐 v2 flow의 표준 state를 만듭니다. |
| `build_state` | Langflow input들 | `Data(data={"user_question": ..., "state": ...})` | Langflow output method입니다. status에 세션과 현재 데이터 존재 여부를 표시합니다. |

### 코드 흐름

```text
Chat Input에서 질문 추출
-> Previous State에서 chat_history/context/current_data 복원
-> session_id 결정
-> pending_user_question에 현재 질문 저장
-> Build Intent Prompt가 읽을 state_payload 반환
```

### 초보자 포인트

`current_data`를 여기서 유지하지 못하면 후속 질문이 "이전 결과 분석"이 아니라 "새 조회"로 잘못 갈 수 있습니다.

## 함수 코드 단위 해석: `load_state`

이 함수는 현재 질문과 이전 state를 합쳐 이번 턴에서 사용할 표준 state를 만듭니다.

### 함수 input

```json
{
  "user_question_value": {"text": "이때 mode별로 정리해줘", "metadata": {"session_id": "abc"}},
  "previous_state_value": {
    "state": {
      "session_id": "abc",
      "current_data": {"data": [{"MODE": "A", "production": 10}]},
      "chat_history": []
    }
  },
  "session_id_value": "default"
}
```

### 함수 output

```json
{
  "user_question": "이때 mode별로 정리해줘",
  "state": {
    "session_id": "abc",
    "chat_history": [],
    "context": {},
    "current_data": {"data": [{"MODE": "A", "production": 10}]},
    "pending_user_question": "이때 mode별로 정리해줘"
  }
}
```

### 핵심 코드 해석

```python
previous_state = _as_dict_state(previous_state_value)
```

이전 노드에서 넘어온 previous state를 dict로 바꿉니다. previous state가 `Data`, dict, JSON 문자열 중 무엇이든 여기서 하나의 dict 형태로 통일합니다.

```python
user_question = _text_from_value(user_question_value) or str(previous_state.get("pending_user_question") or "").strip()
```

현재 Chat Input에서 질문을 먼저 꺼냅니다. 만약 현재 입력이 비어 있으면 previous state에 남아 있던 `pending_user_question`을 fallback으로 사용합니다.

```python
explicit_session_id = str(session_id_value or "").strip()
message_session_id = _session_id_from_value(user_question_value)
```

- `explicit_session_id`: Langflow 입력칸에 직접 넣은 session id
- `message_session_id`: Chat Input 객체 metadata에서 찾은 session id

```python
session_id = str((explicit_session_id if explicit_session_id and explicit_session_id != "default" else "") or previous_state.get("session_id") or message_session_id or explicit_session_id or "default").strip()
```

session id 우선순위를 정하는 코드입니다.

1. 사용자가 명시적으로 넣은 값이 있고 `"default"`가 아니면 그 값을 씁니다.
2. 아니면 previous state의 session id를 씁니다.
3. 아니면 Chat Input metadata의 session id를 씁니다.
4. 그래도 없으면 `"default"`를 씁니다.

```python
state = {
    "session_id": session_id,
    "chat_history": [item for item in _as_list(previous_state.get("chat_history")) if isinstance(item, dict)],
    "context": deepcopy(previous_state.get("context")) if isinstance(previous_state.get("context"), dict) else {},
    "current_data": deepcopy(previous_state.get("current_data")) if isinstance(previous_state.get("current_data"), dict) else None,
    ...
}
```

이 block이 이번 턴의 표준 state를 만듭니다.

- `chat_history`: list이며 각 item이 dict인 것만 유지합니다.
- `context`: 이전 intent/filter 같은 맥락입니다.
- `current_data`: 후속 질문 분석에 필요한 이전 결과입니다.
- `deepcopy`: 원본 previous state를 실수로 수정하지 않기 위해 복사본을 만듭니다.

```python
"pending_user_question": user_question
```

이번 턴의 질문을 state 안에 저장합니다. 뒤의 prompt builder와 final answer builder가 이 값을 참고합니다.
