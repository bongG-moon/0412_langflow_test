# 20. Pandas Analysis Executor

## 이 노드 역할

정규화된 pandas 분석 계획을 실제로 실행하고, 결과를 표준 `analysis_result`로 만드는 노드입니다.

`Normalize Pandas Plan`에서 받은 code를 실행하기 전에 필터를 적용하고, 코드 안전성 검사를 거친 뒤, 최종 row 목록을 생성합니다.

## 왜 필요한가

LLM은 pandas 코드를 만들어 줄 수 있지만, 그 코드를 아무 제한 없이 실행하면 위험합니다. 또한 후속 질문에서 상속된 필터나 컬럼 기반 필터가 실제 데이터에 적용되어야 합니다.

이 노드는 코드 실행 전에 `filter_plan`, `column_filters`, `filters`를 DataFrame에 적용하고, 금지된 Python 문법이나 위험한 이름을 검사합니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `analysis_plan_payload` | `Normalize Pandas Plan`에서 만든 실행 계획입니다. |
| `retrieval_payload` | 실험용 override 입력입니다. 일반 flow에서는 비워도 됩니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `analysis_result` | pandas 실행 결과와 분석 메타데이터가 포함된 표준 결과입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_merge_sources` | 여러 source result를 실행용 table로 병합합니다. |
| `_apply_filter_plan` | 표준 의미 filter와 실제 컬럼 매핑 기반 필터를 적용합니다. |
| `_validate_code` | 생성된 pandas 코드가 허용 가능한 문법인지 검사합니다. |
| `_execute_code` | DataFrame을 만들고 pandas 코드를 실행합니다. |
| `execute_pandas_analysis` | 전체 실행 흐름을 제어하고 `analysis_result`를 만듭니다. |

## 초보자 확인용

이 노드는 실제 pandas 실행이 일어나는 핵심 노드입니다.

LLM 코드가 실패하면 가능한 경우 fallback code로 한 번 더 시도합니다. 그래서 LLM 응답이 조금 불안정해도 flow가 완전히 멈추지 않게 설계되어 있습니다.

## 연결

```text
Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result = df.groupby(['MODE'], as_index=False)['production'].sum()",
      "source": "llm"
    },
    "retrieval_payload": {
      "intent_plan": {
        "filter_plan": [
          {
            "field": "process_name",
            "columns": ["OPER_NAME"],
            "values": ["D/A1", "D/A2"]
          }
        ]
      },
      "source_results": [
        {
          "success": true,
          "data": [
            {"MODE": "DDR5", "OPER_NAME": "D/A1", "production": 100},
            {"MODE": "DDR5", "OPER_NAME": "W/B1", "production": 30}
          ]
        }
      ]
    }
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "analyze_current_data",
    "data": [
      {"MODE": "DDR5", "production": 100}
    ],
    "analysis_logic": "llm",
    "filter_notes": ["filter process_name: 2->1"],
    "awaiting_analysis_choice": true
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_apply_filter_plan` | DataFrame, filter_plan | 필터링된 DataFrame | semantic filter가 매핑된 실제 컬럼에 적용됩니다. |
| `_validate_code` | pandas code | `(true, "")` | 위험한 import, eval, open 등을 막습니다. |
| `_execute_code` | code, rows, plan | 실행 결과 dict | `df`를 만들고 code 실행 후 `result` DataFrame을 꺼냅니다. |
| `execute_pandas_analysis` | analysis_plan_payload | analysis_result | 전체 pandas 분석 결과를 표준 구조로 만듭니다. |

### 코드 흐름

```text
analysis_plan_payload 입력
-> retrieval/source data 확보
-> filter_plan 또는 column_filters 적용
-> code 안전성 검사
-> pandas code 실행
-> 실패 시 fallback code 재시도
-> analysis_result 출력
```

## 함수 코드 단위 해석: `_execute_code`

### 함수 input

```json
{
  "code": "result = df.groupby(['MODE'], as_index=False)['production'].sum()",
  "rows": [
    {"MODE": "DDR5", "OPER_NAME": "D/A1", "production": 100}
  ],
  "plan": {
    "filter_plan": [
      {"field": "process_name", "columns": ["OPER_NAME"], "values": ["D/A1"]}
    ]
  }
}
```

### 함수 output

```json
{
  "success": true,
  "data": [
    {"MODE": "DDR5", "production": 100}
  ],
  "filter_notes": ["filter process_name: 1->1"]
}
```

### 핵심 코드 해석

```python
frame = pd.DataFrame(rows or [])
```

조회 row를 pandas DataFrame으로 바꿉니다.

```python
frame, filter_notes = _apply_filter_plan(frame, plan.get("filter_plan", []), plan.get("column_filters", {}))
```

정규화된 filter plan과 실제 컬럼 기반 필터를 먼저 적용합니다.

```python
if not filter_notes:
    frame, filter_notes = _apply_filters(frame, plan.get("filters", {}))
```

filter plan이 없으면 기존 방식의 deterministic filter를 보조적으로 적용합니다.

```python
ok, error = _validate_code(code)
```

실행 전에 코드 문법과 위험한 접근을 검사합니다.

```python
exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
```

제한된 builtins와 local 변수만 제공한 상태로 코드를 실행합니다.

```python
result = local_vars.get("result")
```

생성된 코드는 반드시 `result` 변수에 최종 DataFrame을 넣어야 합니다.
