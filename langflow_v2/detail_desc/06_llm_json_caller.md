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

