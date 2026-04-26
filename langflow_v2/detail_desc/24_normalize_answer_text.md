# 24. Normalize Answer Text

## 이 노드 역할

최종 답변 LLM의 응답에서 실제 답변 문장만 꺼내 `answer_text`로 정리하는 노드입니다.

LLM 응답이 JSON이 아니거나 답변 필드가 비어 있으면 deterministic fallback 답변을 생성합니다.

## 왜 필요한가

마지막 LLM도 항상 같은 형식으로 답하지 않을 수 있습니다. 예를 들어 `{"answer": "..."}`로 줄 수도 있고, 그냥 문장만 줄 수도 있습니다.

이 노드는 뒤쪽 `Final Answer Builder`가 항상 텍스트를 받을 수 있도록 LLM 응답을 정규화합니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `llm_result` | 최종 답변 생성을 담당한 `LLM JSON Caller`의 출력입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `answer_text` | 최종 사용자 답변에 사용할 자연어 텍스트입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_extract_json_object` | LLM 응답에서 JSON object를 찾아냅니다. |
| `_preview_table` | fallback 답변에 붙일 markdown table을 만듭니다. |
| `_fallback_success_answer` | 성공 결과용 기본 답변을 만듭니다. |
| `_fallback_answer` | 실패/성공 상황에 맞는 fallback 답변을 만듭니다. |
| `normalize_answer_text` | 최종 answer text를 결정합니다. |

## 초보자 확인용

이 노드는 최종 답변 품질을 안정화하는 안전장치입니다.

LLM이 정상적으로 답하면 그 답을 사용하고, LLM 답이 비어 있거나 파싱이 어려우면 분석 결과를 바탕으로 기본 문장을 만들어 줍니다.

## 연결

```text
LLM JSON Caller.llm_result
-> Normalize Answer Text.llm_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "llm_result": {
    "llm_text": "{\"answer\":\"DDR5 생산량은 100입니다.\"}",
    "prompt_payload": {
      "analysis_result": {
        "success": true,
        "data": [{"MODE": "DDR5", "production": 100}]
      }
    }
  }
}
```

### 출력 예시

```json
{
  "answer_text": "DDR5 생산량은 100입니다."
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_extract_json_object` | LLM text | dict | JSON 응답을 추출합니다. |
| `_fallback_success_answer` | analysis result | 문자열 | 성공 결과를 기본 문장으로 요약합니다. |
| `_fallback_answer` | result | 문자열 | 실패면 오류 메시지, 성공이면 요약 답변을 만듭니다. |
| `normalize_answer_text` | llm_result | answer_text | 최종 답변 텍스트를 결정합니다. |

### 코드 흐름

```text
LLM 응답 입력
-> JSON answer 필드 확인
-> text/content/message 필드 확인
-> 비어 있으면 fallback 답변 생성
-> answer_text 출력
```

## 함수 코드 단위 해석: `normalize_answer_text`

### 함수 input

```json
{
  "llm_result": {
    "llm_text": "DDR5 생산량은 100입니다.",
    "prompt_payload": {
      "analysis_result": {
        "success": true,
        "data": [{"MODE": "DDR5", "production": 100}]
      }
    }
  }
}
```

### 함수 output

```json
{
  "answer_text": "DDR5 생산량은 100입니다."
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(llm_result_value)
llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
```

LLM Caller output에서 실제 결과 dict를 꺼냅니다.

```python
raw_text = str(llm_result.get("llm_text") or "")
parsed = _extract_json_object(raw_text)
```

LLM 응답 문자열에서 JSON을 먼저 찾아봅니다.

```python
for key in ("answer", "response", "text", "content", "message"):
```

여러 가능한 답변 필드명을 순서대로 확인합니다.

```python
if answer:
    return {"answer_text": answer}
```

정상 답변이 있으면 그대로 반환합니다.

```python
return {"answer_text": _fallback_answer(analysis_result)}
```

답변을 찾지 못하면 분석 결과를 바탕으로 기본 답변을 만듭니다.

## 추가 함수 코드 단위 해석: `_fallback_success_answer`

최종 답변 LLM이 실패하거나 빈 답변을 반환했을 때 성공 결과를 기본 문장으로 요약하는 함수입니다.

```python
rows = analysis_result.get("data") if isinstance(analysis_result.get("data"), list) else []
rows = [row for row in rows if isinstance(row, dict)]
```

analysis result에서 dict row만 추립니다.

```python
metric = _metric_column(rows)
label = METRIC_LABELS.get(metric, metric or "값")
```

생산량, 목표, 달성률, WIP 같은 대표 metric 컬럼을 찾고 한글 label로 바꿉니다.

```python
if len(rows) == 1:
    dim = _dimension_text(rows[0])
```

결과가 한 건이면 MODE, 공정, 라인, 제품 같은 차원 정보를 함께 문장에 넣습니다.

```python
if top_n:
    return f"가장 {label}이 큰 항목은 {dim}이며 {label}은 {_format_number(rows[0].get(metric))}입니다."
```

top 1 형태의 질문이면 "가장 큰 항목" 문장으로 답합니다.

```python
total = sum(numeric_values)
best = max(rows, key=lambda row: _number(row.get(metric)) if _number(row.get(metric)) is not None else float("-inf"))
```

여러 row가 있으면 합계와 최대 항목을 계산해 기본 요약을 만듭니다.

## 추가 함수 코드 단위 해석: `_preview_table`

fallback 답변에 붙일 markdown table을 만드는 함수입니다.

```python
columns = list(preview[0].keys())[:8]
```

표가 너무 넓어지지 않도록 앞 8개 컬럼만 사용합니다.

```python
text = str(row.get(column, "")).replace("\n", " ").replace("|", "\\|")
values.append(text[:80])
```

markdown table이 깨지지 않도록 줄바꿈과 `|` 문자를 정리하고, 셀 길이를 80자로 제한합니다.

```python
return "\n".join([header, divider, *body])
```

최종적으로 markdown table 문자열을 반환합니다.

## 추가 함수 코드 단위 해석: `normalize_answer_text`의 source 표시

```python
raw_answer = _extract_json_object(str(llm_result.get("llm_text") or ""))
source = "llm"
```

먼저 LLM 응답에서 JSON 답변을 찾고, 기본 source는 `llm`으로 둡니다.

```python
if not answer:
    answer = _fallback_answer(analysis_result)
    source = "fallback"
```

답변을 찾지 못하면 deterministic fallback 답변을 만들고 source를 `fallback`으로 바꿉니다.

```python
return {"answer_text": answer, "answer_source": source, ...}
```

최종 문장뿐 아니라 LLM 답변인지 fallback인지도 함께 반환합니다.
