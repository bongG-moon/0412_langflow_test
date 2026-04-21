# 02. Main Flow Context Builder

`Main Flow Context Builder`는 main flow 초반에서 사용자 질문, session state, domain payload를 하나의 `main_context`로 묶는 노드다.

이 노드를 추가한 이유는 `MongoDB Domain Item Payload Loader.domain_payload`를 여러 노드에 직접 연결하면 canvas 선이 너무 많아지기 때문이다. 이제 domain은 이 노드에 한 번만 연결하고, 이후 노드들은 `main_context`를 읽거나 앞 노드 payload 안에 포함된 `main_context`를 이어받는다.

## 입력

```text
user_question
agent_state
domain_payload
reference_date
```

## 출력

```text
main_context -> Data
```

## 출력 payload

```json
{
  "main_context": {
    "user_question": "오늘 A제품 생산량 알려줘",
    "reference_date": "",
    "agent_state": {
      "turn_id": 1,
      "chat_history": [],
      "current_data": null
    },
    "domain_payload": {
      "domain": {},
      "domain_index": {},
      "domain_errors": []
    },
    "domain": {},
    "domain_index": {},
    "domain_errors": [],
    "mongo_domain_load_status": {}
  },
  "user_question": "오늘 A제품 생산량 알려줘",
  "agent_state": {},
  "domain_payload": {},
  "domain": {},
  "domain_index": {}
}
```

## 역할

- 사용자 질문을 문자열로 정리한다.
- `Session State Loader.agent_state`를 표준 dict로 정리한다.
- `MongoDB Domain Item Payload Loader.domain_payload` 안의 `domain`, `domain_index`, `domain_errors`를 한곳에 모은다.
- 뒤 노드들이 domain/state/question을 매번 따로 연결하지 않아도 되도록 `main_context`라는 공통 묶음을 만든다.

## 권장 연결

```text
Session State Loader.agent_state
-> Main Flow Context Builder.agent_state

MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload

사용자 질문 입력
-> Main Flow Context Builder.user_question

Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Main Flow Context Builder.main_context
-> Normalize Intent With Domain.main_context
```

`Normalize Intent With Domain` 이후에는 `main_context`가 payload 안에 같이 전달되므로, 뒤쪽 노드에 `domain_payload`를 다시 연결하지 않는 것이 새 기본 방식이다.
