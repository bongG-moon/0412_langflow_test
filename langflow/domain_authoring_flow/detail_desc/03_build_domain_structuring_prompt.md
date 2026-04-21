# 03. Build Domain Structuring Prompt

## 역할

사용자 원문, 기존 도메인, authoring config를 모아 LLM에게 보낼 prompt를 만든다.

이 prompt는 LLM이 제품, 공정 그룹, 필터 조건, 데이터셋, 수식 metric, join rule을 구분해서 `domain_patch` JSON으로 반환하도록 지시한다.

## 입력

- `raw_domain_payload`: 원문 도메인 설명
- `existing_domain`: 기존 도메인 구조
- `authoring_config`: 생성/수정 설정

## 출력

`domain_structuring_prompt`

```json
{
  "prompt": "You are converting manufacturing domain knowledge..."
}
```

## LLM에게 요구하는 결과

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
  "warnings": []
}
```

## 주요 구현

- `_existing_domain_summary()`는 기존 도메인 전체가 아니라 key 목록만 prompt에 넣는다.
- prompt 안에는 최소 Domain JSON patch skeleton과 짧은 mapping rule만 넣는다.
- `domain_index`는 만들지 말라고 명시한다. `domain_index`는 Main Flow의 `Domain JSON Loader`가 자동 생성한다.
- 출력 payload에는 실제 LLM 호출에 필요한 `prompt` key만 넣는다.

## 다음 연결

```text
Build Domain Structuring Prompt.domain_structuring_prompt -> Domain Authoring LLM JSON Caller.prompt
```
