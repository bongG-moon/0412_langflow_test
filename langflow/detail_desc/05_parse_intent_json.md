# 05. Parse Intent JSON 상세 설명

대상 코드: `langflow/data_answer_flow/05_parse_intent_json.py`

이 노드는 LLM 응답 텍스트를 실제 intent dict로 파싱한다. LLM은 JSON만 반환하도록 요청받지만, 실제로는 markdown fence나 설명 문장이 섞일 수 있으므로 이를 최대한 복구해서 표준 intent 형태로 보정한다.

## 전체 역할

입력으로 LLM 결과를 받는다.

그리고 다음 작업을 한다.

- LLM 응답 텍스트를 꺼낸다.
- markdown JSON 코드블록이 있으면 내부 JSON만 추출한다.
- 텍스트 중 `{ ... }` JSON object 부분만 찾아낸다.
- JSON parse를 시도한다.
- 누락 필드나 잘못된 타입을 기본 schema로 보정한다.
- parse error를 함께 반환한다.

출력 구조는 다음과 같다.

```json
{
  "intent_raw": {
    "request_type": "data_question",
    "query_summary": "",
    "dataset_hints": [],
    "metric_hints": [],
    "required_params": {},
    "filters": {},
    "group_by": [],
    "sort": null,
    "top_n": null,
    "calculation_hints": [],
    "followup_cues": [],
    "confidence": 0.0
  },
  "parse_errors": []
}
```

## 기본 intent schema

```python
DEFAULT_INTENT: Dict[str, Any] = {
    "request_type": "unknown",
    "query_summary": "",
    "dataset_hints": [],
    "metric_hints": [],
    "required_params": {},
    "filters": {},
    "group_by": [],
    "sort": None,
    "top_n": None,
    "calculation_hints": [],
    "followup_cues": [],
    "confidence": 0.0,
}
```

LLM 결과가 비어 있거나 파싱에 실패했을 때 사용할 기본 intent다.

또한 LLM이 일부 필드를 누락해도 이 기본값을 먼저 깔고 LLM 값을 덮어쓰므로 출력 구조가 항상 일정해진다.

## payload 추출

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

Langflow 입력값에서 dict payload를 꺼낸다.

```python
if value is None:
    return {}
if isinstance(value, dict):
    return value
```

입력이 없으면 빈 dict, 이미 dict면 그대로 반환한다.

```python
data = getattr(value, "data", None)
if isinstance(data, dict):
    return data
```

Langflow `Data` 객체의 `.data`를 사용한다.

```python
text = getattr(value, "text", None)
if isinstance(text, str):
    return {"text": text}
```

`.text`가 있으면 JSON으로 파싱하지 않고 텍스트로 감싼다. LLM 응답은 JSON일 수도 있지만 markdown이 섞인 일반 텍스트일 수도 있기 때문이다.

## LLM 텍스트 읽기

```python
def _read_text(value: Any) -> str:
```

LLM 응답에서 실제 문자열을 추출한다.

```python
if isinstance(value, str):
    return value.strip()
```

문자열이 직접 들어오면 사용한다.

```python
payload = _payload_from_value(value)
for key in ("llm_text", "text", "content"):
    if isinstance(payload.get(key), str):
        return payload[key].strip()
```

payload에서 `llm_text`, `text`, `content` 순서로 문자열을 찾는다.

`LLM JSON Caller`는 `llm_text`를 반환하므로 보통 첫 번째 key에서 찾는다.

```python
text = getattr(value, "text", None)
return str(text or "").strip()
```

fallback으로 `.text` 속성을 사용한다.

## JSON object 추출

```python
def _extract_json_object(text: str) -> str:
```

LLM 응답 텍스트에서 JSON object만 잘라내는 함수다.

```python
text = text.strip()
```

앞뒤 공백을 제거한다.

```python
fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
```

markdown 코드블록을 찾는다.

`(?:json)?`는 ```json 또는 ``` 둘 다 허용한다.

`re.DOTALL`은 줄바꿈이 있어도 `.*?`가 매칭되도록 한다.

```python
if fenced:
    text = fenced.group(1).strip()
```

코드블록이 있으면 내부 내용만 사용한다.

```python
if text.startswith("{") and text.endswith("}"):
    return text
```

이미 JSON object처럼 시작하고 끝나면 그대로 반환한다.

```python
start = text.find("{")
end = text.rfind("}")
if start >= 0 and end > start:
    return text[start : end + 1]
```

설명 문장이 섞여 있으면 첫 `{`부터 마지막 `}`까지 잘라낸다.

```python
return text
```

JSON object를 찾지 못하면 원문을 반환한다. 이후 `json.loads`에서 실패 처리된다.

## list 변환

```python
def _as_list(value: Any) -> list[Any]:
```

값을 list로 통일한다.

LLM이 `"dataset_hints": "production"`처럼 문자열 하나를 반환해도 `["production"]`으로 보정하기 위한 helper다.

## intent 형태 보정

```python
def _normalize_intent_shape(value: Any, errors: list[str]) -> Dict[str, Any]:
```

파싱된 JSON을 표준 intent 구조로 맞춘다.

```python
if not isinstance(value, dict):
    errors.append("Parsed intent is not an object.")
    return dict(DEFAULT_INTENT)
```

파싱 결과가 object가 아니면 기본 intent를 반환한다.

```python
intent = dict(DEFAULT_INTENT)
intent.update(value)
```

기본 intent를 복사한 뒤 LLM 결과를 덮어쓴다. 누락 필드는 기본값이 유지된다.

```python
if intent.get("request_type") not in {"data_question", "process_execution", "unknown"}:
    errors.append("Invalid request_type; using unknown.")
    intent["request_type"] = "unknown"
```

request_type은 허용된 세 값 중 하나여야 한다. 아니면 unknown으로 보정한다.

```python
for key in ("dataset_hints", "metric_hints", "group_by", "calculation_hints", "followup_cues"):
    intent[key] = [str(item) for item in _as_list(intent.get(key)) if str(item).strip()]
```

list여야 하는 필드를 문자열 list로 보정한다. 빈 값은 제거한다.

```python
if not isinstance(intent.get("required_params"), dict):
    intent["required_params"] = {}
if not isinstance(intent.get("filters"), dict):
    intent["filters"] = {}
```

required_params와 filters는 dict여야 한다. 아니면 빈 dict로 보정한다.

```python
if intent.get("sort") is not None and not isinstance(intent.get("sort"), dict):
    intent["sort"] = None
```

sort는 dict 또는 None이어야 한다. 다른 타입이면 None으로 둔다.

```python
try:
    intent["confidence"] = float(intent.get("confidence") or 0.0)
except Exception:
    intent["confidence"] = 0.0
```

confidence를 float으로 변환한다. 실패하면 0.0이다.

```python
return intent
```

보정된 intent를 반환한다.

## 핵심 함수: parse_intent_json

```python
def parse_intent_json(llm_text: Any) -> Dict[str, Any]:
```

LLM 응답을 intent payload로 바꾸는 핵심 함수다.

```python
text = _read_text(llm_text)
errors: list[str] = []
```

LLM 텍스트를 읽고 에러 리스트를 준비한다.

```python
if not text:
    errors.append("llm_text is empty.")
    intent = dict(DEFAULT_INTENT)
```

응답이 비어 있으면 기본 intent를 사용한다.

```python
else:
    try:
        parsed = json.loads(_extract_json_object(text))
        intent = _normalize_intent_shape(parsed, errors)
    except Exception as exc:
        errors.append(f"Intent JSON parse failed: {exc}")
        intent = dict(DEFAULT_INTENT)
```

응답이 있으면 JSON object를 추출하고 파싱한다. 성공하면 형태를 보정한다. 실패하면 parse error를 담고 기본 intent를 사용한다.

```python
return {"intent_raw": intent, "parse_errors": errors}
```

최종 payload를 반환한다.

## Component 입력

```python
DataInput(
    name="llm_result",
    display_name="LLM Result",
    input_types=["Data", "JSON"],
)
```

`LLM JSON Caller.llm_result`를 연결받는 입력이다.

```python
MultilineInput(name="llm_text", display_name="LLM Text", value="", advanced=True)
```

디버깅용 직접 입력이다. LLM Result 연결 없이 텍스트를 붙여 넣어 parser만 테스트할 수 있다.

## Component 출력

```python
Output(name="intent_raw", display_name="Intent Raw", method="build_intent_raw", types=["Data"])
```

파싱된 intent raw payload를 출력한다.

## 실행 메서드

```python
def build_intent_raw(self) -> Data:
```

Langflow output 요청 시 실행된다.

```python
value = getattr(self, "llm_result", None) or getattr(self, "llm_text", "")
```

연결된 LLM Result를 우선 사용한다. 없으면 직접 입력된 LLM Text를 사용한다.

```python
payload = parse_intent_json(value)
```

핵심 함수로 LLM 응답을 intent payload로 변환한다.

```python
return _make_data(payload)
```

payload를 Data로 반환한다. `intent_raw`와 파싱 상태는 모두 `.data` 안의 key로 확인한다.

## 다음 노드 연결

```text
Parse Intent JSON.intent_raw -> Normalize Intent With Domain.intent_raw
```

## 학습 포인트

LLM 응답은 항상 완벽한 JSON이라고 가정하면 안 된다. 이 노드는 LLM 응답의 흔한 흔들림을 흡수한다.

특히 markdown code fence 제거, JSON object 부분 추출, 기본 schema 보정이 핵심이다.
