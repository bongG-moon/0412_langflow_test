# 16. Retrieval Postprocess Router

## 이 노드 역할

조회가 끝난 `retrieval_payload`를 보고 결과를 바로 답변으로 보낼지, pandas 후처리 분석으로 보낼지 결정하는 분기 노드입니다.

즉 이 노드는 "조회 결과를 그대로 보여줘도 되는가?"와 "추가 계산, 정렬, 집계가 필요한가?"를 판단합니다.

## 왜 필요한가

모든 질문이 pandas 분석을 필요로 하지는 않습니다. 예를 들어 "오늘 DA공정 DDR5 생산 보여줘"처럼 이미 조회 결과 자체가 답이면 바로 최종 답변으로 갈 수 있습니다.

반대로 "공정별로 합산해줘", "가장 생산량이 높은 라인만 보여줘", "이전 결과에서 상위 5개만 정리해줘" 같은 질문은 pandas 처리가 필요합니다. 이 노드가 그 갈림길을 만들어 줍니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `retrieval_payload` | `Retrieval Payload Merger`에서 합쳐진 조회 결과입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `direct_response` | 조회 결과를 그대로 답변 단계로 보낼 때 사용하는 출력입니다. |
| `post_analysis` | pandas 분석이 필요할 때 사용하는 출력입니다. |

선택되지 않은 출력에는 `skipped: true`가 들어갑니다. Langflow에서는 두 갈래가 모두 연결되어 있어도 실제 활성 branch만 다음 노드에서 처리되도록 하기 위한 구조입니다.

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_retrieval_payload` | 입력값에서 실제 retrieval payload dict를 꺼냅니다. |
| `_select_postprocess_route` | `direct_response`와 `post_analysis` 중 어떤 route를 쓸지 결정합니다. |
| `route_retrieval_postprocess` | 선택된 branch에는 원본 payload를 싣고, 선택되지 않은 branch에는 skipped payload를 만듭니다. |

## 초보자 확인용

이 노드는 데이터를 직접 조회하거나 분석하지 않습니다. 이미 조회된 결과를 보고 다음 길을 나누는 교차로 역할만 합니다.

pandas가 필요한 대표 조건은 다음과 같습니다.

| 조건 | route |
| --- | --- |
| `intent_plan.needs_pandas`가 true | `post_analysis` |
| `query_mode`가 `followup_transform` | `post_analysis` |
| 여러 개의 `source_results`를 함께 분석해야 함 | `post_analysis` |
| 위 조건에 해당하지 않음 | `direct_response` |

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

`post_analysis`가 선택된 경우:

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

선택되지 않은 `direct_response`에는 다음처럼 skipped payload가 들어갑니다.

```json
{
  "skipped": true,
  "selected_postprocess_route": "post_analysis",
  "branch": "direct_response"
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_retrieval_payload` | `Data(data={"retrieval_payload": {...}})` | `{...}` | Langflow Data wrapper 안에서 실제 payload만 꺼냅니다. |
| `_select_postprocess_route` | retrieval payload | `"post_analysis"` | intent plan과 source 개수를 보고 route를 결정합니다. |
| `route_retrieval_postprocess` | payload, branch 이름 | active/skipped payload | 선택된 output만 다음 노드가 처리할 수 있도록 payload를 구성합니다. |

### 코드 흐름

```text
retrieval_payload 입력
-> intent_plan 확인
-> source_results 개수 확인
-> direct_response 또는 post_analysis 선택
-> 선택되지 않은 output은 skipped 처리
```

## 함수 코드 단위 해석: `_select_postprocess_route`

이 함수는 후처리 route 결정의 핵심입니다.

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

조회 payload 안에 들어 있는 intent plan을 꺼냅니다.

```python
source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
```

조회 결과가 몇 개의 source에서 왔는지 확인합니다.

```python
if plan.get("needs_pandas") or plan.get("query_mode") == "followup_transform" or len(source_results) > 1:
    return "post_analysis"
```

pandas가 필요하다고 판단되는 조건이면 `post_analysis`로 보냅니다.

```python
return "direct_response"
```

그 외에는 조회 결과를 바로 답변 단계로 보냅니다.

## 추가 함수 코드 단위 해석: `route_retrieval_postprocess`

```python
retrieval = _retrieval_payload(retrieval_payload_value)
selected = _select_postprocess_route(retrieval)
```

입력에서 실제 retrieval payload를 꺼낸 뒤 direct response와 post analysis 중 어떤 branch가 맞는지 계산합니다.

```python
if selected != branch:
    return {
        "retrieval_payload": {
            "skipped": True,
            "skip_reason": f"selected postprocess route is {selected}",
            ...
        }
    }
```

현재 output port가 선택된 branch가 아니면 skipped payload를 반환합니다. Langflow의 여러 output을 모두 연결해도 비활성 branch가 뒤 노드를 실행하지 않도록 하기 위한 구조입니다.

```python
routed = deepcopy(retrieval)
routed["selected_postprocess_route"] = selected
routed["branch"] = branch
```

선택된 branch에는 원본 retrieval payload를 복사해서 보내고, 어떤 postprocess route로 선택됐는지 표시합니다.

## 추가 함수 코드 단위 해석: `_select_postprocess_route`의 early result 처리

```python
if retrieval.get("early_result"):
    return "direct_response"
```

finish/clarification 계열 결과는 pandas 분석 대상이 아닙니다. 그래서 direct response branch로 보내 최종 답변 단계로 빠르게 이어지게 합니다.

```python
if plan.get("needs_pandas") or plan.get("query_mode") == "followup_transform" or len(source_results) > 1:
    return "post_analysis"
```

분석 필요 flag, 후속 분석 모드, 여러 source 병합 중 하나라도 해당되면 pandas branch로 보냅니다.
