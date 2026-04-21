# 13. Domain Save Decision

## 역할

규칙 기반 충돌 검증, schema 검증, LLM semantic review 결과를 보고 MongoDB에 저장할지, 저장한다면 어떤 상태로 저장할지 정한다.

## 입력

- `conflict_report`: Domain Conflict Detector output
- `validated_domain`: Domain Schema Validator output
- `semantic_review`: Parse Domain Review JSON output
- `authoring_config`: 선택. 연결하지 않으면 기본값을 사용한다.

## 저장 규칙

| 조건 | 결정 |
| --- | --- |
| validation error 또는 blocking error 있음 | 저장하지 않음 |
| rule conflict 또는 semantic conflict 있음 | `review_required`로 저장 |
| semantic review가 `rejected` 권고 | 저장하지 않음 |
| error/conflict 없음 | `active`로 저장 |
| `authoring_mode=validate_only` | 저장하지 않음 |

`review_required`는 MongoDB에는 남지만 Main Flow에서는 사용하지 않는다. Main Flow loader는 `active` fragment만 불러온다.

## 출력

`save_decision`

```json
{
  "save_decision": {
    "should_save": true,
    "target_status": "active",
    "needs_review": false,
    "reason": "no blocking conflicts",
    "error_count": 0,
    "warning_count": 0,
    "conflict_count": 0,
    "errors": [],
    "warnings": [],
    "conflicts": [],
    "semantic_conflicts": [],
    "semantic_review": {}
  }
}
```

## 다음 연결

```text
Parse Domain Review JSON.semantic_review -> Domain Save Decision.semantic_review
Domain Save Decision.save_decision -> MongoDB Domain Fragment Saver.save_decision
```
