# 05. Build Intent Prompt

## 한 줄 역할

사용자 질문, 이전 상태, domain, table catalog를 모아 intent 분류용 LLM prompt를 만드는 노드입니다.

## intent란?

intent는 "사용자가 지금 무엇을 원하는가"를 구조화한 정보입니다.

예를 들면 다음을 판단합니다.

- 새 데이터 조회가 필요한가?
- 이전 결과를 이어서 분석하는 질문인가?
- 어떤 dataset이 필요한가?
- 날짜 같은 필수 조건이 있는가?
- pandas 후처리가 필요한가?

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `state_payload` | `State Loader` 출력입니다. 현재 질문과 이전 상태가 들어 있습니다. |
| `domain_payload` | 도메인 규칙입니다. MongoDB 또는 JSON Loader 중 하나를 연결합니다. |
| `table_catalog_payload` | dataset/tool catalog입니다. |
| `reference_date` | 테스트용 기준 날짜입니다. 비우면 현재 날짜 기준으로 해석합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | LLM JSON Caller에 넘길 prompt와 관련 context입니다. |

## 주요 함수 설명

- `_unwrap_state`: `state_payload`에서 실제 state를 꺼냅니다.
- `_unwrap_domain`: `domain_payload`에서 domain만 꺼냅니다.
- `_unwrap_catalog`: table catalog를 꺼냅니다.
- `_current_data_summary`: 이전 결과가 있을 때 row 수, 컬럼 등을 요약합니다.
- `build_intent_prompt`: LLM에게 보낼 instruction과 JSON schema를 만듭니다.

## 초보자 포인트

이 노드는 LLM을 호출하지 않습니다.
LLM이 읽을 prompt 문자열만 만듭니다.

즉, 역할은 "질문지를 잘 작성하는 노드"입니다.
실제 답안 작성은 다음 노드인 `LLM JSON Caller`가 합니다.

## 연결

```text
State Loader.state_payload
-> Build Intent Prompt.state_payload

Domain Loader.domain_payload
-> Build Intent Prompt.domain_payload

Table Catalog Loader.table_catalog_payload
-> Build Intent Prompt.table_catalog_payload

Build Intent Prompt.prompt_payload
-> LLM JSON Caller (Intent).prompt_payload
```

