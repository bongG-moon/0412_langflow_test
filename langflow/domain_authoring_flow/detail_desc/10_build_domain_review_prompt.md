# 10. Build Domain Review Prompt

## 역할

기존 active 도메인과 이번에 생성된 domain patch를 비교할 수 있도록 LLM semantic review prompt를 만든다.

이 노드는 전체 원문을 다시 넣지 않는다. 비용을 줄이기 위해 기존 도메인과 신규 patch의 제품, 공정, 용어, 데이터셋, metric, join rule 요약만 넣는다.

## 입력

- `existing_domain`: MongoDB Active Domain Loader output
- `normalized_domain_patch`: Normalize Domain Patch output
- `conflict_report`: Domain Conflict Detector output
- `validated_domain`: Domain Schema Validator output

## 출력

`review_prompt`

```json
{
  "prompt": "You are reviewing manufacturing domain changes..."
}
```

## LLM에게 요구하는 결과

```json
{
  "semantic_review": {
    "semantic_conflicts": [],
    "semantic_warnings": [],
    "recommended_status": "active",
    "confidence": 0.0
  }
}
```

## 다음 연결

```text
Build Domain Review Prompt.review_prompt -> Domain Review LLM Caller.prompt
```
