# 05. Main Flow Context Builder

사용자 질문, session state, domain payload를 하나의 `main_context`로 묶는 노드다.

## 입력

```text
user_question
agent_state
domain_payload
reference_date
```

## 출력

```text
main_context
```

## 역할

이 노드를 둔 이유는 canvas 연결을 단순하게 만들기 위해서다.

예전 방식처럼 `domain_payload`, `domain_index`, `agent_state`, `user_question`을 뒤 노드마다 반복 연결하지 않는다.

```text
Session State Loader.agent_state
-> Main Flow Context Builder.agent_state

MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload

User Question
-> Main Flow Context Builder.user_question
```

그 다음부터는 아래처럼 `main_context` 하나를 우선 연결한다.

```text
Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Main Flow Context Builder.main_context
-> Normalize Intent With Domain.main_context
```

## 반환 예시

```json
{
  "main_context": {
    "user_question": "오늘 A제품 생산량 알려줘",
    "reference_date": "",
    "agent_state": {},
    "domain_payload": {},
    "domain": {},
    "domain_index": {},
    "domain_prompt_context": {},
    "domain_errors": [],
    "mongo_domain_load_status": {}
  },
  "user_question": "오늘 A제품 생산량 알려줘",
  "agent_state": {},
  "domain_payload": {},
  "domain": {},
  "domain_index": {},
  "domain_prompt_context": {}
}
```

## domain_prompt_context

`domain_payload`에 `domain_prompt_context`가 있으면 그대로 전달한다.

없으면 `domain`과 `domain_index`를 바탕으로 fallback 요약을 만든다.

이 값은 `Build Intent Prompt`와 같은 LLM prompt 노드에서 token 사용량을 줄이는 데 사용된다.

## table catalog 연결 위치

Table catalog는 `main_context`에 넣지 않는다. 모든 질문에서 필요하지 않은 table/source metadata를 첫 prompt부터 싣지 않기 위해서다.

`Table Catalog Loader.table_catalog_payload`는 후단의 `Retrieval Plan Builder.table_catalog_payload`와 `OracleDB Data Retriever.table_catalog_payload`에 직접 연결한다.
