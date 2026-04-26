# 20. Analysis Result Merger

## 한 줄 역할

early, direct, pandas branch 중 실제 결과 하나를 골라 `analysis_result`로 통합하는 노드입니다.

## 왜 필요한가

앞 흐름은 여러 branch로 나뉩니다.

- 조건 부족으로 빨리 끝난 결과
- 조회만 하고 바로 답하는 결과
- pandas 분석을 거친 결과

최종 답변 단계는 하나의 입력만 받는 것이 편하므로 이 노드가 branch를 다시 합칩니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `early_result` | `Early Result Adapter` 출력입니다. |
| `direct_result` | `Direct Result Adapter` 출력입니다. |
| `pandas_result` | `Pandas Analysis Executor` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | 선택된 최종 분석 결과입니다. |

## 주요 함수 설명

- `_analysis_result`: 입력에서 실제 result payload를 꺼냅니다.
- `merge_analysis_results`: skipped가 아닌 유효 결과를 우선순위대로 선택합니다.

## 초보자 포인트

이 노드는 데이터를 계산하지 않습니다.
"이번 턴에서 살아남은 branch 결과가 무엇인가"를 고릅니다.

## 연결

```text
Early Result Adapter.analysis_result
-> Analysis Result Merger.early_result

Direct Result Adapter.analysis_result
-> Analysis Result Merger.direct_result

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result

Analysis Result Merger.analysis_result
-> Build Final Answer Prompt.analysis_result
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "early_result": {"skipped": true},
  "direct_result": {"skipped": true},
  "pandas_result": {
    "analysis_result": {
      "success": true,
      "result_type": "pandas_analysis",
      "final_rows": [
        {"MODE": "A", "production": 150}
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
    "result_type": "pandas_analysis",
    "selected_analysis_branch": "pandas_result",
    "final_rows": [
      {"MODE": "A", "production": 150}
    ]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_analysis_result` | `{"analysis_result": {...}}` | `{...}` | branch output에서 실제 analysis result를 꺼냅니다. |
| `merge_analysis_results` | early/direct/pandas | active analysis result | 세 branch 중 skipped가 아닌 실제 결과를 하나 선택합니다. |
| `build_result` | Langflow inputs | `Data(data=analysis_result)` | Langflow output method입니다. |

### 코드 흐름

```text
early_result 확인
-> direct_result 확인
-> pandas_result 확인
-> 실제 결과 branch 선택
-> selected_analysis_branch 표시
```

### 초보자 포인트

앞에서 여러 갈래로 나뉘었던 flow를 다시 하나로 합치는 지점입니다. 뒤의 최종 답변 노드는 branch 종류를 몰라도 `analysis_result` 하나만 읽으면 됩니다.

## 함수 코드 단위 해석: `merge_analysis_results`

이 함수는 early/direct/pandas 세 결과 중 실제 실행된 analysis result 하나를 고릅니다.

### 함수 input

```json
{
  "early_result_value": {"skipped": true},
  "direct_result_value": {"skipped": true},
  "pandas_result_value": {
    "analysis_result": {
      "success": true,
      "data": [{"MODE": "A", "production": 150}]
    }
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "success": true,
    "data": [{"MODE": "A", "production": 150}],
    "selected_analysis_branch": "pandas_result"
  }
}
```

### 핵심 코드 해석

```python
candidates = [
    ("early_result", early_result_value),
    ("direct_result", direct_result_value),
    ("pandas_result", pandas_result_value),
]
```

세 branch를 순서대로 후보 list에 넣습니다.

```python
for branch, value in candidates:
    result = _analysis_result(value)
```

각 branch에서 실제 analysis result를 꺼냅니다.

```python
if not result or result.get("skipped"):
    continue
```

비어 있거나 skipped인 branch는 건너뜁니다.

```python
merged = deepcopy(result)
merged["selected_analysis_branch"] = branch
return {"analysis_result": merged}
```

실제 결과를 찾으면 복사한 뒤 어떤 branch였는지 표시하고 반환합니다.
