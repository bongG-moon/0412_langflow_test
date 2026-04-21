# 04. Domain Item Prompt Context Builder

LLM prompt에 넣을 변수를 만든다.

입력:

```text
route_payload
existing_items
```

출력의 핵심은 `template_vars`다.

```json
{
  "template_vars": {
    "routes": "metrics, join_rules",
    "item_schemas": "{...}",
    "existing_items": "{...}",
    "raw_notes": "[...]",
    "output_schema": "{...}",
    "raw_text": "..."
  }
}
```

다음 연결:

```text
Domain Item Prompt Context Builder.prompt_context -> Domain Item Prompt Template.prompt_context
```
