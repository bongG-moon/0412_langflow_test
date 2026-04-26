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

## Python 코드 상세 해석

### 입력 예시

```json
{
  "retrieval_payload": {
    "success": true,
    "intent_plan": {
      "needs_pandas": true,
      "query_mode": "retrieval"
    },
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ]
  }
}
```

### 출력 예시

`post_analysis` output:

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ]
  },
  "selected_postprocess_route": "post_analysis",
  "branch": "post_analysis"
}
```

`direct_response` output은 선택되지 않았으므로:

```json
{
  "skipped": true,
  "selected_postprocess_route": "post_analysis",
  "branch": "direct_response"
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_retrieval_payload` | `Data(data={"retrieval_payload": {...}})` | retrieval dict | merger 출력에서 실제 payload를 꺼냅니다. |
| `_select_postprocess_route` | retrieval payload | `"direct_response"` 또는 `"post_analysis"` | pandas 분석이 필요한지 결정합니다. multi source, follow-up, `needs_pandas=true`면 보통 post_analysis입니다. |
| `route_retrieval_postprocess` | retrieval payload, branch | active 또는 skipped payload | 선택된 branch만 다음 노드가 처리하게 합니다. |
| `_payload` | branch 이름 | routed payload | class output method들이 공유하는 내부 함수입니다. |
| `build_direct_response`, `build_post_analysis` | 없음 | `Data(data=payload)` | Langflow canvas에 보이는 두 output port입니다. |

### 코드 흐름

```text
retrieval_payload 입력
-> source_results 개수와 needs_pandas 확인
-> direct_response 또는 post_analysis 선택
-> 선택되지 않은 output에는 skipped 표시
```

### 초보자 포인트

이 노드는 "조회된 데이터를 그대로 말할지", "pandas로 계산한 뒤 말할지"를 나누는 두 번째 교차로입니다.

## 함수 코드 단위 해석: `_select_postprocess_route`

이 함수는 조회 결과를 바로 답변할지, pandas 분석으로 보낼지 결정합니다.

### 함수 input

```json
{
  "intent_plan": {
    "needs_pandas": true,
    "query_mode": "retrieval"
  },
  "source_results": [
    {"dataset_key": "production"},
    {"dataset_key": "wip"}
  ]
}
```

### 함수 output

```text
post_analysis
```

### 핵심 코드 해석

```python
plan = retrieval.get("intent_plan") if isinstance(retrieval.get("intent_plan"), dict) else {}
```

retrieval payload 안에서 intent plan을 꺼냅니다.

```python
source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
```

조회 결과가 몇 개 source에서 왔는지 확인합니다.

```python
if plan.get("needs_pandas") or plan.get("query_mode") == "followup_transform" or len(source_results) > 1:
    return "post_analysis"
```

아래 중 하나라도 해당하면 pandas 분석으로 보냅니다.

- intent plan에서 pandas 필요하다고 판단함
- 후속 질문임
- 여러 dataset을 조회함

```python
return "direct_response"
```

그 외에는 조회 결과를 바로 답변에 사용합니다.
