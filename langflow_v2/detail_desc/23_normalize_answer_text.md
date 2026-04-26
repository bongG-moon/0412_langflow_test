# 23. Normalize Answer Text

## 한 줄 역할

최종 답변 LLM 응답을 파싱해서 `answer_text`로 정리하는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Answer)` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `answer_text` | 자연어 답변, 하이라이트, warnings 등을 담습니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON을 찾습니다.
- `_fallback_answer`: LLM 응답이 없거나 파싱 실패했을 때 규칙 기반 답변을 만듭니다.
- `_fallback_success_answer`: 성공 결과를 사람이 읽을 수 있는 문장으로 만듭니다.
- `normalize_answer_text`: LLM 응답과 fallback을 합쳐 최종 answer_text를 만듭니다.

## 기대 JSON 예시

```json
{
  "answer": "오늘 DA공정 생산량은 총 33,097입니다.",
  "highlights": ["총 12건 기준입니다."]
}
```

## 초보자 포인트

이 노드는 사용자에게 바로 출력하지 않습니다.
문장만 정리하고, 실제 화면용 메시지와 final_result는 `Final Answer Builder`가 만듭니다.

LLM 호출이 실패해도 fallback 답변이 있으므로 테스트가 가능합니다.

## 연결

```text
LLM JSON Caller (Answer).llm_result
-> Normalize Answer Text.llm_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "llm_result": {
    "llm_text": "{\"response\":\"MODE A가 150으로 가장 많습니다.\"}",
    "prompt_payload": {
      "analysis_result": {
        "final_rows": [
          {"MODE": "A", "production": 150}
        ]
      }
    }
  }
}
```

### 출력 예시

```json
{
  "answer_text": {
    "response": "MODE A가 150으로 가장 많습니다.",
    "answer_source": "llm",
    "errors": []
  }
}
```

LLM 응답이 비어 있으면 fallback 답변을 만듭니다.

```json
{
  "answer_text": {
    "response": "총 1건의 결과가 있습니다. MODE A의 production은 150입니다.",
    "answer_source": "fallback"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_extract_json_object` | LLM 텍스트 | JSON dict | 최종 답변 LLM이 JSON 외 문장을 붙여도 response를 꺼냅니다. |
| `_preview_table` | rows | markdown table 문자열 | fallback 답변에서 데이터를 사람이 읽기 쉽게 보여줍니다. |
| `_metric_column` | rows | `"production"` | 숫자 metric 컬럼을 찾아 fallback 문장을 만들 때 씁니다. |
| `_dimension_text` | `{"MODE": "A"}` | `"MODE A"` | row의 차원 정보를 자연어처럼 표현합니다. |
| `_fallback_success_answer` | analysis result | 답변 문장 | LLM이 실패해도 최종 데이터 기반 답변을 만들기 위한 안전장치입니다. |
| `_fallback_answer` | analysis result | 답변 문장 | success/error 상태별 fallback 답변을 고릅니다. |
| `normalize_answer_text` | llm_result | answer_text payload | LLM 답변 JSON을 표준 `response` 형태로 맞춥니다. |
| `build_answer` | Langflow input | `Data(data=answer_text)` | Langflow output method입니다. |

### 코드 흐름

```text
LLM answer text 파싱
-> response 필드 추출
-> 없거나 오류면 analysis_result 기반 fallback 생성
-> Final Answer Builder가 읽을 answer_text 반환
```

### 초보자 포인트

이 노드는 답변의 마지막 안전망입니다. LLM이 JSON을 잘못 주거나 API key가 비어 있어도, 최종 데이터가 있으면 최소한의 답변을 생성합니다.

## 함수 코드 단위 해석: `normalize_answer_text`

이 함수는 최종 답변 LLM의 응답을 `{"response": "..."}` 형태로 정리합니다.

### 함수 input

```json
{
  "llm_result": {
    "llm_text": "{\"response\":\"MODE A가 150으로 가장 많습니다.\"}",
    "prompt_payload": {
      "analysis_result": {
        "data": [{"MODE": "A", "production": 150}]
      }
    }
  }
}
```

### 함수 output

```json
{
  "answer_text": {
    "response": "MODE A가 150으로 가장 많습니다.",
    "answer_source": "llm",
    "errors": []
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
analysis_result = prompt_payload.get("analysis_result") if isinstance(prompt_payload.get("analysis_result"), dict) else {}
```

LLM 답변이 실패했을 때 fallback 답변을 만들기 위해 원래 analysis result를 꺼냅니다.

```python
raw, errors = _parse_jsonish(llm_result.get("llm_text", ""))
```

LLM 응답 JSON을 파싱합니다.

```python
response = str(raw.get("response") or raw.get("answer") or "").strip() if isinstance(raw, dict) else ""
```

LLM이 `response` 대신 `answer`라고 반환해도 답변으로 사용할 수 있게 둘 다 확인합니다.

```python
if not response:
    response = _fallback_answer(analysis_result)
    source = "fallback"
else:
    source = "llm"
```

LLM 답변이 없으면 final data를 보고 fallback 답변을 만듭니다.

```python
return {"answer_text": {"response": response, "answer_source": source, "errors": errors}}
```

Final Answer Builder가 읽을 수 있는 표준 형태로 반환합니다.
