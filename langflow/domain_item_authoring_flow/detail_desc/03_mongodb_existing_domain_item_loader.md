# 03. MongoDB Existing Domain Item Loader

route에 포함된 `gbn`에 해당하는 기존 item만 MongoDB에서 조회한다.

기본 조회 위치:

```text
Database Name: datagov
Collection Name: manufacturing_domain_items
```

조회 조건:

```json
{
  "gbn": {"$in": ["metrics"]},
  "status": {"$in": ["active", "review_required"]}
}
```

기존 item 전체가 아니라 key, alias, keyword 등 충돌 검증과 prompt에 필요한 요약만 반환한다.
