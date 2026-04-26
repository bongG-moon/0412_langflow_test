# 14. Retrieval Payload Merger

## 한 줄 역할

single, multi, follow-up retrieval branch 중 실제로 실행된 payload 하나를 골라 다음 노드로 넘깁니다.

## 왜 필요한가

Langflow에서는 branch가 여러 개로 갈라져도 다시 하나로 합쳐야 뒤 처리를 공통으로 할 수 있습니다.

이 노드는 다음 세 branch를 하나로 모읍니다.

- single retrieval
- multi retrieval
- follow-up retrieval

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | 단일 조회 branch 결과입니다. |
| `multi_retrieval` | 복합 조회 branch 결과입니다. |
| `followup_retrieval` | 이전 current_data 재사용 branch 결과입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | 실제 선택된 retrieval 결과입니다. |

## 주요 함수 설명

- `_retrieval_payload`: 입력에서 실제 retrieval_payload를 꺼냅니다.
- `merge_retrieval_payloads`: skipped가 아닌 첫 번째 유효 payload를 선택합니다.

## 초보자 포인트

이 노드는 데이터를 합산하거나 join하지 않습니다.
"여러 branch 출력 중 어떤 branch가 진짜인가"를 고르는 역할입니다.

데이터 join이나 계산은 나중의 pandas 단계에서 합니다.

## 연결

```text
Dummy/Oracle Retriever (Single).retrieval_payload
-> Retrieval Payload Merger.single_retrieval

Dummy/Oracle Retriever (Multi).retrieval_payload
-> Retrieval Payload Merger.multi_retrieval

Current Data Retriever.retrieval_payload
-> Retrieval Payload Merger.followup_retrieval

Retrieval Payload Merger.retrieval_payload
-> Retrieval Postprocess Router.retrieval_payload
```

