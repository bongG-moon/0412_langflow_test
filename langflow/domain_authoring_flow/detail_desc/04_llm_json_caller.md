# 04. Domain Authoring LLM JSON Caller

## 역할

도메인 구조화 prompt를 LLM에 보내고 JSON 문자열 응답을 받는다.

현재 구현은 LangGraph 쪽과 맞춰 `langchain_google_genai.ChatGoogleGenerativeAI`를 사용한다. 함수명과 변수명은 범용적인 LLM 호출 의미를 유지한다.

## 입력

- `prompt`: Build Domain Structuring Prompt output
- `llm_api_key`: 이 노드에서 사용할 API key
- `model_name`: 모델명
- `temperature`: 기본값 `0`
- `timeout_seconds`: 기본값 `60`

## 출력

`llm_result`

```json
{
  "llm_text": "{ \"domain_patch\": ... }",
  "llm_debug": {
    "provider": "langchain_google_genai",
    "model_name": "gemini-flash-latest",
    "prompt_chars": 1000,
    "ok": true,
    "error": null
  }
}
```

## 주요 구현

- `_read_prompt()`는 `prompt`, `domain_structuring_prompt`, `text` 순서로 prompt 문자열을 찾는다.
- API key가 없거나 패키지가 없으면 예외 대신 `llm_debug.error`에 이유를 담아 반환한다.
- `.text`는 사용하지 않고 LLM 응답도 `.data["llm_text"]`에 담는다.

## 다음 연결

```text
Domain Authoring LLM JSON Caller.llm_result -> Parse Domain Patch JSON.llm_result
```
