# 10. MongoDB Domain Item Saver

정규화된 domain item을 MongoDB에 건바이건 저장한다.

저장 기준:

```text
unique key: gbn + key
active item: Main Flow에서 사용
review_required item: 저장은 되지만 Main Flow에서는 제외
```

기본 저장 위치:

```text
Database Name: datagov
Collection Name: manufacturing_domain_items
```

출력:

```json
{
  "saved_items": [
    {
      "gbn": "metrics",
      "key": "production_achievement_rate",
      "status": "active",
      "used_in_main_flow": true
    }
  ],
  "save_status": {
    "saved": true,
    "saved_count": 1,
    "errors": []
  }
}
```
