# 19. Normalize Pandas Plan

## 이 노드 역할

Pandas 코드 생성을 담당한 LLM 응답을 파싱하고, 실행 노드가 사용할 수 있는 `analysis_plan_payload` 형태로 정리하는 노드입니다.

LLM이 JSON을 깔끔하게 주지 않거나 코드가 비어 있어도 fallback code를 만들어 flow가 중단되지 않도록 합니다.

## 왜 필요한가

LLM 응답은 항상 완벽한 JSON이라고 보장할 수 없습니다. 코드블록 안에 JSON이 들어가거나, 설명 문장과 JSON이 섞이거나, `code` 필드가 비어 있을 수 있습니다.

이 노드는 그런 응답을 실행 가능한 구조로 정규화합니다. 실제 코드 실행은 다음 단계인 `Pandas Analysis Executor`에서 수행합니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `llm_result` | pandas 코드 생성용 `LLM JSON Caller`의 출력입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `analysis_plan_payload` | pandas 실행 코드, 원본 rows/columns, intent plan이 포함된 실행 계획입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_extract_json_object` | LLM 응답 문자열에서 JSON object를 찾아냅니다. |
| `_fallback_code` | LLM 코드가 없을 때 기본 pandas 코드를 만듭니다. |
| `normalize_pandas_plan` | LLM 응답과 prompt payload를 합쳐 실행 계획을 만듭니다. |

## 초보자 확인용

이 노드는 LLM이 만든 코드를 바로 실행하지 않습니다. 먼저 코드와 설명, warnings를 안전하게 꺼내고, `rows`, `columns`, `retrieval_payload`를 함께 묶어 다음 노드로 넘깁니다.

## 연결

```text
LLM JSON Caller.llm_result
-> Normalize Pandas Plan.llm_result

Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "llm_result": {
    "llm_text": "{\"code\":\"result = df.groupby(['MODE'], as_index=False)['production'].sum()\",\"explanation\":\"MODE별 생산량 합계\"}",
    "prompt_payload": {
      "rows": [
        {"MODE": "DDR5", "production": 100}
      ],
      "columns": ["MODE", "production"],
      "plan": {"group_by": ["MODE"]}
    }
  }
}
```

### 출력 예시

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result = df.groupby(['MODE'], as_index=False)['production'].sum()",
      "explanation": "MODE별 생산량 합계",
      "source": "llm"
    },
    "rows": [
      {"MODE": "DDR5", "production": 100}
    ],
    "columns": ["MODE", "production"]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_extract_json_object` | LLM text | dict 또는 `{}` | 응답 안에서 JSON object를 찾습니다. |
| `_fallback_code` | plan, columns | pandas code | group_by, sort, top_n 등을 기반으로 기본 코드를 만듭니다. |
| `normalize_pandas_plan` | llm_result | analysis_plan_payload | 실행 노드가 읽는 표준 구조로 변환합니다. |

### 코드 흐름

```text
LLM 응답 입력
-> prompt_payload에서 rows/columns/plan 복원
-> LLM text에서 JSON 추출
-> code가 없으면 fallback code 생성
-> analysis_plan_payload 출력
```

## 함수 코드 단위 해석: `normalize_pandas_plan`

### 함수 input

```json
{
  "llm_result": {
    "llm_text": "{\"code\":\"result = df.copy()\"}",
    "prompt_payload": {
      "rows": [{"production": 100}],
      "columns": ["production"],
      "plan": {}
    }
  }
}
```

### 함수 output

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result = df.copy()",
      "source": "llm"
    },
    "rows": [{"production": 100}],
    "columns": ["production"]
  }
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(llm_result_value)
llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
```

Langflow Data wrapper에서 실제 LLM 결과를 꺼냅니다.

```python
prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
```

LLM 호출 전에 사용했던 rows, columns, intent plan을 다시 가져옵니다.

```python
raw_plan = _extract_json_object(text)
```

LLM 응답 문자열에서 JSON object를 추출합니다.

```python
code = str(raw_plan.get("code") or "").strip()
if not code:
    code = _fallback_code(prompt_payload.get("plan", {}), columns)
```

LLM이 code를 주지 않았으면 기본 pandas 코드를 생성합니다.

```python
analysis_plan = {**raw_plan, "code": code, "source": "llm" if raw_plan.get("code") else "fallback"}
```

코드가 LLM에서 온 것인지 fallback인지 표시합니다. 이 값은 나중에 실행 결과의 `analysis_logic`으로 이어집니다.
