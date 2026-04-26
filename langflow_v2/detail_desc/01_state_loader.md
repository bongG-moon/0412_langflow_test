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

