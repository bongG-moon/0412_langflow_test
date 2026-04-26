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

