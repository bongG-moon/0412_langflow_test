# 02. Domain Item Router

입력 원문을 보고 어떤 도메인 항목인지 1차 분류한다.

지원 `gbn`:

```text
products
process_groups
terms
datasets
metrics
join_rules
mixed
```

Langflow 기본 Smart Router를 쓰고 싶으면 이 노드를 대체할 수 있다. 단, 뒤 노드와 연결하려면 다음 형태의 payload를 만들어야 한다.

```json
{
  "raw_text": "생산 달성률은 생산량 / 목표량이다.",
  "routes": ["metrics"],
  "primary_gbn": "metrics",
  "confidence": 0.9
}
```

다음 연결:

```text
Domain Item Router.route_payload -> MongoDB Existing Domain Item Loader.route_payload
Domain Item Router.route_payload -> Domain Item Prompt Context Builder.route_payload
Domain Item Router.route_payload -> Normalize Domain Item.route_payload
```
