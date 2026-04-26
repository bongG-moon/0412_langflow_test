# 15. Retrieval Postprocess Router

## 한 줄 역할

조회 결과를 바로 답할지, pandas 분석을 거칠지 나누는 분기 노드입니다.

## 두 가지 분기

| 출력 포트 | 의미 |
| --- | --- |
| `direct_response` | 조회 결과를 거의 그대로 최종 답변으로 보낼 수 있습니다. |
| `post_analysis` | group by, sort, metric 계산, follow-up 분석 등 pandas 처리가 필요합니다. |

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | `Retrieval Payload Merger`의 출력입니다. |

## 주요 함수 설명

- `_select_postprocess_route`: pandas가 필요한지 판단합니다.
- `route_retrieval_postprocess`: 선택된 branch에는 payload를 보내고 나머지는 skipped 처리합니다.

## pandas가 필요한 대표 경우

- `needs_pandas`가 true
- 여러 source_result가 있음
- 후속 질문이라 current_data를 다시 분석해야 함
- top N, 정렬, 그룹 집계, metric 계산이 필요함

## 초보자 포인트

이 노드는 분석을 직접 하지 않습니다.
분석이 필요한지 판단해서 길을 나눌 뿐입니다.

## 연결

```text
Retrieval Payload Merger.retrieval_payload
-> Retrieval Postprocess Router.retrieval_payload

Retrieval Postprocess Router.direct_response
-> Direct Result Adapter.retrieval_payload

Retrieval Postprocess Router.post_analysis
-> Build Pandas Prompt.retrieval_payload
```

