# 18. Normalize Pandas Plan

## 한 줄 역할

LLM이 만든 pandas 분석 계획을 파싱하고, 실행 가능한 `analysis_plan_payload`로 정리하는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Pandas)` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_plan_payload` | pandas 코드, 입력 row, 컬럼, intent plan을 담은 실행 계획입니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON을 찾습니다.
- `_fallback_code`: LLM 응답이 없거나 깨졌을 때 기본 pandas 코드를 만듭니다.
- `normalize_pandas_plan`: 코드, 설명, warnings, retrieval payload를 정리합니다.

## LLM이 기대하는 반환 형태

```json
{
  "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
  "explanation": "MODE별 생산량 합계를 계산합니다."
}
```

## 초보자 포인트

이 노드는 LLM 코드를 바로 실행하지 않습니다.
실행 전 한 번 구조를 정리하는 안전장치입니다.

LLM이 실패해도 fallback code를 만들어 flow가 완전히 멈추지 않게 합니다.

## 연결

```text
LLM JSON Caller (Pandas).llm_result
-> Normalize Pandas Plan.llm_result

Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "llm_result": {
    "llm_text": "{\"code\":\"result_df = df.groupby('MODE', as_index=False)['production'].sum()\",\"explanation\":\"mode별 생산량 합계\"}",
    "prompt_payload": {
      "rows": [
        {"MODE": "A", "production": 100}
      ],
      "columns": ["MODE", "production"]
    }
  }
}
```

### 출력 예시

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result_df = df.groupby('MODE', as_index=False)['production'].sum()",
      "explanation": "mode별 생산량 합계",
      "input_columns": ["MODE", "production"]
    },
    "rows": [
      {"MODE": "A", "production": 100}
    ],
    "columns": ["MODE", "production"],
    "errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_strip_code_fence` | ```json ... ``` | JSON 문자열 | LLM이 코드블록으로 응답해도 파싱 가능하게 합니다. |
| `_extract_json_object` | 설명문 + JSON | JSON dict | LLM 응답에서 실제 JSON 부분만 찾습니다. |
| `_fallback_code` | plan, columns | pandas code 문자열 | LLM 응답이 비어도 기본 groupby/정렬 코드를 만들어 테스트 가능하게 합니다. |
| `normalize_pandas_plan` | llm_result | analysis_plan_payload | LLM 응답을 executor가 이해하는 code/rows/columns 구조로 맞춥니다. |
| `build_plan` | Langflow input | `Data(data=analysis_plan_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
LLM raw text 파싱
-> code/explanation 추출
-> prompt_payload의 rows/columns 유지
-> code가 없으면 fallback code 생성
-> Pandas Analysis Executor에 넘길 plan 반환
```

### 초보자 포인트

LLM이 만든 코드를 바로 실행하지 않고 한 번 표준 형태로 정리합니다. 이 단계가 있어야 executor에서 입력 데이터와 code를 안정적으로 받을 수 있습니다.

## 함수 코드 단위 해석: `normalize_pandas_plan`

이 함수는 Pandas LLM 응답을 executor가 실행할 수 있는 `analysis_plan_payload`로 바꿉니다.

### 함수 input

```json
{
  "llm_result": {
    "llm_text": "{\"code\":\"result = df.groupby('MODE', as_index=False)['production'].sum()\"}",
    "prompt_payload": {
      "rows": [{"MODE": "A", "production": 100}],
      "columns": ["MODE", "production"],
      "plan": {"group_by": ["MODE"]}
    }
  }
}
```

### 함수 output

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
      "source": "llm"
    },
    "rows": [{"MODE": "A", "production": 100}],
    "columns": ["MODE", "production"]
  }
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(llm_result_value)
llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
```

LLM Caller output에서 실제 `llm_result`를 꺼냅니다.

```python
prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
```

LLM 호출 전에 사용했던 rows, columns, plan을 다시 꺼냅니다. executor에 그대로 전달해야 하기 때문입니다.

```python
raw_plan, errors = _parse_jsonish(llm_result.get("llm_text", ""))
```

LLM이 반환한 JSON 문자열을 파싱합니다.

```python
if not isinstance(raw_plan, dict):
    raw_plan = {}
```

파싱 결과가 dict가 아니면 빈 plan으로 처리합니다.

```python
code = str(raw_plan.get("code") or "").strip()
if not code:
    code = _fallback_code(prompt_payload.get("plan", {}), columns)
```

LLM이 code를 못 만들었으면 fallback pandas code를 만듭니다.

```python
analysis_plan = {**raw_plan, "code": code, "source": "llm" if raw_plan.get("code") else "fallback"}
```

최종 실행 계획에 code와 source를 넣습니다. source는 나중에 디버깅할 때 LLM 코드인지 fallback 코드인지 알려줍니다.
