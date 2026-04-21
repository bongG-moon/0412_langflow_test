# 05. Parse Domain Patch JSON

## 역할

LLM 응답 문자열에서 JSON을 파싱해 `domain_patch` payload로 만든다.

LLM이 markdown fence를 붙이거나, `domain_patch` 대신 `domain`을 반환해도 가능한 범위에서 처리한다.

## 입력

- `llm_result`: Domain Authoring LLM JSON Caller output

## 출력

`domain_patch`

```json
{
  "domain_patch": {
    "products": {},
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  },
  "warnings": [],
  "parse_errors": []
}
```

## 주요 구현

- `_parse_json_block()`은 ```json fenced block과 본문 속 첫 JSON object를 모두 처리한다.
- LLM이 full domain document를 반환하면 그 안의 `domain`을 patch로 사용한다.
- Streamlit식 legacy 필드가 들어온 경우도 `domain_patch` 안에 담아 다음 Normalize 노드가 변환할 수 있게 한다.
- LLM 토큰을 줄이기 위해 classification log나 assumptions는 더 이상 표준 출력으로 요구하지 않는다.

## 다음 연결

```text
Parse Domain Patch JSON.domain_patch -> Normalize Domain Patch.domain_patch
```
