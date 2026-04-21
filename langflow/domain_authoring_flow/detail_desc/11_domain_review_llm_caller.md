# 11. Domain Review LLM Caller

## 역할

semantic review prompt를 LLM API로 보내고 JSON 문자열 응답을 받는다.

이 노드는 LLM 호출만 담당한다. JSON 구조 보정은 다음 `Parse Domain Review JSON` 노드가 담당한다.

## 입력

- `prompt`: Build Domain Review Prompt output
- `llm_api_key`: 이 review 노드에서 사용할 API key
- `model_name`: 이 review 노드에서 사용할 model
- `temperature`: 기본값 `0`
- `timeout_seconds`: 기본값 `60`

## 출력

`llm_result`

```json
{
  "llm_text": "{...semantic review json...}",
  "llm_debug": {
    "provider": "langchain_google_genai",
    "model_name": "gemini-flash-latest",
    "prompt_chars": 1234,
    "ok": true,
    "error": null
  }
}
```

## 다음 연결

```text
Domain Review LLM Caller.llm_result -> Parse Domain Review JSON.llm_result
```
