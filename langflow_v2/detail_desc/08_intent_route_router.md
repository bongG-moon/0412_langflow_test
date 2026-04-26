# 08. Intent Route Router

## 한 줄 역할

`intent_plan.route` 값을 보고 flow를 네 갈래로 나누는 분기 노드입니다.

## 네 가지 분기

| 출력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | dataset 하나만 조회하면 되는 질문입니다. |
| `multi_retrieval` | 여러 dataset을 조회해야 하는 질문입니다. |
| `followup_transform` | 이전 결과를 다시 분석하는 후속 질문입니다. |
| `finish` | 조건 부족, 조회 불필요 등으로 바로 종료하거나 안내해야 하는 경우입니다. |

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Normalize Intent Plan`의 출력입니다. |

## 주요 함수 설명

- `_intent_payload`: 입력에서 실제 intent plan을 꺼냅니다.
- `_select_route`: route 값을 읽고 유효한 분기 이름으로 정리합니다.
- `route_intent`: 선택된 branch에는 실제 payload를, 나머지 branch에는 skipped payload를 보냅니다.

## skipped payload란?

선택되지 않은 출력도 Langflow 연결상 downstream 노드에 값이 들어갈 수 있습니다.
그래서 선택되지 않은 branch에는 다음처럼 표시합니다.

```json
{
  "skipped": true,
  "skip_reason": "route is multi_retrieval"
}
```

뒤 노드들은 `skipped: true`를 보면 아무 작업도 하지 않습니다.

## 초보자 포인트

이 노드가 있어야 Langflow 화면에서 분기가 눈에 보입니다.
즉, `single`, `multi`, `follow-up`, `finish`를 캔버스에서 명확히 확인하기 위한 노드입니다.

## 연결

```text
Normalize Intent Plan.intent_plan
-> Intent Route Router.intent_plan

Intent Route Router.single_retrieval
-> Dummy/Oracle Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Dummy/Oracle Retriever (Multi).intent_plan

Intent Route Router.followup_transform
-> Current Data Retriever.intent_plan

Intent Route Router.finish
-> Early Result Adapter.intent_plan
```

