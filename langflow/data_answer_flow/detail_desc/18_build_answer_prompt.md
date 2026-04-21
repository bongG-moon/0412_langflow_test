# 18. Build Answer Prompt

분석 결과를 한국어 답변으로 요약하도록 built-in LLM에 전달할 prompt를 만드는 노드다.

## 입력

```text
template
analysis_result
```

## 출력

```text
prompt         -> Message
prompt_payload -> Data
```

## 역할

- 사용자 질문, 최근 대화, 결과 요약, 결과 미리보기, 조회 범위, 분석 계획을 prompt로 묶는다.
- 이 노드는 LLM을 직접 호출하지 않는다.
- `prompt` output을 Langflow 기본 LLM 노드에 연결한다.

## 다음 연결

```text
Build Answer Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Final Answer Builder.answer_llm_output
```
