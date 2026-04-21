# 06. Normalize Intent With Domain

LLM이 만든 raw intent를 domain 지식 기준으로 보정하는 노드다.

## 새 기본 입력

```text
intent_raw
main_context
```

## Legacy 보조 입력

```text
domain_payload
agent_state
user_question
reference_date
```

새 구조에서는 `domain_payload`, `agent_state`, `user_question`을 직접 연결하지 않는다. `main_context` 안에 이미 들어 있다.

## 출력

```text
intent -> Data
```

출력 payload에는 정규화된 `intent`와 함께 `main_context`도 포함된다. 이 덕분에 뒤 노드들은 domain/state를 다시 연결하지 않아도 된다.

## 역할

- 제품명, 공정명, 특수 용어, metric alias를 domain index 기준으로 정규화한다.
- 오늘/어제 같은 날짜 표현을 실제 날짜 문자열로 변환한다.
- LLM이 놓친 명백한 dataset/metric/filter keyword를 domain 기준으로 보완한다.
- metric에 `required_datasets`가 있으면 intent에 붙인다.
- 후속 질문 판단에 필요한 cue를 보강한다.

## 권장 연결

```text
Parse Intent JSON.intent_raw
-> Normalize Intent With Domain.intent_raw

Main Flow Context Builder.main_context
-> Normalize Intent With Domain.main_context

Normalize Intent With Domain.intent
-> Request Type Router.intent
```
