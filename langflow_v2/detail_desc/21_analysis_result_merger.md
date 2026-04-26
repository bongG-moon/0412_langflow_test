# 21. Analysis Result Merger

## 이 노드 역할

early result, direct result, pandas result 중 실제로 활성화된 결과 하나를 선택해 하나의 `analysis_result`로 합치는 노드입니다.

앞쪽 flow는 여러 branch로 나뉘지만, 최종 답변 단계는 하나의 결과만 받는 구조가 편합니다. 이 노드가 다시 결과 흐름을 하나로 모읍니다.

## 왜 필요한가

질문 종류에 따라 다음 세 가지 branch 중 하나가 활성화됩니다.

| branch | 의미 |
| --- | --- |
| `early_result` | 조회 없이 바로 답변할 수 있는 경우 |
| `direct_result` | 조회 결과를 그대로 답변하면 되는 경우 |
| `pandas_result` | pandas 후처리 분석을 거친 경우 |

이 노드는 선택되지 않은 skipped branch를 무시하고 실제 결과만 다음 노드로 넘깁니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `early_result` | 조기 응답 branch의 결과입니다. |
| `direct_result` | direct response branch의 결과입니다. |
| `pandas_result` | pandas analysis branch의 결과입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `analysis_result` | 최종 답변 prompt와 final builder가 사용할 단일 결과입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_analysis_result` | 입력 wrapper에서 실제 result dict를 꺼냅니다. |
| `merge_analysis_results` | 세 입력 중 skipped가 아닌 결과를 선택합니다. |

## 초보자 확인용

이 노드는 계산하지 않습니다. 여러 갈래 중 실제로 성공한 갈래를 하나로 모으는 정리 노드입니다.

보통 하나의 branch만 활성화되므로, 이 노드가 선택할 결과도 하나입니다.

## 연결

```text
Early Result Adapter.analysis_result
-> Analysis Result Merger.early_result

Direct Result Adapter.analysis_result
-> Analysis Result Merger.direct_result

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result

Analysis Result Merger.analysis_result
-> MongoDB Data Store.payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "direct_result": {
    "analysis_result": {
      "success": true,
      "data": [{"production": 100}],
      "analysis_logic": "direct_response"
    }
  },
  "pandas_result": {
    "analysis_result": {
      "skipped": true
    }
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": true,
    "data": [{"production": 100}],
    "analysis_logic": "direct_response",
    "merged_from": "direct_result"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_analysis_result` | `Data(data={"analysis_result": {...}})` | result dict | wrapper를 제거합니다. |
| `merge_analysis_results` | early/direct/pandas | selected result | skipped가 아닌 결과를 선택합니다. |

### 코드 흐름

```text
early_result 확인
-> direct_result 확인
-> pandas_result 확인
-> skipped가 아닌 첫 결과 선택
-> merged_from 표시
```

## 함수 코드 단위 해석: `merge_analysis_results`

### 함수 input

```json
{
  "early_result": {"skipped": true},
  "direct_result": {"success": true, "data": [{"production": 100}]},
  "pandas_result": {"skipped": true}
}
```

### 함수 output

```json
{
  "analysis_result": {
    "success": true,
    "data": [{"production": 100}],
    "merged_from": "direct_result"
  }
}
```

### 핵심 코드 해석

```python
for name, value in candidates:
    result = _analysis_result(value)
```

정해진 순서대로 후보 결과를 확인합니다.

```python
if not result or result.get("skipped"):
    continue
```

비어 있거나 skipped인 branch는 무시합니다.

```python
selected = deepcopy(result)
selected["merged_from"] = name
```

선택된 결과에 어떤 branch에서 왔는지 표시합니다.

```python
return {"analysis_result": selected}
```

뒤쪽 노드가 하나의 결과만 받도록 표준 payload로 반환합니다.

## 추가 함수 코드 단위 해석: `merge_analysis_results`의 우선순위

```python
candidates = [
    ("early_result", _analysis_result(early_result_value)),
    ("direct_result", _analysis_result(direct_result_value)),
    ("pandas_result", _analysis_result(pandas_result_value)),
]
```

세 branch 결과를 같은 형식으로 만든 뒤 정해진 순서대로 검사합니다. 실제 flow에서는 보통 하나만 active입니다.

```python
if not isinstance(result, dict) or not result:
    continue
```

비어 있는 입력은 무시합니다.

```python
if result.get("skipped"):
    skipped.append({"source": source, "skip_reason": result.get("skip_reason", "")})
    continue
```

선택되지 않은 branch는 skipped 목록에만 기록하고 다음 후보를 봅니다.

```python
merged = deepcopy(result)
merged["merged_from"] = source
```

선택된 결과를 복사하고 어느 branch에서 왔는지 표시합니다.

```python
return {"analysis_result": merged}
```

뒤쪽 final answer 노드들은 branch 종류를 몰라도 `analysis_result` 하나만 읽으면 됩니다.
