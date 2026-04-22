# 07. Parse Domain Item JSON

커스텀 `Domain Item LLM API Caller` 출력에서 JSON을 추출한다.

지원 입력 형태:

```text
Data
Message
Text
JSON
```

출력:

```json
{
  "domain_items_raw": [],
  "unmapped_text": "",
  "parse_errors": [],
  "llm_text_chars": 0
}
```
