# 06. LLM JSON Caller

## 한 줄 역할

앞 노드가 만든 prompt를 LLM에 보내고, LLM 응답 텍스트를 `llm_result`로 반환합니다.

## 어디에 쓰나?

이 노드는 같은 파일을 Langflow 화면에 세 번 올려서 사용합니다.

1. `LLM JSON Caller (Intent)`: 사용자 의도 분류
2. `LLM JSON Caller (Pandas)`: pandas 코드 계획 생성
3. `LLM JSON Caller (Answer)`: 최종 자연어 답변 생성

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | prompt 문자열과 관련 context입니다. |
| `llm_api_key` | LLM API key입니다. 비우면 뒤 normalize 노드의 fallback이 동작합니다. |
| `model_name` | 사용할 모델 이름입니다. API key를 넣으면 함께 입력해야 합니다. |
| `temperature` | 답변의 랜덤성입니다. 보통 `0`을 권장합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `llm_result` | LLM 원문 응답, 에러 목록, 원래 prompt_payload를 포함합니다. |

## 주요 함수 설명

- `_payload_from_value`: `prompt_payload`를 dict로 꺼냅니다.
- `_load_llm`: LangChain chat model 객체를 만듭니다.
- `call_llm_json`: prompt를 LLM에 보내고 응답 텍스트를 받습니다.

## OpenAI 모델로 바꿀 때

현재 테스트용 구현은 LangChain chat model을 불러오는 부분만 바꾸면 됩니다.
코드 안에는 다음 예시 주석이 들어 있습니다.

```python
from langchain_openai import ChatOpenAI
return ChatOpenAI(api_key=llm_api_key, model=model_name, temperature=temperature)
```

## 초보자 포인트

이 노드는 JSON을 직접 파싱하지 않습니다.
그 이유는 LLM 응답이 깨지거나 비어 있어도 flow가 멈추지 않게 하기 위해서입니다.
파싱과 보정은 뒤의 normalize 노드가 담당합니다.

## 연결

```text
Build Intent Prompt.prompt_payload
-> LLM JSON Caller (Intent).prompt_payload
-> Normalize Intent Plan.llm_result

Build Pandas Prompt.prompt_payload
-> LLM JSON Caller (Pandas).prompt_payload
-> Normalize Pandas Plan.llm_result

Build Final Answer Prompt.prompt_payload
-> LLM JSON Caller (Answer).prompt_payload
-> Normalize Answer Text.llm_result
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "prompt_payload": {
    "prompt": "Return JSON only: {\"route\":\"single_retrieval\"}"
  },
  "llm_api_key": "sk-...",
  "model_name": "gpt-4o-mini",
  "temperature": "0"
}
```

### 출력 예시

```json
{
  "llm_result": {
    "llm_text": "{\"route\":\"single_retrieval\",\"datasets\":[\"production\"]}",
    "prompt_payload": {
      "prompt": "Return JSON only..."
    },
    "model_name": "gpt-4o-mini",
    "errors": []
  }
}
```

API key가 비어 있으면 테스트용 fallback이 작동할 수 있습니다.

```json
{
  "llm_result": {
    "llm_text": "",
    "errors": ["LLM API key is empty; downstream normalizer will use fallback logic."]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"prompt_payload": {...}})` | `{"prompt_payload": {...}}` | 앞 prompt builder의 Data를 dict로 꺼냅니다. |
| `_load_llm` | `api_key`, `model_name`, `temperature` | LangChain chat model 객체 | 실제 LLM provider 객체를 만드는 부분입니다. 현재는 범용 이름을 쓰고, 내부 구현을 교체하기 쉽게 둡니다. |
| `call_llm_json` | prompt payload, key, model | `llm_result` | prompt 문자열을 LLM에 보내고 응답 text를 받아 표준 payload로 감쌉니다. |
| `build_result` | Langflow 입력값 | `Data(data=llm_result)` | Langflow output method입니다. |

### 코드 흐름

```text
prompt_payload에서 prompt 문자열 추출
-> API key가 있으면 LLM 객체 생성
-> llm.invoke(prompt)
-> response.content를 llm_text에 저장
-> 다음 normalizer가 읽을 llm_result 반환
```

### 초보자 포인트

이 노드는 JSON을 검증하지 않습니다. LLM 응답을 "문자열 그대로" 다음 노드에 넘깁니다. JSON 파싱과 기본값 보정은 뒤의 normalize 노드가 담당합니다.

## 함수 코드 단위 해석: `call_llm_json`

이 함수는 prompt를 LLM에 보내고 응답 text를 `llm_result`로 감싸 반환합니다.

### 함수 input

```json
{
  "prompt_payload_value": {
    "prompt_payload": {
      "prompt": "Return JSON only."
    }
  },
  "llm_api_key": "sk-...",
  "model_name": "gpt-4o-mini",
  "temperature": "0"
}
```

### 함수 output

```json
{
  "llm_result": {
    "llm_text": "{\"route\":\"single_retrieval\"}",
    "prompt_payload": {"prompt": "Return JSON only."},
    "model_name": "gpt-4o-mini",
    "errors": []
  }
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(prompt_payload_value)
prompt_payload = payload.get("prompt_payload") if isinstance(payload.get("prompt_payload"), dict) else payload
prompt = str(prompt_payload.get("prompt") or "")
```

앞 노드에서 온 값을 dict로 바꾸고, 그 안에서 실제 prompt 문자열을 꺼냅니다.

```python
if not str(llm_api_key or "").strip():
    return {
        "llm_result": {
            "llm_text": "",
            "errors": ["LLM API key is empty; downstream normalizer will use fallback logic."],
            ...
        }
    }
```

API key가 없으면 LLM을 호출하지 않습니다. 대신 뒤 normalizer가 fallback logic을 쓰도록 빈 `llm_text`와 오류 메시지를 반환합니다.

```python
llm = _load_llm(str(llm_api_key), str(model_name or ""), float(temperature or 0))
```

LangChain chat model 객체를 만듭니다. 현재 코드에서는 provider 이름을 노출하지 않고 범용 `llm_api_key`, `model_name`을 사용합니다.

```python
response = llm.invoke(prompt)
text = getattr(response, "content", str(response))
```

LLM에 prompt를 보내고, 응답 객체의 `content`를 꺼냅니다. `content`가 없으면 객체를 문자열로 바꿉니다.

```python
return {
    "llm_result": {
        "llm_text": text,
        "prompt_payload": prompt_payload,
        "model_name": model_name,
        "errors": [],
    }
}
```

응답을 파싱하지 않고 text 그대로 담습니다. 이 설계 덕분에 Intent, Pandas, Answer 세 곳에서 같은 LLM Caller를 재사용할 수 있습니다.
