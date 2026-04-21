# 09. MongoDB Domain Payload Loader

## 역할

Main Data Answer Flow에서 사용할 도메인 정보를 MongoDB에서 불러오는 노드다.

Domain Authoring Flow의 `MongoDB Domain Fragment Saver`가 저장한 `active` 상태 fragment를 모두 읽고, 하나의 `domain_payload`로 병합한다. 이 `domain_payload`는 기존 `Domain JSON Loader.domain_payload`와 같은 형태이므로 뒤 노드들은 그대로 연결할 수 있다.

이 loader는 legacy fragment 기반 도메인 저장소를 사용할 때의 입력 경로다.
현재 Main Flow에서는 loader output을 `Main Flow Context Builder`에 한 번만 연결한다.

```text
MongoDB Domain Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload
```

## 입력

- `domain_id`: 선택 입력. 기본값은 `manufacturing_default`
- `Database Name`: 선택 입력. MongoDB database 이름. 기본값은 `datagov`
- `Collection Name`: 선택 입력. domain fragment collection 이름. 기본값은 `manufacturing_domain_fragments`

`Database Name`과 `Collection Name`은 Authoring Flow에서 저장할 때 사용한 값과 같아야 한다.

## MongoDB 조회 조건

```json
{
  "domain_id": "입력 domain_id",
  "status": "active"
}
```

조회된 fragment는 `created_at`, `_id` 순서로 병합된다. 따라서 먼저 저장된 정보 위에 나중에 저장된 정보가 추가/보완되는 방식으로 동작한다.

## 출력

`domain_payload`

```json
{
  "domain_document": {
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
  "domain": {
    "products": {},
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  },
  "domain_index": {
    "term_alias_to_key": {},
    "product_alias_to_key": {},
    "process_alias_to_group": {},
    "metric_alias_to_key": {},
    "dataset_keyword_to_key": {}
  },
  "domain_errors": [],
  "mongo_domain_load_status": {
    "domain_id": "manufacturing_default",
    "database": "datagov",
    "collection": "manufacturing_domain_fragments",
    "active_fragment_count": 1,
    "loaded": true,
    "errors": [],
    "domain_error_count": 0,
    "source": "mongodb_domain_fragments"
  }
}
```

`loaded`는 MongoDB에서 active fragment를 정상 조회했는지를 의미한다. 조회된 도메인 안의 alias 충돌, column schema 경고 등은 `domain_errors`와 `domain_error_count`에서 확인한다.

## active fragment가 없을 때

MongoDB 연결은 성공했지만 해당 `domain_id`와 collection에 `active` fragment가 없으면 `domain_errors`에 다음 형태의 메시지가 들어간다.

```json
{
  "domain_errors": [
    "No active domain fragments found for domain_id='manufacturing_default' in datagov.manufacturing_domain_fragments."
  ],
  "mongo_domain_load_status": {
    "loaded": false,
    "active_fragment_count": 0,
    "errors": [
      "No active domain fragments found for domain_id='manufacturing_default' in datagov.manufacturing_domain_fragments."
    ],
    "domain_error_count": 1
  }
}
```

이 경우에는 Authoring Flow에서 fragment가 `active`로 저장되었는지, 그리고 Main Flow의 `Database Name`, `Collection Name`, `domain_id`가 저장 노드와 같은지 확인하면 된다.

## 다음 연결

```text
MongoDB Domain Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload
```

## 수동 JSON 테스트 경로

MongoDB를 쓰지 않고 로컬 JSON으로 테스트할 때만 아래 경로를 사용한다.

```text
Domain JSON Input.domain_json_payload -> Domain JSON Loader.domain_json_payload
Domain JSON Loader.domain_payload -> Main Flow Context Builder.domain_payload
```
