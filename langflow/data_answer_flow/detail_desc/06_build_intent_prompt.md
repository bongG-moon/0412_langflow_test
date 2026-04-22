# 06. Build Intent Prompt

사용자 질문을 LLM이 구조화된 intent JSON으로 바꾸도록 prompt를 만드는 노드다.

## 입력

```text
template
main_context
user_question
agent_state
domain_payload
```

`main_context`가 권장 입력이다. 나머지는 legacy/direct test용 advanced 입력이다.

## 출력

```text
prompt
prompt_payload
```

권장 연결은 `prompt_payload`다.

```text
Build Intent Prompt.prompt_payload
-> LLM API Caller.prompt
```

## prompt_payload 구조

```json
{
  "prompt": "...",
  "prompt_type": "intent"
}
```

`prompt_type="intent"` 덕분에 `LLM API Caller.response_mode=auto`에서 JSON 응답 모드로 동작한다.

## Domain 사용 방식

이 노드는 전체 domain을 그대로 prompt에 넣지 않는다.

우선순위:

1. `main_context.domain_prompt_context`
2. `domain_payload.domain_prompt_context`
3. `domain + domain_index`로 만든 fallback 요약

이 요약에는 dataset keyword, metric formula, alias index, product/process/term 요약만 들어간다.

## Table Catalog 사용 방식

`main_context.table_catalog_prompt_context`가 있으면 prompt에 함께 넣는다.

table catalog prompt context에는 다음 정보만 들어간다.

- dataset display name
- description
- keywords
- question examples
- required params
- tool name
- 주요 column 이름/type/description

실제 SQL, table name, db_key는 prompt에 넣지 않는다.

## 어떤 질문에 어떤 데이터가 필요한지

질문과 dataset 후보의 직접 연결은 table catalog의 `keywords`, `question_examples`가 맡는다.

계산 metric과 dataset의 관계는 domain의 `metrics.required_datasets`가 맡는다.

예를 들어 “생산 달성율”은 domain metric에서 `production`, `target`이 필요하다고 알려주고, table catalog가 두 dataset의 tool/required parameter/SQL 정보를 제공한다.

## LLM이 반환해야 하는 주요 intent

```json
{
  "request_type": "data_question",
  "dataset_hints": ["production"],
  "metric_hints": ["production_qty"],
  "required_params": {
    "date": "2026-04-22"
  },
  "filters": {
    "product": "A"
  },
  "group_by": [],
  "sort": {
    "column_or_metric": "",
    "direction": "desc"
  },
  "top_n": null,
  "confidence": 0.9
}
```
