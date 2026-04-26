# 25. State Memory Message Builder

## 한 줄 역할

`Final Answer Builder.next_state`를 Langflow Message History에 저장할 수 있는 message 형태로 바꾸는 노드입니다.

## 왜 필요한가

Langflow Message History는 보통 user/assistant 메시지를 저장합니다.
우리는 그 안에 다음 턴에서 사용할 state도 함께 저장해야 합니다.

그래서 이 노드는 state JSON 앞에 marker를 붙인 특별한 메시지를 만듭니다.
다음 턴의 `State Memory Extractor`가 그 marker를 찾아 다시 state를 읽습니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `next_state` | `Final Answer Builder.next_state` 출력입니다. |
| `memory_marker` | 상태 메시지임을 표시하는 문자열입니다. 기본값을 그대로 쓰면 됩니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `memory_message` | Message History Store에 넣을 message입니다. |
| `memory_payload` | 저장될 state payload를 확인하기 위한 Data 출력입니다. |

## 주요 함수 설명

- `_state_from_value`: next_state 입력에서 실제 state를 꺼냅니다.
- `_json_safe`: datetime 등 JSON 저장이 어려운 값을 안전한 값으로 바꿉니다.
- `build_state_memory_message`: marker + JSON 문자열 형태의 message를 만듭니다.

## 초보자 포인트

이 노드는 사용자에게 보이는 답변을 만드는 노드가 아닙니다.
후속 질문을 위해 Langflow 내부 기억을 저장하는 노드입니다.

Playground에서 후속 질문이 안 된다면 이 노드가 Message History Store에 연결되어 있는지 확인해야 합니다.

## 연결

```text
Final Answer Builder.next_state
-> State Memory Message Builder.next_state

State Memory Message Builder.memory_message
-> Message History (Store).message
```

다음 턴에서는 다시:

```text
Message History (Retrieve).messages
-> State Memory Extractor.memory_messages
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "next_state": {
    "state": {
      "session_id": "abc",
      "chat_history": [],
      "context": {
        "last_route": "post_analysis"
      },
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 150}
        ]
      }
    }
  },
  "memory_marker": "__MANUFACTURING_AGENT_STATE__"
}
```

### 출력 예시

`memory_message`:

```text
__MANUFACTURING_AGENT_STATE__
{"marker":"__MANUFACTURING_AGENT_STATE__","state":{"session_id":"abc","current_data":{"rows":[...]}},"state_json":"{\"session_id\":\"abc\",...}"}
```

`memory_payload`:

```json
{
  "memory_payload": {
    "marker": "__MANUFACTURING_AGENT_STATE__",
    "state": {
      "session_id": "abc",
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 150}
        ]
      }
    },
    "state_json": "{\"session_id\":\"abc\",...}"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_make_message` | memory text | Langflow Message | Message History Store에 저장할 수 있는 메시지 객체를 만듭니다. |
| `_state_from_value` | `{"state": {...}}` | state dict | Final Answer Builder의 next_state에서 실제 state만 꺼냅니다. |
| `_json_safe` | state dict | JSON 저장 가능한 dict | datetime/ObjectId 같은 값이 있어도 JSON 문자열로 만들 수 있게 합니다. |
| `build_state_memory_message` | next_state, marker | memory payload | marker가 붙은 state snapshot 메시지와 JSON payload를 만듭니다. |
| `_payload` | 없음 | cached memory payload | 두 output이 같은 계산을 공유하게 합니다. |
| `build_memory_message` | 없음 | Message | Message History Store에 연결하는 출력입니다. |
| `build_memory_payload` | 없음 | Data | 디버깅이나 API 저장용으로 볼 수 있는 구조화 출력입니다. |

### 코드 흐름

```text
Final Answer Builder.next_state 입력
-> state만 추출
-> JSON 안전 형태로 변환
-> marker 포함 memory text 생성
-> Message History Store에 저장할 Message 반환
```

### 초보자 포인트

이 노드는 Langflow 자체 Message History를 short-term memory처럼 쓰기 위한 마지막 단계입니다. 다음 질문 때 `00 State Memory Extractor`가 이 marker를 찾아 이전 state를 복원합니다.

## 함수 코드 단위 해석: `build_state_memory_message`

이 함수는 다음 턴에서 읽을 수 있는 state snapshot 메시지를 만듭니다.

### 함수 input

```json
{
  "next_state_value": {
    "state": {
      "session_id": "abc",
      "current_data": {
        "data": [{"MODE": "A", "production": 150}]
      }
    }
  },
  "marker_value": "__MANUFACTURING_AGENT_STATE__"
}
```

### 함수 output

```json
{
  "memory_text": "__MANUFACTURING_AGENT_STATE__\n{\"marker\":\"__MANUFACTURING_AGENT_STATE__\",\"state\":{\"session_id\":\"abc\"}}",
  "memory_payload": {
    "marker": "__MANUFACTURING_AGENT_STATE__",
    "state": {"session_id": "abc"},
    "state_json": "{\"session_id\":\"abc\"}"
  }
}
```

### 핵심 코드 해석

```python
state = _state_from_value(next_state_value)
```

Final Answer Builder가 만든 next_state에서 실제 state dict만 꺼냅니다.

```python
marker = str(marker_value or DEFAULT_MEMORY_MARKER).strip() or DEFAULT_MEMORY_MARKER
```

Message History에서 나중에 이 메시지를 찾기 위한 marker를 정합니다.

```python
safe_state = _json_safe(state)
```

state 안에 JSON으로 바로 저장하기 어려운 값이 있으면 문자열 등으로 바꿉니다.

```python
state_json = json.dumps(safe_state, ensure_ascii=False)
```

state를 JSON 문자열로 만듭니다. 한글이 깨져 보이지 않도록 `ensure_ascii=False`를 사용합니다.

```python
record = {
    "marker": marker,
    "state": safe_state,
    "state_json": state_json,
}
```

나중에 State Memory Extractor가 읽을 수 있는 record 구조를 만듭니다.

```python
memory_text = f"{marker}\n{json.dumps(record, ensure_ascii=False)}"
```

Langflow Message History에는 Message text로 저장해야 하므로 marker와 JSON record를 하나의 문자열로 합칩니다.
