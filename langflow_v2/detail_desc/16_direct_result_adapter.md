# 16. Direct Result Adapter

## 한 줄 역할

pandas 분석이 필요 없는 조회 결과를 `analysis_result` 형태로 바꾸는 노드입니다.

## 언제 쓰나?

예를 들어 단순히 `오늘 DA공정 생산량 알려줘`처럼 조회된 row와 summary만으로 답할 수 있는 경우 사용됩니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | `Retrieval Postprocess Router.direct_response` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | 최종 답변 단계가 읽을 표준 결과입니다. |

## 주요 함수 설명

- `_retrieval_payload`: 입력에서 실제 retrieval payload를 꺼냅니다.
- `adapt_direct_result`: source_results, rows, summary를 final 단계용 analysis_result로 정리합니다.

## 초보자 포인트

이 노드는 데이터를 계산하지 않습니다.
조회 결과를 최종 답변 노드가 읽기 쉬운 모양으로 바꾸는 adapter입니다.

## 연결

```text
Retrieval Postprocess Router.direct_response
-> Direct Result Adapter.retrieval_payload

Direct Result Adapter.analysis_result
-> Analysis Result Merger.direct_result
```

