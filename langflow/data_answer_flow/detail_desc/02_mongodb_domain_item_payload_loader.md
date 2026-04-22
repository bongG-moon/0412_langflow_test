# 02. MongoDB Domain Item Payload Loader

`domain_item_authoring_flow`에서 저장한 item-level domain knowledge를 Main Flow에서 읽어오는 노드다.

## 입력

```text
db_name
collection_name
```

둘 다 advanced input이다.

기본값:

```text
db_name = datagov
collection_name = manufacturing_domain_items
```

## 출력

```text
domain_payload
```

## MongoDB 조회 방식

domain id를 입력받지 않는다.

아래 조건으로 item을 모두 읽는다.

```json
{
  "status": "active"
}
```

읽는 필드는 실행에 필요한 값만 남겼다.

```text
gbn
key
payload
```

`created_at`, `updated_at`, patch hash 같은 관리성 필드는 Main Flow 실행에 필요하지 않으므로 불러오지 않는다.

## 반환 구조

```json
{
  "domain_document": {
    "domain_id": "mongodb_domain_items",
    "status": "active",
    "metadata": {}
  },
  "domain": {
    "products": {},
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  },
  "domain_index": {},
  "domain_prompt_context": {},
  "domain_errors": [],
  "mongo_domain_load_status": {}
}
```

## domain과 domain_prompt_context 차이

`domain`은 정규화, 후처리, pandas 분석에서 필요한 전체 정보다.

`domain_prompt_context`는 LLM prompt에 넣기 위한 경량 요약이다.

포함하는 정보:

- dataset의 `display_name`, `keywords`, `required_params`, `tool_name`
- metric의 `display_name`, `aliases`, `required_datasets`, `formula`
- product/process/term alias 요약
- 빠른 정규화를 위한 `alias_index`

제외하는 정보:

- MongoDB 관리 필드
- 저장 시점 metadata
- 전체 컬럼을 포함한 큰 원본 payload 중 prompt에 바로 필요 없는 정보

## 연결

```text
MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload
```

뒤 노드에는 domain payload를 반복 연결하지 않는다. `Main Flow Context Builder`가 `main_context` 안에 domain 정보를 담아 전달한다.
