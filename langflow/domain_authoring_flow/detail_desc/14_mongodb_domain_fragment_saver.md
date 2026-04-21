# 14. MongoDB Domain Fragment Saver

## 역할

정규화된 domain patch를 MongoDB fragment 문서로 저장한다.

저장되는 fragment는 나중에 Main Flow의 `MongoDB Domain Payload Loader`가 `active` 상태만 모아서 하나의 Domain JSON으로 병합한다.

## 입력

- `normalized_domain_patch`: Normalize Domain Patch output
- `save_decision`: Domain Save Decision output
- `validated_domain`: Domain Schema Validator output
- `authoring_config`: 선택. 연결하지 않으면 `manufacturing_default`를 사용한다.
- `db_name`: 선택. MongoDB database 이름. 기본값은 `datagov`
- `collection_name`: 선택. 저장할 collection 이름. 기본값은 `manufacturing_domain_fragments`

## MongoDB

- DB: `datagov`
- Collection: `manufacturing_domain_fragments`

`datagov`는 collection이 아니라 database 이름이다. 다른 database나 collection에 저장하고 싶으면 고급 입력의 `db_name`, `collection_name`을 변경한다.

## 저장 문서 형태

```json
{
  "domain_id": "manufacturing_default",
  "fragment_id": "manufacturing_default_xxxxxxxx_xxxxxxxx",
  "status": "active",
  "title": "metrics:production_achievement_rate",
  "domain_patch": {},
  "patch_summary": {
    "products": [],
    "process_groups": [],
    "terms": [],
    "datasets": [],
    "metrics": [],
    "join_rules": []
  },
  "patch_hash": "...",
  "validation": {},
  "save_decision": {},
  "metadata": {},
  "authoring_mode": "append",
  "created_at": "UTC ISO datetime",
  "updated_at": "UTC ISO datetime"
}
```

## 출력

`saved_fragment`

```json
{
  "saved_fragment": {
    "saved": true,
    "domain_id": "manufacturing_default",
    "fragment_id": "manufacturing_default_xxxxxxxx_xxxxxxxx",
    "status": "active",
    "database": "datagov",
    "collection": "manufacturing_domain_fragments",
    "upserted_id": "...",
    "matched_count": 0,
    "modified_count": 0,
    "error": "",
    "used_in_main_flow": true
  }
}
```

`status=review_required`로 저장된 조각은 `used_in_main_flow=false`이며 Main Flow에서 자동으로 불러오지 않는다.

같은 `domain_id + patch_hash`가 다시 저장되면 새 문서를 계속 추가하지 않고 기존 fragment를 업데이트한다.
