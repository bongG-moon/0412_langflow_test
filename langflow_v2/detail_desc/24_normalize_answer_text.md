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
