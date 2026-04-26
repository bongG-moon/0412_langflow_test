# 07. LLM JSON Caller

## 이 노드 역할

앞 노드가 만든 prompt를 LLM에 보내고, LLM의 원문 응답 text를 `llm_result`로 반환합니다.

## 왜 필요한가

v2 flow에서는 LLM을 세 군데에서 사용합니다.

1. Intent 판단: 사용자가 새 조회를 원하는지, 후속 분석을 원하는지 판단합니다.
2. Pandas 분석 계획: 조회된 데이터를 어떻게 pandas로 계산할지 계획합니다.
3. 최종 답변 생성: 분석 결과를 자연어 문장으로 바꿉니다.

세 단계 모두 "prompt를 보내고 text를 받는다"는 동작은 같습니다. 그래서 이 공통 동작을 하나의 LLM caller로 분리했습니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | prompt 문자열과 context입니다. |
| `llm_api_key` | LLM API key입니다. 비어 있으면 LLM을 호출하지 않고 fallback용 빈 응답을 반환합니다. |
| `model_name` | 사용할 모델 이름입니다. |
| `temperature` | 응답 무작위성입니다. 계획 생성에는 보통 `0`을 권장합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `llm_result` | LLM 원문 응답, 오류 목록, 원래 prompt_payload를 담습니다. |

## 주요 함수 설명

- `_payload_from_value`: `prompt_payload` 입력을 dict로 꺼냅니다.
- `_load_llm`: LangChain chat model 객체를 생성합니다.
- `call_llm_json`: prompt를 LLM에 보내고 응답 text를 표준 payload로 감쌉니다.
- `build_result`: Langflow output method입니다.

## OpenAI 모델로 바꿀 때

현재 구현이 Google GenAI용이라면, OpenAI 기준으로는 `_load_llm`만 아래처럼 바꾸면 됩니다.

```python
def _load_llm(llm_api_key: str, model_name: str, temperature: float):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(api_key=llm_api_key, model=model_name, temperature=temperature)
```

나머지 `call_llm_json` 구조는 그대로 둘 수 있습니다. provider별 차이는 `_load_llm`에만 모아 두는 것이 안전합니다.

## 초보자 확인용

이 노드는 JSON을 직접 파싱하지 않습니다.

LLM 응답이 깨진 JSON이거나 빈 문자열이어도, 이 노드는 그대로 다음 normalize 노드에 넘깁니다. JSON 파싱과 보정은 다음 단계가 담당합니다.

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
    "prompt": "Return JSON only."
  },
  "llm_api_key": "sk-...",
  "model_name": "gpt-4o-mini",
  "temperature": "0"
}
```

### 출력 예시

정상 호출:

```json
{
  "llm_result": {
    "llm_text": "{\"query_mode\":\"retrieval\",\"needed_datasets\":[\"production\"]}",
    "prompt_payload": {
      "prompt": "Return JSON only."
    },
    "model_name": "gpt-4o-mini",
    "errors": []
  }
}
```

API key가 비어 있는 경우:

```json
{
  "llm_result": {
    "llm_text": "",
    "prompt_payload": {
      "prompt": "Return JSON only."
    },
    "model_name": "",
    "errors": [
      "LLM API key is empty; downstream normalizer will use fallback logic."
    ]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"prompt_payload": {...}})` | `{"prompt_payload": {...}}` | 앞 노드 출력이 Data로 감싸져 있어도 실제 dict를 꺼냅니다. |
| `_load_llm` | `api_key`, `model_name`, `temperature` | LangChain chat model 객체 | 실제 LLM provider 객체를 만드는 부분입니다. provider 변경 시 주로 여기를 바꿉니다. |
| `call_llm_json` | prompt payload, key, model | `llm_result` | prompt를 LLM에 보내고 응답 text를 표준 구조로 감쌉니다. |
| `build_result` | Langflow 입력값 | `Data(data=llm_result)` | Langflow output method입니다. |

### 코드 흐름

```text
prompt_payload에서 prompt 문자열 추출
-> API key가 없으면 빈 llm_text와 오류 반환
-> API key가 있으면 LLM 객체 생성
-> llm.invoke(prompt)
-> response.content를 llm_text로 저장
-> 다음 normalizer가 읽을 llm_result 반환
```

## 함수 코드 단위 해석: `call_llm_json`

이 함수는 prompt를 LLM에 보내고 응답 text를 표준 payload로 반환합니다.

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

입력값에서 실제 prompt payload를 꺼냅니다. 앞 노드가 `{"prompt_payload": {...}}` 형태로 감싸서 보냈다면 한 번 벗깁니다.

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

API key가 없으면 LLM을 호출하지 않습니다. 대신 다음 normalizer가 fallback logic을 사용할 수 있게 빈 `llm_text`와 오류 메시지를 반환합니다.

```python
llm = _load_llm(str(llm_api_key), str(model_name or ""), float(temperature or 0))
response = llm.invoke(prompt)
text = getattr(response, "content", str(response))
```

LLM 객체를 만들고 prompt를 보냅니다. 응답 객체에 `content`가 있으면 그 값을 쓰고, 없으면 응답 객체 전체를 문자열로 바꿉니다.

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

응답을 파싱하지 않고 text 그대로 반환합니다. 이 구조 덕분에 Intent, Pandas, Answer 단계가 같은 caller를 재사용할 수 있습니다.
