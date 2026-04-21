# 06. Normalize Domain Patch

## 역할

LLM이 만든 domain patch를 Main Flow가 이해하는 표준 schema로 보정한다.

특히 기존 Streamlit 도메인 관리에서 쓰던 `dataset_keywords`, `value_groups`, `analysis_rules`, `join_rules` 형식도 변환한다.

## 입력

- `domain_patch`: Parse Domain Patch JSON output

## 출력

`normalized_domain_patch`

```json
{
  "normalized_domain_patch": {
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

## 변환 규칙

- `dataset_keywords` -> `datasets.<dataset_key>.keywords`
- `value_groups` 중 `process_name` -> `process_groups`
- `value_groups` 중 `product_name` -> `products`
- 그 외 `value_groups` -> `terms`
- `analysis_rules` -> `metrics`
- legacy `join_rules` -> 표준 `join_rules`

## 주요 구현

- dataset은 `display_name`, `keywords`, `required_params`, `columns`를 표준화한다.
- metric은 `aliases`, `required_datasets`, `required_columns`, `source_columns`, `default_group_by`를 list로 보정한다.
- alias와 keywords는 순서를 유지하며 중복 제거한다.

## 다음 연결

```text
Normalize Domain Patch.normalized_domain_patch -> Domain Conflict Detector.normalized_domain_patch
Normalize Domain Patch.normalized_domain_patch -> Domain Patch Merger.normalized_domain_patch
```
