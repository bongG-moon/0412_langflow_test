# 08. Domain Patch Merger

## 역할

정규화된 patch를 기존 도메인에 병합한다.

`authoring_mode=create`이면 빈 도메인에서 시작하고, `append/update`이면 기존 도메인을 기반으로 병합한다.

## 입력

- `existing_domain`
- `normalized_domain_patch`
- `conflict_report`
- `authoring_config`

## 출력

`merged_domain`

```json
{
  "domain_document": {
    "domain_id": "manufacturing_default",
    "status": "draft",
    "metadata": {},
    "domain": {}
  },
  "merge_status": {
    "authoring_mode": "append",
    "merged": true,
    "is_saveable": true,
    "blocking_errors": [],
    "conflict_count": 0
  },
  "conflict_report": {}
}
```

## 주요 구현

- dict는 재귀 병합한다.
- list는 순서를 유지하며 중복 제거한다.
- `validate_only` 모드에서는 병합 결과는 만들지만 저장 가능 상태는 false로 둔다.
- 병합된 도메인은 `domain_document.domain`에만 담고, `merged_domain`/`domain_patch` 같은 큰 중복 필드는 생성하지 않는다.

## 다음 연결

```text
Domain Patch Merger.merged_domain -> Domain Schema Validator.merged_domain
```
