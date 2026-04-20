# 04. LLM JSON Caller 상세 설명

대상 코드: `langflow/data_answer_flow/04_llm_json_caller.py`

이 노드는 prompt를 받아 LLM API를 호출하고, JSON 형태 응답을 기대하는 텍스트를 반환한다. 현재 구현은 `langchain_google_genai.ChatGoogleGenerativeAI` 기반이지만, 노드 이름과 함수 이름은 특정 provider를 강하게 드러내지 않도록 범용적인 `LLM` 표현을 사용한다.

## 전체 역할

입력으로 prompt, API key, model name, temperature, timeout을 받는다.

그리고 다음 작업을 한다.

- prompt payload에서 실제 prompt 문자열을 추출한다.
- Secret input에서 API key를 안전하게 읽는다.
- model name과 실행 옵션을 정리한다.
- `ChatGoogleGenerativeAI`로 LLM을 호출한다.
- 응답에서 텍스트를 추출한다.
- 성공/실패 debug 정보를 함께 반환한다.

출력 구조는 다음과 같다.

```json
{
  "llm_text": "{...}",
  "llm_debug": {
    "provider": "langchain_google_genai",
    "model_name": "gemini-flash-latest",
    "prompt_chars": 1200,
    "ok": true,
    "error": null,
    "response_chars": 500
  }
}
```

## import 영역

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 일부 payload 처리에 사용한다. `dataclass`, `import_module`, `Any`, `Dict`는 Langflow 호환 공통부와 타입 힌트용이다.

## Langflow와 LLM 클래스 로딩

```python
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
SecretStrInput = _load_attr(["lfx.io", "langflow.io"], "SecretStrInput", _make_input)
```

이 노드는 prompt를 `DataInput`으로 받고, model name 같은 일반 문자열은 `MessageTextInput`으로 받는다. API key는 노출되면 안 되므로 `SecretStrInput`을 사용한다.

```python
ChatGoogleGenerativeAI = _load_attr(
    ["langchain_google_genai"],
    "ChatGoogleGenerativeAI",
    None,
)
```

`langchain_google_genai` 패키지에서 `ChatGoogleGenerativeAI` 클래스를 찾는다. 설치되어 있지 않으면 `None`을 반환한다.

이 구조 덕분에 import 단계에서 바로 죽지 않고, 실행 시점에 `"langchain_google_genai is not installed"`라는 debug error를 반환할 수 있다.

## payload 추출 함수

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

입력값에서 dict payload를 꺼낸다.

```python
if value is None:
    return {}
if isinstance(value, dict):
    return value
```

없으면 빈 dict, 이미 dict면 그대로 반환한다.

```python
data = getattr(value, "data", None)
if isinstance(data, dict):
    return data
```

Langflow `Data` 객체의 `.data`를 읽는다.

```python
text = getattr(value, "text", None)
if isinstance(text, str):
    return {"text": text}
```

이 노드에서는 `.text`를 JSON으로 파싱하지 않고 `{"text": text}`로 감싼다. prompt는 일반 문자열이므로 JSON일 필요가 없기 때문이다.

## Secret 읽기

```python
def _read_secret(value: Any) -> str:
```

Langflow Secret input에서 실제 문자열을 꺼낸다.

```python
if value is None:
    return ""
```

값이 없으면 빈 문자열이다.

```python
if hasattr(value, "get_secret_value"):
```

Pydantic SecretStr 같은 객체는 실제 값을 `get_secret_value()`로 꺼낸다.

```python
try:
    return str(value.get_secret_value() or "").strip()
except Exception:
    return ""
```

secret 값을 안전하게 문자열로 변환한다. 실패하면 빈 문자열이다.

```python
return str(value or "").strip()
```

일반 문자열로 들어온 경우를 처리한다.

## prompt 읽기

```python
def _read_prompt(value: Any) -> str:
```

입력 payload에서 실제 prompt 문자열을 찾는다.

```python
if isinstance(value, str):
    return value
```

문자열이 직접 들어오면 그대로 사용한다.

```python
payload = _payload_from_value(value)
for key in ("prompt", "intent_prompt", "retrieval_plan_prompt", "pandas_code_prompt", "text"):
    if isinstance(payload.get(key), str):
        return payload[key]
```

payload에서 prompt로 쓸 수 있는 key를 순서대로 찾는다.

`intent_prompt`만이 아니라 `retrieval_plan_prompt`, `pandas_code_prompt`도 보는 이유는 이 LLM Caller를 나중에 다른 prompt builder에도 재사용하기 위해서다.

```python
text = getattr(value, "text", None)
return str(text or "").strip()
```

마지막으로 `.text` 속성을 fallback으로 사용한다.

## 응답 텍스트 추출

```python
def _extract_text_from_response(content: Any) -> str:
```

LLM 응답 content에서 문자열을 꺼낸다.

```python
if isinstance(content, str):
    return content.strip()
```

content가 문자열이면 앞뒤 공백 제거 후 반환한다.

```python
if isinstance(content, list):
    parts: list[str] = []
```

일부 LLM 응답은 content가 list 형태일 수 있다. 이 경우 각 조각을 이어 붙인다.

```python
for item in content:
    if isinstance(item, str):
        parts.append(item)
    elif isinstance(item, dict) and isinstance(item.get("text"), str):
        parts.append(item["text"])
    elif hasattr(item, "text"):
        parts.append(str(getattr(item, "text") or ""))
```

list item이 문자열, dict, text 속성을 가진 객체인 경우를 각각 처리한다.

```python
return "".join(parts).strip()
```

조각들을 이어 붙이고 공백을 제거한다.

```python
return str(content or "").strip()
```

그 외 타입은 문자열로 변환한다.

## 핵심 함수: call_llm_json

```python
def call_llm_json(
    prompt: Any,
    llm_api_key: Any,
    model_name: str,
    temperature: Any,
    timeout_seconds: Any,
) -> Dict[str, Any]:
```

LLM 호출 핵심 함수다.

```python
prompt_text = _read_prompt(prompt)
api_key = _read_secret(llm_api_key)
model = str(model_name or "").strip() or "gemini-flash-latest"
```

prompt, API key, model name을 정리한다. model name이 비어 있으면 기본값을 사용한다.

```python
debug = {
    "provider": "langchain_google_genai",
    "model_name": model,
    "prompt_chars": len(prompt_text),
    "ok": False,
    "error": None,
}
```

호출 결과를 추적하기 위한 debug payload를 만든다.

```python
if not prompt_text:
    debug["error"] = "prompt is empty"
    return {"llm_text": "", "llm_debug": debug}
```

prompt가 없으면 호출하지 않고 에러 payload를 반환한다.

```python
if not api_key:
    debug["error"] = "llm_api_key is empty"
    return {"llm_text": "", "llm_debug": debug}
```

API key가 없으면 호출하지 않는다.

```python
if ChatGoogleGenerativeAI is None:
    debug["error"] = "langchain_google_genai is not installed"
    return {"llm_text": "", "llm_debug": debug}
```

필요 패키지가 없으면 실행 불가 상태를 반환한다.

```python
try:
    temp = float(temperature)
except Exception:
    temp = 0.0
```

temperature 입력을 float으로 변환한다. 실패하면 0.0이다.

```python
try:
    timeout = float(timeout_seconds)
except Exception:
    timeout = 60.0
```

timeout도 float으로 변환한다. 실패하면 60초다.

```python
try:
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temp,
        timeout=timeout,
    )
```

LLM 객체를 생성한다. 현재 실제 호출 구현은 Google GenAI 기반이다.

```python
response = llm.invoke(
    [
        ("system", "Return only valid JSON. Do not include markdown fences."),
        ("human", prompt_text),
    ]
)
```

system message와 human message를 넣어 LLM을 호출한다.

system message는 JSON만 반환하라고 강하게 제한한다.

```python
text = _extract_text_from_response(getattr(response, "content", response))
```

응답 객체의 `.content`를 우선 읽고, 없으면 응답 자체에서 텍스트를 추출한다.

```python
if not text:
    debug["error"] = "empty LLM response text"
    return {"llm_text": "", "llm_debug": debug}
```

응답 텍스트가 비어 있으면 에러로 처리한다.

```python
except Exception:
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temp,
        )
```

첫 번째 호출이 실패하면 timeout 인자 없이 한 번 더 시도한다. 일부 환경이나 버전에서 `timeout` 인자를 지원하지 않을 수 있기 때문이다.

```python
except Exception as exc:
    debug["error"] = str(exc)
    return {"llm_text": "", "llm_debug": debug}
```

두 번째 시도도 실패하면 에러 메시지를 debug에 담아 반환한다.

```python
debug["ok"] = True
debug["response_chars"] = len(text or "")
return {"llm_text": text or "", "llm_debug": debug}
```

성공하면 `ok=True`, 응답 길이를 기록하고 `llm_text`를 반환한다.

## Component 입력

```python
DataInput(name="prompt", ...)
```

Prompt Builder의 출력이다.

```python
SecretStrInput(name="llm_api_key", ...)
```

LLM API key다. 노드마다 별도로 입력받는 구조다.

```python
MessageTextInput(name="model_name", value="gemini-flash-latest")
```

사용할 모델명이다. 빠른 모델이 필요하면 빠른 모델명을, 복잡한 reasoning이 필요하면 더 강한 모델명을 여기에 넣는 방식이다.

```python
MessageTextInput(name="temperature", value="0", advanced=True)
MessageTextInput(name="timeout_seconds", value="60", advanced=True)
```

고급 설정으로 숨겨진 실행 옵션이다.

## Component 출력

```python
Output(name="llm_result", display_name="LLM Result", method="call_llm", types=["Data"])
```

LLM 호출 결과를 출력한다.

## 실행 메서드

```python
def call_llm(self) -> Data:
```

Langflow output 요청 시 실행된다.

```python
payload = call_llm_json(
    getattr(self, "prompt", None),
    getattr(self, "llm_api_key", None),
    getattr(self, "model_name", ""),
    getattr(self, "temperature", "0"),
    getattr(self, "timeout_seconds", "60"),
)
```

Component input 값을 읽어 핵심 함수로 전달한다.

```python
return _make_data(payload)
```

결과 payload를 `Data`로 감싸 반환한다. LLM 응답 텍스트는 `.data["llm_text"]`에서 확인한다.

## 다음 노드 연결

```text
Build Intent Prompt.intent_prompt -> LLM JSON Caller.prompt
LLM JSON Caller.llm_result -> Parse Intent JSON.llm_result
```

## 학습 포인트

이 노드는 범용 LLM 호출 노드 패턴이다.

중요한 구조는 세 가지다.

- prompt builder와 LLM caller를 분리한다.
- API key와 model은 노드마다 직접 입력받는다.
- 실패해도 flow 전체가 바로 죽지 않도록 `llm_debug`에 에러를 담아 반환한다.
