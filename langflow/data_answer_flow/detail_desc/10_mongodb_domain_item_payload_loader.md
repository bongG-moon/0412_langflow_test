# 10. MongoDB Domain Item Payload Loader

새 item 기반 도메인 저장소를 Main Data Answer Flow에서 사용할 `domain_payload`로 변환한다.

조회 위치:

```text
Database Name: datagov
Collection Name: manufacturing_domain_items
```

조회 조건:

```json
{
  "status": "active"
}
```

출력은 기존 Main Flow downstream 노드가 기대하는 형태와 같다.

```json
{
  "domain_document": {
    "domain_id": "mongodb_domain_items",
    "status": "active",
    "metadata": {},
    "domain": {}
  },
  "domain": {},
  "domain_index": {},
  "domain_errors": [],
  "mongo_domain_load_status": {
    "source": "mongodb_domain_items",
    "active_item_count": 0,
    "gbn_counts": {}
  }
}
```

다음 연결:

```text
MongoDB Domain Item Payload Loader.domain_payload -> Build Intent Prompt.domain_payload
MongoDB Domain Item Payload Loader.domain_payload -> Normalize Intent With Domain.domain_payload
MongoDB Domain Item Payload Loader.domain_payload -> Query Mode Decider.domain_payload
```
