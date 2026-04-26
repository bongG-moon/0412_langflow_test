# 19. Pandas Analysis Executor

## 한 줄 역할

`analysis_plan_payload` 안의 pandas 코드를 실행해서 최종 분석 row를 만드는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `analysis_plan_payload` | `Normalize Pandas Plan` 출력입니다. |
| `retrieval_payload` | 실험용 override입니다. 보통 연결하지 않아도 됩니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | pandas 분석 결과입니다. |

## 주요 함수 설명

- `_merge_sources`: 여러 source result를 pandas DataFrame으로 만들 row list로 합칩니다.
- `_apply_filters`: intent filter를 DataFrame에 적용합니다.
- `_validate_code`: 실행 전에 코드가 너무 위험하지 않은지 간단히 확인합니다.
- `_execute_code`: 제한된 환경에서 pandas 코드를 실행합니다.
- `execute_pandas_analysis`: 전체 실행 과정을 관리합니다.

## 실행 결과 구조

```json
{
  "analysis_result": {
    "success": true,
    "data": [],
    "summary": "분석 결과 ...",
    "intent_plan": {}
  }
}
```

## 초보자 포인트

이 노드는 실제로 코드를 실행하므로 가장 조심해야 하는 부분입니다.

그래서 실행 환경에 `pd`, `df`, `source_frames` 같은 필요한 값만 넣고, 위험한 built-in 사용은 제한합니다.

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
      "code": "result_df = df.groupby('MODE', as_index=False)['production'].sum()"
    },
    "rows": [
      {"MODE": "A", "production": 100},
      {"MODE": "A", "production": 50},
      {"MODE": "B", "production": 30}
    ],
    "columns": ["MODE", "production"]
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": true,
    "result_type": "pandas_analysis",
    "final_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "final_columns": ["MODE", "production"],
    "row_count": 2,
    "errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_analysis_plan_payload` | `{"analysis_plan_payload": {...}}` | plan payload | 앞 노드 출력에서 실제 실행 계획을 꺼냅니다. |
| `_retrieval_payload` | optional retrieval payload | retrieval dict | plan에 rows가 부족하면 원래 조회 결과에서 rows를 보충할 수 있게 합니다. |
| `_merge_sources` | 여러 source_results | 통합 rows/columns | 여러 dataset을 pandas DataFrame 하나로 만들기 위한 준비입니다. |
| `_apply_filters` | DataFrame, filters | 필터 적용 DataFrame | intent filter가 남아 있으면 실행 전에 데이터를 한 번 더 거릅니다. |
| `_validate_code` | pandas code | `(true, "")` 또는 `(false, reason)` | 위험하거나 허용하지 않는 코드를 실행하지 않도록 사전 검사합니다. |
| `_execute_code` | code, rows, plan | final rows/result | 제한된 namespace에서 pandas code를 실행하고 `result_df`를 rows로 바꿉니다. |
| `execute_pandas_analysis` | analysis plan | analysis result | code 실행, 오류 처리, 결과 schema 생성을 담당합니다. |
| `build_result` | Langflow input | `Data(data=analysis_result)` | Langflow output method입니다. |

### 코드 흐름

```text
analysis_plan_payload 입력
-> rows를 pandas DataFrame으로 변환
-> code 안전성 검사
-> 제한된 실행 환경에서 code 실행
-> result_df를 list[dict] final_rows로 변환
-> 최종 analysis_result 반환
```

### 초보자 포인트

LLM은 계산 결과를 직접 만들지 않습니다. LLM은 pandas code 계획만 만들고, 실제 숫자 계산은 이 노드에서 pandas가 수행합니다.

## 함수 코드 단위 해석: `_validate_code`

이 함수는 LLM이 만든 pandas code를 실행하기 전에 위험하거나 잘못된 코드인지 검사합니다.

### 함수 input

```python
"result = df.groupby('MODE', as_index=False)['production'].sum()"
```

### 함수 output

```json
[true, ""]
```

문제가 있으면:

```json
[false, "Forbidden Python node: Import"]
```

### 핵심 코드 해석

```python
tree = ast.parse(code)
```

문자열 code를 Python AST로 바꿉니다. AST는 코드를 실행하지 않고 구조만 분석할 수 있게 해주는 형태입니다.

```python
except SyntaxError as exc:
    return False, f"Generated pandas code syntax error: {exc}"
```

문법 오류가 있으면 실행하지 않고 실패를 반환합니다.

```python
for node in ast.walk(tree):
```

코드 안의 모든 문법 요소를 하나씩 검사합니다.

```python
if isinstance(node, (ast.Import, ast.ImportFrom, ast.With, ast.Try, ast.While, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.Delete)):
    return False, f"Forbidden Python node: {type(node).__name__}"
```

LLM이 만든 코드가 import, class, while 같은 위험하거나 필요 없는 문법을 쓰면 차단합니다. pandas 집계에는 이런 문법이 필요하지 않기 때문입니다.

```python
if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
    return False, f"Forbidden Python name: {node.id}"
```

`open`, `exec`, `eval` 같은 위험한 이름을 쓰지 못하게 막습니다.

```python
if isinstance(node, ast.Assign):
    has_result = has_result or any(isinstance(target, ast.Name) and target.id == "result" for target in node.targets)
```

이 executor는 최종 결과를 `result` 변수에서 읽습니다. 그래서 코드가 `result = ...`를 반드시 포함하는지 검사합니다.

```python
return (True, "") if has_result else (False, "Generated pandas code must assign result.")
```

`result`를 만들면 통과, 만들지 않으면 실패입니다.

## 함수 코드 단위 해석: `_execute_code`

이 함수는 검증된 pandas code를 실제로 실행합니다.

### 함수 input

```json
{
  "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
  "rows": [
    {"MODE": "A", "production": 100},
    {"MODE": "A", "production": 50},
    {"MODE": "B", "production": 30}
  ],
  "plan": {
    "filters": {}
  }
}
```

### 함수 output

```json
{
  "success": true,
  "data": [
    {"MODE": "A", "production": 150},
    {"MODE": "B", "production": 30}
  ],
  "filter_notes": []
}
```

### 핵심 코드 해석

```python
frame = pd.DataFrame(rows or [])
```

list of dict를 pandas DataFrame으로 바꿉니다. pandas 계산은 DataFrame을 기준으로 합니다.

```python
frame, filter_notes = _apply_filters(frame, plan.get("filters", {}) if isinstance(plan.get("filters"), dict) else {})
```

plan에 filter가 있으면 DataFrame에 먼저 적용합니다. `filter_notes`에는 몇 건에서 몇 건으로 줄었는지 기록됩니다.

```python
ok, error = _validate_code(code)
if not ok:
    return {"success": False, "error_message": error, "data": [], "filter_notes": filter_notes}
```

코드 검증이 실패하면 실행하지 않고 오류를 반환합니다.

```python
local_vars = {"df": frame.copy(), "pd": pd, "result": None}
```

LLM code가 사용할 수 있는 변수들을 준비합니다.

- `df`: 입력 데이터 DataFrame
- `pd`: pandas module
- `result`: 최종 결과를 담아야 하는 변수

```python
exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
```

실제 코드 실행 부분입니다. `SAFE_BUILTINS`만 허용해서 아무 Python 기능이나 쓰지 못하게 제한합니다.

```python
result = local_vars.get("result")
```

실행이 끝난 뒤 LLM code가 만든 `result` 변수를 꺼냅니다.

```python
if isinstance(result, pd.Series):
    result = result.to_frame().reset_index()
```

결과가 Series이면 DataFrame으로 바꿉니다. 뒤 노드는 row list를 기대하기 때문입니다.

```python
if not isinstance(result, pd.DataFrame):
    return {"success": False, "error_message": "Pandas code result is not a DataFrame.", "data": [], "filter_notes": filter_notes}
```

최종 결과가 DataFrame이 아니면 실패 처리합니다.

```python
result = result.where(pd.notnull(result), None)
return {"success": True, "data": result.to_dict(orient="records"), "filter_notes": filter_notes}
```

NaN 값을 JSON에서 다루기 쉬운 `None`으로 바꾸고, DataFrame을 `list[dict]`로 바꿔 반환합니다.

## 추가 함수 코드 단위 해석: `execute_pandas_analysis`

이 함수는 pandas 분석 노드의 최상위 실행 함수입니다. plan을 꺼내고, 데이터가 있는지 확인하고, 코드를 실행하고, 최종 analysis result를 만듭니다.

### 함수 input

```json
{
  "analysis_plan_payload_value": {
    "analysis_plan_payload": {
      "analysis_plan": {
        "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
        "source": "llm"
      },
      "rows": [
        {"MODE": "A", "production": 100},
        {"MODE": "A", "production": 50}
      ],
      "columns": ["MODE", "production"]
    }
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "analyze_current_data",
    "data": [
      {"MODE": "A", "production": 150}
    ],
    "summary": "data analysis complete: 1 rows",
    "analysis_logic": "llm",
    "generated_code": "result = df.groupby('MODE', as_index=False)['production'].sum()"
  }
}
```

### 핵심 코드 해석

```python
payload = _analysis_plan_payload(analysis_plan_payload_value)
```

앞 노드에서 온 값을 표준 analysis plan payload로 꺼냅니다.

```python
retrieval = payload.get("retrieval_payload") if isinstance(payload.get("retrieval_payload"), dict) else {}
if retrieval_payload_value is not None:
    override = _retrieval_payload(retrieval_payload_value)
    if override:
        retrieval = override
```

기본적으로 plan payload 안의 retrieval 정보를 쓰지만, 실험용으로 별도 retrieval payload가 연결되면 그것으로 덮어쓸 수 있습니다.

```python
if payload.get("skipped") or retrieval.get("skipped"):
    result = {"skipped": True, ...}
    return {"analysis_result": result}
```

선택되지 않은 branch라면 pandas를 실행하지 않고 skipped result를 반환합니다.

```python
table = payload.get("table") if isinstance(payload.get("table"), dict) and payload.get("table") else _merge_sources(source_results)
```

분석할 table을 준비합니다. 이미 table이 있으면 그것을 쓰고, 없으면 source_results를 병합합니다.

```python
if not table.get("success") or not rows:
    result = {"success": False, "analysis_logic": "no_data", ...}
    return {"analysis_result": result}
```

분석할 데이터가 없으면 pandas 실행을 하지 않습니다.

```python
code = str(analysis_plan.get("code") or "").strip()
if not code:
    code = _fallback_code(plan, [str(column) for column in columns])
```

LLM이 code를 만들지 못했으면 fallback code를 생성합니다.

```python
executed = _execute_code(code, rows, plan)
```

실제 pandas 실행은 `_execute_code`에 맡깁니다.

```python
if not executed.get("success") and analysis_logic == "llm":
    fallback = _fallback_code(plan, [str(column) for column in columns])
    executed = _execute_code(fallback, rows, plan)
```

LLM code가 실패하면 fallback code로 한 번 더 시도합니다.

```python
result_rows = executed.get("data", []) if executed.get("success") else []
```

실행 성공 시 최종 row를 꺼냅니다. 실패하면 빈 list입니다.

```python
result = {
    "success": bool(executed.get("success")),
    "data": _json_safe(result_rows),
    "summary": ...,
    "generated_code": code,
    "source_results": source_results,
    "intent_plan": plan,
    "state": state,
}
```

최종 답변 builder가 읽을 표준 analysis result를 만듭니다. 여기에는 계산 결과뿐 아니라 사용한 코드, 원본 source, intent plan, state도 같이 들어갑니다.
