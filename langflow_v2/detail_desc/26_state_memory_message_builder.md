# 26. State Memory Message Builder

## 이 노드 역할

`Final Answer Builder.next_state`를 Langflow Message History에 저장할 수 있는 memory message로 바꾸는 노드입니다.

다음 턴에서 `State Memory Extractor`가 이 message를 찾아 이전 대화 상태를 복원할 수 있게 합니다.

## 왜 필요한가

Langflow canvas에서는 일반적으로 다음 실행으로 Python dict 상태가 자동 전달되지 않습니다. 그래서 state를 message 형태로 저장해 두고, 다음 질문이 들어올 때 다시 읽어야 합니다.

이 노드는 상태 dict를 JSON 문자열로 감싸고, 찾기 쉬운 marker를 붙여 memory에 넣을 수 있는 형태로 만듭니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `next_state` | `Final Answer Builder.next_state` 출력입니다. |
| `memory_marker` | memory에서 state message를 식별할 marker입니다. 기본값은 `__LANGFLOW_V2_AGENT_STATE__`입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `memory_message` | Message History에 저장할 Message 객체입니다. |
| `memory_payload` | 디버깅과 확인용 Data payload입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_state_from_value` | 입력값에서 state dict를 꺼냅니다. |
| `_json_safe` | JSON 직렬화 가능한 값으로 정리합니다. |
| `build_state_memory_message` | marker와 state를 포함한 memory record를 만듭니다. |

## 초보자 확인용

이 노드는 사용자에게 보이는 답변을 만들지 않습니다. 다음 질문에서 이전 조건과 데이터를 이어받을 수 있도록 상태를 보관하는 역할입니다.

예를 들어 사용자가 "그중 상위 5개만 보여줘"라고 물었을 때, 이전 질문의 날짜, 공정, mode, current_data를 복원하는 기반이 됩니다.

## 연결

```text
Final Answer Builder.next_state
-> State Memory Message Builder.next_state

State Memory Message Builder.memory_message
-> Message History 또는 memory 저장 노드
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "state": {
    "session_id": "demo-session",
    "chat_history": [
      {"role": "user", "content": "오늘 DA공정 DDR5 생산 보여줘"}
    ],
    "context": {
      "last_required_params": {"date": "20260426"},
      "last_filters": {"mode": ["DDR5"]}
    },
    "current_data": {
      "data": [{"MODE": "DDR5", "production": 100}]
    }
  }
}
```

### 출력 예시

```json
{
  "memory_payload": {
    "marker": "__LANGFLOW_V2_AGENT_STATE__",
    "type": "langflow_v2_agent_state",
    "version": 1,
    "session_id": "demo-session",
    "chat_turns": 1,
    "has_current_data": true,
    "state": {
      "session_id": "demo-session"
    }
  },
  "memory_text": "{\"marker\":\"__LANGFLOW_V2_AGENT_STATE__\",...}"
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_state_from_value` | `{"state": {...}}` | state dict | 여러 가능한 wrapper에서 state를 찾습니다. |
| `_json_safe` | state dict | JSON-safe dict | datetime 등 직렬화 어려운 값을 문자열로 바꿉니다. |
| `build_state_memory_message` | next_state, marker | memory payload | 저장용 record와 text를 만듭니다. |

### 코드 흐름

```text
next_state 입력
-> state dict 추출
-> marker, type, version, saved_at 추가
-> memory_text JSON 생성
-> memory_message와 memory_payload 출력
```

## 함수 코드 단위 해석: `build_state_memory_message`

### 함수 input

```json
{
  "next_state": {
    "state": {
      "session_id": "demo-session",
      "chat_history": [],
      "current_data": {"data": [{"production": 100}]}
    }
  },
  "marker": "__LANGFLOW_V2_AGENT_STATE__"
}
```

### 함수 output

```json
{
  "memory_payload": {
    "marker": "__LANGFLOW_V2_AGENT_STATE__",
    "type": "langflow_v2_agent_state",
    "version": 1,
    "session_id": "demo-session",
    "has_current_data": true
  },
  "state_json": "{\"session_id\":\"demo-session\",...}"
}
```

### 핵심 코드 해석

```python
marker = str(marker_value or DEFAULT_MEMORY_MARKER).strip() or DEFAULT_MEMORY_MARKER
```

입력 marker가 비어 있으면 기본 marker를 사용합니다.

```python
state = _json_safe(_state_from_value(next_state_value))
```

입력값에서 state를 꺼내 JSON 저장 가능한 형태로 정리합니다.

```python
record = {
    "marker": marker,
    "type": "langflow_v2_agent_state",
    "version": 1,
    "saved_at": datetime.now(timezone.utc).isoformat(),
    "session_id": state.get("session_id", "default"),
    "chat_turns": len(state.get("chat_history", [])),
    "has_current_data": isinstance(state.get("current_data"), dict) and bool(state.get("current_data")),
    "state": state,
}
```

다음 턴에서 찾고 해석할 수 있는 memory record를 구성합니다.

```python
text = json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str)
```

Message History에 저장할 JSON 문자열을 만듭니다.

```python
return {
    "memory_payload": record,
    "memory_text": text,
    "state": state,
    "state_json": json.dumps(state, ensure_ascii=False, default=str),
}
```

Message 출력과 디버깅용 Data 출력이 모두 사용할 수 있도록 record와 문자열을 함께 반환합니다.

## 추가 함수 코드 단위 해석: `_state_from_value`

`Final Answer Builder.next_state`가 어떤 wrapper로 들어오더라도 실제 state dict를 꺼내는 함수입니다.

```python
payload = _payload_from_value(value)
state = payload.get("state") or payload.get("next_state") or payload.get("agent_state")
```

가능한 state key 이름을 순서대로 확인합니다.

```python
if isinstance(state, dict):
    return deepcopy(state)
```

dict state를 찾으면 복사해서 반환합니다.

```python
state_json = payload.get("state_json")
if isinstance(state_json, str):
    parsed = json.loads(state_json)
    return parsed if isinstance(parsed, dict) else {}
```

state가 JSON 문자열로만 들어온 경우 다시 dict로 복원합니다.

```python
return deepcopy(payload) if payload.get("chat_history") or payload.get("current_data") else {}
```

payload 자체가 state처럼 생긴 경우도 허용합니다. `chat_history`나 `current_data`가 있으면 state로 볼 수 있습니다.

## 추가 함수 코드 단위 해석: `build_state_memory_message`의 record 구성

```python
record = {
    "marker": marker,
    "type": "langflow_v2_agent_state",
    "version": 1,
    "saved_at": datetime.now(timezone.utc).isoformat(),
```

Message History에서 다시 찾을 수 있도록 marker와 type/version을 붙이고 저장 시각을 남깁니다.

```python
"session_id": state.get("session_id", "default"),
"chat_turns": len(state.get("chat_history", [])) if isinstance(state.get("chat_history"), list) else 0,
"has_current_data": isinstance(state.get("current_data"), dict) and bool(state.get("current_data")),
```

디버깅하기 쉬운 요약 metadata를 record 최상위에 둡니다.

```python
"state": state,
```

실제 다음 턴 복원에 필요한 전체 state는 `state` key 안에 저장합니다.

```python
text = json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str)
```

Message History에 저장할 compact JSON 문자열을 만듭니다. `ensure_ascii=False`라 한글도 그대로 보존됩니다.
