# 00. State Memory Extractor

## 한 줄 역할

Langflow Message History에 저장된 이전 대화 상태를 찾아서 `previous_state`로 꺼내는 노드입니다.

## 왜 필요한가

사용자가 두 번째 질문에서 `이때 가장 생산량이 많았던 MODE 알려줘`처럼 말하면, Agent는 이전 질문의 결과 데이터를 기억해야 합니다.

Langflow의 Playground는 대화 메시지를 저장할 수 있지만, 그 안에서 우리가 필요한 `current_data`, `chat_history`, `context`를 직접 꺼내야 합니다. 이 노드가 그 일을 합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `memory_messages` | Langflow Message History의 Retrieve 출력입니다. 이전 대화 메시지 목록이 들어옵니다. |
| `memory_marker` | 우리가 저장한 상태 메시지를 찾기 위한 표시 문자열입니다. 기본값을 그대로 쓰면 됩니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `previous_state` | 이전 상태를 담은 payload입니다. 다음 노드인 `State Loader.previous_state`로 연결합니다. |

출력 예시는 다음과 같습니다.

```json
{
  "previous_state": {
    "state": {
      "chat_history": [],
      "context": {},
      "current_data": {}
    },
    "state_json": "{...}"
  },
  "memory_loaded": true
}
```

## 주요 함수 설명

- `_collect_texts`: Message History 출력이 어떤 모양이든 문자열을 최대한 찾아냅니다.
- `_json_objects_from_text`: 문자열 안에서 JSON object 후보를 찾습니다.
- `_state_from_record`: JSON 안에서 `state`, `next_state`, `current_data` 같은 실제 상태를 골라냅니다.
- `extract_previous_state`: 전체 작업을 조합해서 가장 최근 상태를 반환합니다.

## 초보자 포인트

이 노드는 데이터 조회를 하지 않습니다. 단지 이전 대화에 저장된 상태를 읽는 역할입니다.

`memory_loaded`가 `false`라면 보통 다음 중 하나입니다.

- Message History Retrieve 노드가 연결되지 않음
- 이전 턴에서 State Memory Message Builder가 저장되지 않음
- Playground에서 새 세션으로 질문함

## 연결

```text
Message History (Retrieve).messages
-> State Memory Extractor.memory_messages

State Memory Extractor.previous_state
-> State Loader.previous_state
```

## Python 코드 상세 해석

### 입력 예시

Langflow Message History가 이전 턴 메시지를 다음처럼 넘긴다고 생각하면 됩니다.

```json
{
  "messages": [
    {
      "text": "일반 답변 메시지"
    },
    {
      "text": "{\"marker\":\"__MANUFACTURING_AGENT_STATE__\",\"state\":{\"session_id\":\"abc\",\"current_data\":{\"rows\":[{\"MODE\":\"A\",\"production\":10}]}}}"
    }
  ]
}
```

### 출력 예시

```json
{
  "previous_state": {
    "state": {
      "session_id": "abc",
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 10}
        ]
      }
    },
    "state_json": "{\"session_id\":\"abc\",\"current_data\":{\"rows\":[...]}}"
  },
  "memory_loaded": true,
  "memory_message_count": 2,
  "memory_record_count": 1,
  "memory_errors": []
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"messages": [...]})` | `{"messages": [...]}` | Langflow 값은 `Data`, dict, Message처럼 여러 형태로 들어올 수 있어서 먼저 dict로 통일합니다. |
| `_text_from_value` | `{"text": "hello"}` | `"hello"` | Message 객체나 dict에서 실제 텍스트만 꺼냅니다. |
| `_collect_texts` | `{"messages": [{"text": "a"}, {"text": "b"}]}` | `["a", "b"]` | Message History 출력 구조가 중첩될 수 있으므로 안쪽 텍스트까지 모두 모읍니다. |
| `_json_objects_from_text` | `"prefix {\"marker\":\"x\"}"` | `[{"marker": "x"}]` | 메시지 안에 JSON만 딱 들어있는 것이 아니라 앞뒤 문장이 섞여도 JSON 부분을 찾아냅니다. |
| `_state_from_record` | `{"state": {"session_id": "abc"}}` | `{"session_id": "abc"}` | memory message 안에서 실제 agent state만 꺼냅니다. |
| `extract_previous_state` | `memory_messages`, `marker` | `previous_state` payload | 뒤에서부터 최신 메시지를 훑으며 marker가 붙은 state를 찾습니다. |
| `build_previous_state` | Langflow input `memory_messages` | `Data(data=payload)` | Langflow가 호출하는 실제 output method입니다. 내부에서 `extract_previous_state`를 실행합니다. |

### 코드 흐름

```text
Message History 출력
-> _collect_texts로 모든 텍스트 수집
-> 뒤에서부터 marker 포함 메시지 검색
-> _json_objects_from_text로 JSON record 추출
-> _state_from_record로 state 추출
-> State Loader가 읽을 previous_state payload 생성
```

### 초보자 포인트

이 노드는 "기억을 만드는 노드"가 아니라 "이전 기억을 찾는 노드"입니다. 저장은 마지막 `26 State Memory Message Builder`와 Langflow Message History Store가 담당합니다.

## 함수 코드 단위 해석: `extract_previous_state`

이 함수는 Message History 안에서 가장 최근 state snapshot을 찾습니다.

### 함수 input

```json
{
  "memory_messages_value": [
    {"text": "일반 답변"},
    {"text": "__MANUFACTURING_AGENT_STATE__ {\"marker\":\"__MANUFACTURING_AGENT_STATE__\",\"state\":{\"session_id\":\"abc\"}}"}
  ],
  "marker_value": "__MANUFACTURING_AGENT_STATE__"
}
```

### 함수 output

```json
{
  "previous_state": {
    "state": {"session_id": "abc"},
    "state_json": "{\"session_id\":\"abc\"}"
  },
  "memory_loaded": true,
  "memory_message_count": 2,
  "memory_record_count": 1,
  "memory_errors": []
}
```

### 핵심 코드 해석

```python
marker = str(marker_value or DEFAULT_MEMORY_MARKER).strip() or DEFAULT_MEMORY_MARKER
texts = _collect_texts(memory_messages_value)
errors: list[str] = []
selected: Dict[str, Any] = {}
scanned_records = 0
```

- `marker`: state 메시지를 일반 채팅 메시지와 구분하는 표식입니다.
- `_collect_texts(...)`: Message History 결과가 list, dict, Message 객체처럼 여러 형태일 수 있어서 모든 텍스트를 list로 모읍니다.
- `selected`: 최종으로 선택된 최신 state를 담을 변수입니다.
- `scanned_records`: marker가 붙은 JSON record를 몇 개 찾았는지 세기 위한 값입니다.

```python
for text in reversed(texts):
```

`reversed`를 쓰는 이유는 가장 최근 메시지부터 확인하기 위해서입니다. memory에는 예전 state도 남아 있을 수 있으므로 최신 state를 먼저 찾습니다.

```python
if marker not in text:
    continue
```

현재 text에 marker가 없으면 state 메시지가 아닙니다. `continue`로 다음 text 검사로 넘어갑니다.

```python
records = [record for record in _json_objects_from_text(text) if record.get("marker") == marker]
```

텍스트 안에서 JSON 객체를 모두 찾아낸 뒤, 그중 marker가 같은 record만 남깁니다.

```python
state = _state_from_record(record)
if state:
    selected = {
        "state": state,
        "state_json": json.dumps(state, ensure_ascii=False),
        "memory_record": record,
    }
    break
```

record 안에서 실제 state를 꺼냅니다. state가 있으면 선택하고 반복을 멈춥니다. `ensure_ascii=False`는 한글이 `\uAC00` 같은 형태로 깨져 보이지 않게 하기 위한 옵션입니다.

```python
if not selected:
    selected = {"state": {}, "state_json": "", "memory_record": {}}
```

이전 state를 찾지 못해도 뒤 노드가 깨지지 않도록 빈 state를 만들어 반환합니다.
