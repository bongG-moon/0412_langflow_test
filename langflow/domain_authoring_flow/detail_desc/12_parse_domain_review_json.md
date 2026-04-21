# 12. Parse Domain Review JSON

## 역할

LLM semantic review 응답을 저장 판단에서 사용할 수 있는 `semantic_review` payload로 정리한다.

LLM 응답이 비어 있거나 JSON parsing에 실패하면 안전하게 `recommended_status=review_required`로 보정한다.

## 입력

- `llm_result`: Domain Review LLM Caller output

## 출력

`semantic_review`

```json
{
  "semantic_review": {
    "semantic_conflicts": [],
    "semantic_warnings": [],
    "recommended_status": "active",
    "confidence": 0.0,
    "parse_errors": []
  }
}
```

## 다음 연결

```text
Parse Domain Review JSON.semantic_review -> Domain Save Decision.semantic_review
```
