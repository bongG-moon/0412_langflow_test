# 09. Domain Schema Validator

## 역할

병합된 도메인이 Main Data Answer Flow에서 사용할 수 있는 구조인지 검사한다.

## 입력

- `merged_domain`: Domain Patch Merger output

## 출력

`validated_domain`

```json
{
  "domain_document": {},
  "validation": {
    "errors": [],
    "warnings": [],
    "conflicts": []
  },
  "is_saveable": true,
  "merge_status": {}
}
```

## 검사 내용

- `products`, `process_groups`, `terms`, `datasets`, `metrics`, `join_rules` root key 존재 여부
- dataset columns의 `name`, `type`
- dataset `required_params`가 list인지 여부
- metric `required_datasets`와 `source_columns`
- join rule이 참조하는 dataset 존재 여부
- 검증된 도메인도 `domain_document.domain`에만 유지하고 `validated_domain` 중복 필드는 만들지 않는다.

## 다음 연결

```text
Domain Schema Validator.validated_domain -> Build Domain Review Prompt.validated_domain
Domain Schema Validator.validated_domain -> Domain Save Decision.validated_domain
Domain Schema Validator.validated_domain -> MongoDB Domain Fragment Saver.validated_domain
```
