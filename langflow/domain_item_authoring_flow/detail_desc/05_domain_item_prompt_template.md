# 05. Domain Item Prompt Template

`template_vars`를 prompt 문자열로 조합한다.

이 노드는 Langflow 기본 Prompt Template 노드로 대체할 수 있다. 기본 Prompt Template을 쓸 때도 `{routes}`, `{item_schemas}`, `{existing_items}`, `{raw_notes}`, `{output_schema}`, `{raw_text}` 변수를 유지하면 된다.

출력:

```text
prompt         -> Message 타입. prompt 미리보기 또는 호환용
prompt_payload -> Data 타입. Domain Item LLM API Caller에 연결
```

다음 연결:

```text
Domain Item Prompt Template.prompt_payload
-> Domain Item LLM API Caller.prompt
```
