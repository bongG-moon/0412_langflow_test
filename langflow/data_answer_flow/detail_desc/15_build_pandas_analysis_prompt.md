# 15. Build Pandas Analysis Prompt

`analysis_context`를 읽어 LLM이 pandas 전처리/분석 코드를 JSON으로 만들 수 있도록 prompt를 구성하는 노드다.

## 입력

```text
template
analysis_context
main_context     optional
domain_payload   legacy optional
```

새 구조에서는 `Analysis Base Builder.analysis_context` 안에 `main_context`가 들어 있으므로 `domain_payload`는 직접 연결하지 않아도 된다.

## 출력

```text
prompt         -> Message
prompt_payload -> Data
```

## 역할

- 분석 대상 dataframe profile을 만든다.
- sample rows를 prompt에 넣는다.
- intent, retrieval plan, metric 정의, dataset 정의, merge notes를 LLM에게 전달한다.
- LLM이 `{"code": "result = ..."}` 형태의 JSON만 반환하도록 지시한다.

## 권장 연결

```text
Analysis Base Builder.analysis_context
-> Build Pandas Analysis Prompt.analysis_context

Build Pandas Analysis Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Parse Pandas Analysis JSON.llm_output
```
