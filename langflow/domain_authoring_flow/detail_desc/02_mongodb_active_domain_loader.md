# 02. MongoDB Active Domain Loader

## 역할

MongoDB에 저장된 `active` 상태 domain fragment를 모두 불러와 하나의 기존 도메인 문서로 병합한다.

도메인 지식을 조금씩 저장하더라도, 새 조각을 검증할 때는 기존 active 조각 전체를 합친 현재 도메인과 비교해야 한다. 이 노드는 그 현재 도메인을 만든다.

## 입력

- `authoring_config`: 선택. 연결하지 않으면 `manufacturing_default`를 사용한다.
- `domain_id`: 선택. 기본값은 `manufacturing_default`
- `db_name`: 선택. MongoDB database 이름. 기본값은 `datagov`
- `collection_name`: 선택. domain fragment collection 이름. 기본값은 `manufacturing_domain_fragments`

두 입력 모두 설정하지 않아도 기본 도메인으로 자동 동작한다.

## MongoDB

- DB: `datagov`
- Collection: `manufacturing_domain_fragments`
- Query: `{"domain_id": domain_id, "status": "active"}`

`datagov`는 collection이 아니라 database 이름이다. 다른 database나 collection에 저장하고 싶으면 고급 입력의 `db_name`, `collection_name`을 변경한다.

## 출력

`existing_domain`

```json
{
  "existing_domain_document": {
    "domain_id": "manufacturing_default",
    "status": "active",
    "metadata": {},
    "domain": {
      "products": {},
      "process_groups": {},
      "terms": {},
      "datasets": {},
      "metrics": {},
      "join_rules": []
    }
  },
  "mongo_domain_load_status": {
    "domain_id": "manufacturing_default",
    "database": "datagov",
    "collection": "manufacturing_domain_fragments",
    "active_fragment_count": 0,
    "loaded": true,
    "errors": []
  }
}
```

## 다음 연결

```text
MongoDB Active Domain Loader.existing_domain -> Build Domain Structuring Prompt.existing_domain
MongoDB Active Domain Loader.existing_domain -> Domain Conflict Detector.existing_domain
MongoDB Active Domain Loader.existing_domain -> Domain Patch Merger.existing_domain
```
