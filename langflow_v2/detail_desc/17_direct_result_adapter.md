# 17. Direct Result Adapter

## 이 노드 역할

pandas 분석 없이 바로 답변 가능한 조회 결과를 표준 `analysis_result` 형태로 바꾸는 노드입니다.

`Retrieval Postprocess Router`에서 `direct_response`로 선택된 payload를 받아 최종 답변 빌더가 읽을 수 있는 공통 결과 구조로 정리합니다.

## 왜 필요한가

뒤쪽 노드들은 pandas 분석 결과든 단순 조회 결과든 모두 `analysis_result`라는 같은 형식을 기대합니다.

이 노드가 없으면 direct branch와 pandas branch의 결과 모양이 달라져서 `Analysis Result Merger`, `Build Final Answer Prompt`, `Final Answer Builder`에서 매번 다른 구조를 처리해야 합니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `retrieval_payload` | `Retrieval Postprocess Router.direct_response`에서 전달된 payload입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `analysis_result` | 최종 답변 단계에서 사용할 표준 분석 결과 payload입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_retrieval_payload` | 입력값에서 실제 retrieval payload를 꺼냅니다. |
| `adapt_direct_result` | 첫 번째 조회 결과를 기준으로 `analysis_result`를 만듭니다. |

## 초보자 확인용

이 노드는 계산을 하지 않습니다. 조회된 row를 최종 답변 노드가 이해하는 이름과 위치로 옮겨 담는 어댑터입니다.

대표적으로 `source_results[0].data`를 `analysis_result.data`로 복사하고, 조회 조건도 `retrieval_applied_params`, `retrieval_applied_filters`, `filter_plan` 등에 보존합니다.

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
    "intent_plan": {
      "required_params": {"date": "20260426"},
      "filters": {"process_name": ["D/A1", "D/A2"]}
    },
    "source_results": [
      {
        "dataset_key": "production",
        "success": true,
        "data": [
          {"WORK_DT": "20260426", "OPER_NAME": "D/A1", "production": 100}
        ],
        "summary": "1 rows"
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
    "tool_name": "direct_response",
    "data": [
      {"WORK_DT": "20260426", "OPER_NAME": "D/A1", "production": 100}
    ],
    "summary": "1 rows",
    "analysis_logic": "direct_response",
    "retrieval_applied_params": {"date": "20260426"},
    "retrieval_applied_filters": {"process_name": ["D/A1", "D/A2"]}
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_retrieval_payload` | `{"retrieval_payload": {...}}` | retrieval dict | wrapper에서 실제 조회 payload를 꺼냅니다. |
| `adapt_direct_result` | retrieval payload | `{"analysis_result": {...}}` | 조회 결과를 표준 analysis result로 변환합니다. |

### 코드 흐름

```text
direct_response payload 입력
-> skipped 여부 확인
-> source_results 중 첫 번째 성공 결과 선택
-> rows, summary, intent_plan, state 보존
-> analysis_result 생성
```

## 함수 코드 단위 해석: `adapt_direct_result`

### 함수 input

```json
{
  "retrieval_payload": {
    "source_results": [
      {
        "dataset_key": "production",
        "success": true,
        "data": [{"production": 100}]
      }
    ]
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "direct_response",
    "data": [{"production": 100}],
    "analysis_logic": "direct_response"
  }
}
```

### 핵심 코드 해석

```python
retrieval = _retrieval_payload(retrieval_payload_value)
```

입력값에서 실제 retrieval payload를 꺼냅니다.

```python
source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
```

조회 source 결과 목록을 가져옵니다.

```python
first = source_results[0] if source_results and isinstance(source_results[0], dict) else {}
```

direct response에서는 보통 하나의 조회 결과를 기준으로 답변을 만들기 때문에 첫 번째 source를 사용합니다.

```python
rows = first.get("data") if isinstance(first.get("data"), list) else []
```

실제 데이터 row 목록을 꺼냅니다.

```python
"retrieval_applied_params": plan.get("required_params", {}),
"retrieval_applied_filters": plan.get("filters", {}),
"filter_plan": plan.get("filter_plan", []),
```

다음 턴에서 이어서 질문할 때 필요한 조회 조건과 필터 계획을 결과 안에 보존합니다.
