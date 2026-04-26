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

## Python 코드 상세 해석

### 입력 예시

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "dataset_key": "production",
        "data": [
          {"MODE": "A", "production": 10}
        ],
        "summary": "total rows 1"
      }
    ]
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": true,
    "result_type": "direct_response",
    "source_results": [
      {
        "dataset_key": "production",
        "data": [
          {"MODE": "A", "production": 10}
        ]
      }
    ],
    "final_rows": [
      {"MODE": "A", "production": 10}
    ],
    "summary": "total rows 1"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_retrieval_payload` | `{"retrieval_payload": {...}}` | retrieval dict | 앞 router output에서 실제 조회 결과를 꺼냅니다. |
| `adapt_direct_result` | retrieval payload | analysis result | pandas 없이 바로 최종 답변으로 갈 수 있게 조회 결과를 analysis_result 형식으로 바꿉니다. |
| `build_result` | Langflow input | `Data(data=analysis_result)` | Langflow output method입니다. |

### 코드 흐름

```text
direct_response branch 입력
-> 첫 source_result의 data를 final_rows로 사용
-> source_results와 summary 유지
-> Analysis Result Merger로 전달
```

### 초보자 포인트

조회 결과를 그대로 보여줘도 되는 질문이라면 pandas를 거치지 않습니다. 그래도 뒤 노드와 모양을 맞추기 위해 `analysis_result`로 변환합니다.

## 함수 코드 단위 해석: `adapt_direct_result`

이 함수는 retrieval payload를 final answer가 읽을 수 있는 analysis result로 바꿉니다.

### 함수 input

```json
{
  "retrieval_payload": {
    "source_results": [
      {
        "dataset_key": "production",
        "data": [
          {"MODE": "A", "production": 10}
        ],
        "summary": "total rows 1"
      }
    ],
    "intent_plan": {"route": "single_retrieval"}
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "direct_response",
    "data": [
      {"MODE": "A", "production": 10}
    ],
    "summary": "total rows 1",
    "analysis_logic": "direct_response"
  }
}
```

### 핵심 코드 해석

```python
retrieval = _retrieval_payload(retrieval_payload_value)
```

앞 노드에서 넘어온 값을 retrieval payload dict로 꺼냅니다.

```python
source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
first = source_results[0] if source_results and isinstance(source_results[0], dict) else {}
```

직접 답변은 보통 첫 번째 조회 결과를 기준으로 합니다.

```python
rows = first.get("data") if isinstance(first.get("data"), list) else []
```

첫 source result 안의 실제 row list를 꺼냅니다.

```python
result = {
    "success": bool(first.get("success", retrieval.get("success", True))),
    "data": rows,
    "summary": first.get("summary", retrieval.get("summary", "")),
    ...
}
```

pandas 결과와 같은 모양으로 맞추기 위해 `success`, `data`, `summary`, `source_results`, `intent_plan` 등을 채웁니다.
