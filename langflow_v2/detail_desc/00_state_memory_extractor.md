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

