# Domain Authoring Flow

> Legacy note: 새 권장 방식은 `langflow/domain_item_authoring_flow`이다. 이 폴더는 큰 domain patch fragment를 저장하는 기존 방식으로 보존한다.

이 폴더는 사용자가 입력한 제조 도메인 설명을 Main Data Answer Flow에서 사용할 수 있는 MongoDB domain fragment로 바꾸는 Langflow custom component 모음이다.

기본 권장 방식은 MongoDB fragment 저장 방식이다. 사용자가 도메인 원문을 조금씩 입력하면 새 도메인 조각을 만들고, 기존 active 조각과 충돌 검증한 뒤 `manufacturing_domain_fragments` collection에 저장한다.

Main Flow는 `active` 상태 fragment만 한 번에 불러와 병합해서 사용한다. 충돌이 있는 fragment는 `review_required`로 저장되며 Main Flow에는 자동 반영되지 않는다.

## Flow Order

```text
00_raw_domain_input.py
01_domain_authoring_config_input.py
02_mongodb_active_domain_loader.py
03_build_domain_structuring_prompt.py
04_llm_json_caller.py
05_parse_domain_patch_json.py
06_normalize_domain_patch.py
07_domain_conflict_detector.py
08_domain_patch_merger.py
09_domain_schema_validator.py
10_build_domain_review_prompt.py
11_domain_review_llm_caller.py
12_parse_domain_review_json.py
13_domain_save_decision.py
14_mongodb_domain_fragment_saver.py
```

중간 payload는 가능한 작게 유지한다. 기존 도메인은 `existing_domain_document.domain`, 병합/검증 도메인은 `domain_document.domain`에 한 번만 담고, `existing_domain`, `merged_domain`, `validated_domain` 같은 중복 payload key는 만들지 않는다.

## MongoDB Storage Wiring

| From | To | Required |
| --- | --- | --- |
| `Raw Domain Input.raw_domain_payload` | `Build Domain Structuring Prompt.raw_domain_payload` | Yes |
| `MongoDB Active Domain Loader.existing_domain` | `Build Domain Structuring Prompt.existing_domain` | Yes |
| `MongoDB Active Domain Loader.existing_domain` | `Domain Conflict Detector.existing_domain` | Yes |
| `MongoDB Active Domain Loader.existing_domain` | `Domain Patch Merger.existing_domain` | Yes |
| `Build Domain Structuring Prompt.domain_structuring_prompt` | `Domain Authoring LLM JSON Caller.prompt` | Yes |
| `Domain Authoring LLM JSON Caller.llm_result` | `Parse Domain Patch JSON.llm_result` | Yes |
| `Parse Domain Patch JSON.domain_patch` | `Normalize Domain Patch.domain_patch` | Yes |
| `Normalize Domain Patch.normalized_domain_patch` | `Domain Conflict Detector.normalized_domain_patch` | Yes |
| `Normalize Domain Patch.normalized_domain_patch` | `Domain Patch Merger.normalized_domain_patch` | Yes |
| `Domain Conflict Detector.conflict_report` | `Domain Patch Merger.conflict_report` | Yes |
| `Domain Patch Merger.merged_domain` | `Domain Schema Validator.merged_domain` | Yes |
| `MongoDB Active Domain Loader.existing_domain` | `Build Domain Review Prompt.existing_domain` | Yes |
| `Normalize Domain Patch.normalized_domain_patch` | `Build Domain Review Prompt.normalized_domain_patch` | Yes |
| `Domain Conflict Detector.conflict_report` | `Build Domain Review Prompt.conflict_report` | Yes |
| `Domain Schema Validator.validated_domain` | `Build Domain Review Prompt.validated_domain` | Yes |
| `Build Domain Review Prompt.review_prompt` | `Domain Review LLM Caller.prompt` | Yes |
| `Domain Review LLM Caller.llm_result` | `Parse Domain Review JSON.llm_result` | Yes |
| `Domain Conflict Detector.conflict_report` | `Domain Save Decision.conflict_report` | Yes |
| `Domain Schema Validator.validated_domain` | `Domain Save Decision.validated_domain` | Yes |
| `Parse Domain Review JSON.semantic_review` | `Domain Save Decision.semantic_review` | Yes |
| `Normalize Domain Patch.normalized_domain_patch` | `MongoDB Domain Fragment Saver.normalized_domain_patch` | Yes |
| `Domain Save Decision.save_decision` | `MongoDB Domain Fragment Saver.save_decision` | Yes |
| `Domain Schema Validator.validated_domain` | `MongoDB Domain Fragment Saver.validated_domain` | Yes |

Compact chain:

```text
MongoDB Active Domain Loader
  -> Build Domain Structuring Prompt.existing_domain
  -> Domain Conflict Detector.existing_domain
  -> Domain Patch Merger.existing_domain

Raw Domain Input
  -> Build Domain Structuring Prompt
  -> Domain Authoring LLM JSON Caller
  -> Parse Domain Patch JSON
  -> Normalize Domain Patch
  -> Domain Conflict Detector
  -> Domain Patch Merger
  -> Domain Schema Validator
  -> Build Domain Review Prompt
  -> Domain Review LLM Caller
  -> Parse Domain Review JSON
  -> Domain Save Decision
  -> MongoDB Domain Fragment Saver
```

`Domain Authoring Config Input`은 고급 override용이다. 처음에는 연결하지 않아도 된다. 연결하지 않으면 `domain_id=manufacturing_default`, `authoring_mode=append`, `target_status=active`로 동작한다.

## Save Policy

`Domain Save Decision`은 다음 규칙으로 저장 상태를 정한다.

| Condition | MongoDB status | Main Flow 반영 |
| --- | --- | --- |
| validation/blocking error 있음 | 저장하지 않음 | No |
| rule conflict 또는 semantic conflict 있음 | `review_required` | No |
| semantic review가 rejected 권고 | 저장하지 않음 | No |
| error/conflict 없음 | `active` | Yes |
| `validate_only` mode | 저장하지 않음 | No |

## LLM Result Schema

`Build Domain Structuring Prompt`는 LLM에게 다음 구조를 요구한다.

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

기존 Streamlit 도메인 관리 화면에서 쓰던 `dataset_keywords`, `value_groups`, `analysis_rules`, `join_rules` 형태가 LLM 결과에 섞여 들어와도 `Normalize Domain Patch`가 Main Flow용 schema로 변환한다.

## Examples

- `examples/sample_raw_domain_text.txt`: 사용자가 입력할 수 있는 원문 예시
- `examples/sample_llm_result.json`: LLM 호출 없이 Parse/Normalize 이후 노드를 테스트할 수 있는 예시
