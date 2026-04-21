# 03. Build Intent Prompt

사용자 질문과 domain/state 정보를 LLM이 읽을 수 있는 intent 추출 prompt로 만드는 노드다.

## 새 기본 입력

```text
template
main_context
```

## Legacy 보조 입력

```text
user_question
agent_state
domain_payload
```

위 세 입력은 이전 구조와 직접 테스트를 위해 남겨둔 값이다. 새 flow에서는 `Main Flow Context Builder.main_context`만 연결하면 된다.

## 출력

```text
prompt        -> Message
intent_prompt -> Data
```

`prompt`는 Langflow built-in LLM에 연결하기 위한 Message output이다.

`intent_prompt`는 `04 LLM JSON Caller`를 직접 사용할 때를 위한 legacy/custom LLM 경로다.

## 역할

- `main_context.user_question`을 읽는다.
- `main_context.agent_state`에서 최근 대화, 이전 context, current_data 요약을 읽는다.
- `main_context.domain_payload`에서 dataset, metric, alias index 정보를 읽는다.
- LLM이 JSON intent만 반환하도록 schema와 지시사항을 포함한 prompt를 만든다.

## 권장 연결

```text
Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Build Intent Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Parse Intent JSON.llm_result
```

## Legacy 연결

```text
Build Intent Prompt.intent_prompt
-> LLM JSON Caller.prompt

LLM JSON Caller.llm_result
-> Parse Intent JSON.llm_result
```
