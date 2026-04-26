# 19. Normalize Pandas Plan

## 최근 변경: domain 기반 fallback 계산

이 노드의 fallback 코드는 더 이상 `production`, `target`, `achievement_rate` 같은 제조 metric 이름을 Python 코드에 직접 고정하지 않습니다.

LLM이 pandas 코드를 주지 못했을 때는 `intent_plan.metric_keys`, `intent_plan.metric_definitions`, `prompt_payload.domain.metrics`, `domain.datasets.<dataset_key>.primary_quantity_column`, 실제 table row의 숫자형 컬럼을 기준으로 계산 대상을 찾습니다.

metric 계산은 domain metric에 등록된 `source_columns`, `formula`, `output_column`을 사용합니다.

```json
{
  "metrics": {
    "good_rate": {
      "source_columns": ["pass_qty", "input_qty"],
      "formula": "sum(pass_qty) / sum(input_qty) * 100",
      "output_column": "good_rate"
    }
  }
}
```

위처럼 등록하면 fallback code는 `pass_qty`, `input_qty`를 group_by 기준으로 합산한 뒤 `good_rate`를 계산합니다. 새로운 metric을 추가할 때 Python 코드를 수정하지 않고 domain 정의를 수정하는 방식으로 확장합니다.

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

## 추가 함수 코드 단위 해석: `_fallback_code`

LLM이 pandas code를 주지 못했을 때 사용할 기본 코드를 만드는 함수입니다.

```python
group_by = [column for column in _as_list(plan.get("group_by")) if str(column) in columns]
```

intent plan의 group_by 중 실제 컬럼에 존재하는 값만 사용합니다.

```python
numeric_priority = ["production", "target", "achievement_rate", "wip_qty", ...]
numeric_cols = [column for column in numeric_priority if column in columns]
```

제조 데이터에서 자주 쓰는 numeric metric 컬럼을 우선순위대로 찾습니다.

```python
if sort_column:
    suffix += f"\nif {sort_column!r} in result.columns:\n    result = result.sort_values({sort_column!r}, ascending={ascending!r})"
```

정렬 요청이 있으면 결과 DataFrame에 해당 컬럼이 있을 때만 정렬하도록 안전한 코드를 붙입니다.

```python
if "production" in columns and "target" in columns:
```

생산량과 목표가 함께 있으면 달성률 계산 코드를 우선 생성합니다.

```python
result['achievement_rate'] = None
mask = result['target'].notna() & (result['target'] != 0)
result.loc[mask, 'achievement_rate'] = result.loc[mask, 'production'] / result.loc[mask, 'target'] * 100
```

target이 0이거나 null인 경우 나눗셈 오류가 나지 않도록 mask를 적용합니다.

```python
return "result = df.copy()" + suffix
```

집계할 숫자 컬럼을 찾지 못하면 원본 table을 그대로 반환하는 pass-through 코드를 만듭니다.

## 추가 함수 코드 단위 해석: `normalize_pandas_plan`의 source 결정

```python
if not plan.get("needs_pandas", True):
    code = "result = df.copy()"
    source = "direct_table"
```

intent plan상 pandas 분석이 필요 없으면 DataFrame을 그대로 반환하는 코드로 고정합니다.

```python
elif not code:
    code = _fallback_code(plan if isinstance(plan, dict) else {}, columns)
    source = "fallback"
```

LLM 응답에 code가 없으면 deterministic fallback code를 사용합니다.

```python
"warnings": _unique_strings([*_as_list(raw_plan.get("warnings") if isinstance(raw_plan, dict) else []), *warnings])
```

LLM 파싱 오류나 LLM이 직접 준 경고를 중복 제거해서 보존합니다.
