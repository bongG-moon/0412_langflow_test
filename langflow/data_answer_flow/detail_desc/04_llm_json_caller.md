# 04. LLM JSON Caller

Langflow 기본 LLM 노드를 쓰기 어려울 때 사용하는 optional fallback 노드다.

## 입력

```text
prompt
llm_api_key
model_name
temperature
timeout_seconds
```

## 출력

```text
llm_result
```

## 역할

- `langchain_google_genai.ChatGoogleGenerativeAI` 기반으로 LLM을 직접 호출한다.
- `Build Intent Prompt.intent_prompt` 같은 Data payload에서 prompt 문자열을 꺼내 호출한다.
- 호출 결과를 `{"llm_text": "..."}` 형태의 Data payload로 반환한다.

## 현재 기준

Main Flow의 기본 권장 경로는 이 노드가 아니다.

기본 경로:

```text
Build Intent Prompt.prompt
-> built-in LLM
-> Parse Intent JSON.llm_result
```

fallback 경로:

```text
Build Intent Prompt.intent_prompt
-> LLM JSON Caller.prompt
-> Parse Intent JSON.llm_result
```

## 왜 남겨두는가

- Langflow 기본 LLM 노드가 없는 환경에서 테스트할 수 있다.
- 특정 Google GenAI 호출 방식만 빠르게 검증할 수 있다.
- 기존 flow와의 호환성을 유지할 수 있다.
