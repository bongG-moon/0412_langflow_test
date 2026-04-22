# 08. Normalize Domain Item

LLM이 만든 raw item을 MongoDB 저장용 최소 schema로 정리한다.

출력 item 예시:

```json
{
  "gbn": "metrics",
  "key": "production_achievement_rate",
  "status": "active",
  "payload": {},
  "normalized_aliases": [],
  "normalized_keywords": [],
  "source_note_id": "note_1",
  "source_text": "",
  "warnings": []
}
```

`normalized_aliases`, `normalized_keywords`는 충돌 검증과 추후 웹 검색에 사용한다.
