# 07. LLM API Caller

Langflow built-in LLM 대신 사용하는 공통 LLM 호출 노드다.

파일명은 기존 호환을 위해 `04_llm_json_caller.py`이지만, 실제 노드명은 `LLM API Caller`다.

## 입력

```text
prompt
llm_api_key
model_name
temperature
timeout_seconds
response_mode
system_instruction
```

## 출력

```text
llm_result
```

## 역할

- `prompt` payload에서 `prompt` 문자열을 읽는다.
- `llm_api_key`, `model_name`, `temperature`를 노드별로 입력받는다.
- 현재 구현은 `langchain_google_genai.ChatGoogleGenerativeAI`를 사용한다.
- 함수명과 변수명은 범용 LLM API 호출 의미로 유지했다.
- 결과는 아래 형태로 반환한다.

```json
{
  "llm_text": "...",
  "llm_debug": {
    "provider": "langchain_google_genai",
    "model_name": "...",
    "response_mode": "json",
    "prompt_chars": 1234,
    "ok": true,
    "error": null
  }
}
```

## Response Mode

`response_mode`는 `auto`, `json`, `text` 중 하나를 쓴다.

일반적으로 `auto`로 두면 된다.

- `Build Intent Prompt`는 `prompt_type="intent"`를 보낸다.
- `Build Pandas Analysis Prompt`는 `prompt_type="pandas_analysis"`를 보낸다.
- `Build Answer Prompt`는 `prompt_type="answer_text"`를 보낸다.

`auto` 모드에서는 intent/pandas prompt는 JSON 응답을 요구하고, answer prompt는 자연어 text 응답을 요구한다.

## 연결 예시

Intent LLM:

```text
Build Intent Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Parse Intent JSON.llm_result
```

Pandas 분석 LLM:

```text
Build Pandas Analysis Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Parse Pandas Analysis JSON.llm_output
```

최종 답변 LLM:

```text
Build Answer Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Final Answer Builder.answer_llm_output
```

## 구현 메모

실제 lfx Langflow 환경에서는 상단 fallback import 블록이 필수는 아니다. 현재는 로컬 테스트와 Langflow 버전 차이를 흡수하기 위해 남겨두었다.
