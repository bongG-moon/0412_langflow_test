# 01. Domain Text Splitter

여러 줄 도메인 입력을 의미 단위 note 배열로 나눈다.

입력:

```text
Raw Domain Text Input.raw_domain_payload
```

출력:

```json
{
  "raw_text": "전체 원문",
  "combined_raw_text": "정리된 전체 원문",
  "raw_notes": [
    {"note_id": "note_1", "raw_text": "생산 달성률은 생산량 / 목표량으로 계산한다."},
    {"note_id": "note_2", "raw_text": "production과 target은 WORK_DT 기준으로 조인한다."}
  ],
  "note_count": 2
}
```

이 노드는 저장 건수를 직접 결정하지 않는다. LLM이 반환한 `items` 배열의 개수가 실제 MongoDB 저장 건수가 된다. splitter는 LLM이 여러 줄 입력을 놓치지 않도록 `raw_notes`를 명확하게 제공하는 역할이다.

다음 연결:

```text
Domain Text Splitter.split_domain_payload -> Domain Item Router.raw_domain_payload
```
