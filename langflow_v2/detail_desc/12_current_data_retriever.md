# 12. Current Data Retriever

## 한 줄 역할

후속 질문에서 이전 결과인 `state.current_data`를 새 조회 결과처럼 다시 꺼내는 노드입니다.

## 언제 쓰나?

첫 질문:

```text
오늘 DA공정 생산량 알려줘
```

후속 질문:

```text
이때 가장 생산량이 많았던 MODE 알려줘
```

두 번째 질문은 DB를 새로 조회할 필요가 없습니다.
이전 결과를 pandas로 다시 분석하면 됩니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.followup_transform` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | 이전 current_data를 source_results처럼 감싼 payload입니다. |

## 주요 함수 설명

- `_source_result_from_current_data`: current_data를 source_result 형태로 바꿉니다.
- `_build_current_datasets`: 현재 데이터의 dataset 요약을 만듭니다.
- `retrieve_current_data`: 후속 분석에 필요한 retrieval_payload를 만듭니다.

## 초보자 포인트

이름은 Retriever지만 DB 조회를 하지 않습니다.
이미 가지고 있는 데이터를 "조회 결과처럼" 포장해서 뒤 노드들이 같은 방식으로 처리하게 만듭니다.

## 연결

```text
Intent Route Router.followup_transform
-> Current Data Retriever.intent_plan

Current Data Retriever.retrieval_payload
-> Retrieval Payload Merger.followup_retrieval
```

