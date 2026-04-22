# 06. Domain Item LLM API Caller

`Domain Item Prompt Template`에서 만든 prompt를 LLM API로 보내고, JSON 문자열 응답을 `Parse Domain Item JSON`이 읽을 수 있는 payload로 반환한다.

## 입력

```text
prompt
llm_api_key
model_name
temperature
timeout_seconds
system_instruction
```

`prompt`에는 보통 아래 output을 연결한다.

```text
Domain Item Prompt Template.prompt_payload
```

`llm_api_key`, `model_name`은 이 노드에서 직접 입력한다. 필요한 모델이 빠른 모델이면 `model_name`에 빠른 모델명을 넣고, 더 정확한 추출이 필요하면 더 강한 모델명을 넣으면 된다.

## 출력

```text
llm_result
```

반환 payload:

```json
{
  "llm_text": "{...LLM JSON text...}",
  "llm_debug": {
    "provider": "langchain_google_genai",
    "model_name": "...",
    "response_mode": "json",
    "prompt_chars": 0,
    "ok": true,
    "error": null
  }
}
```

## 역할

Langflow 기본 LLM node를 쓰지 않고, domain item authoring flow 안에서 커스텀 LLM 호출을 수행하기 위한 노드다.

내부 구현은 `langchain_google_genai.ChatGoogleGenerativeAI`를 사용한다. 함수명과 노드명은 특정 공급자를 강조하지 않고 LLM API 호출 역할을 드러내도록 작성했다.

## 다음 연결

```text
Domain Item LLM API Caller.llm_result
-> Parse Domain Item JSON.llm_output
```

이 노드는 JSON-only system instruction을 기본값으로 사용한다. LLM이 markdown fence를 붙이더라도 다음 parser가 한 번 더 정리해서 JSON만 추출한다.
