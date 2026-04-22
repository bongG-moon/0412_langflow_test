# 19. Build Answer Prompt

pandas 분석 결과를 사용자에게 설명하는 최종 답변 prompt를 만드는 노드다.

## 입력

```text
template
analysis_result
```

## 출력

```text
prompt
prompt_payload
```

권장 연결은 `prompt_payload`다.

```text
Build Answer Prompt.prompt_payload
-> LLM API Caller.prompt
```

## prompt_payload 구조

```json
{
  "prompt": "...",
  "prompt_type": "answer_text"
}
```

`LLM API Caller.response_mode=auto`에서는 자연어 text 응답 모드로 처리된다.

## prompt에 들어가는 정보

- 사용자 질문
- 최근 chat history
- 분석 성공 여부
- 분석 summary
- 결과 row count
- 결과 preview rows
- 조회/분석 범위
- pandas analysis plan

원본 table 전체를 prompt에 넣지 않는다. preview만 사용한다.

## 연결

```text
Execute Pandas Analysis.analysis_result
-> Build Answer Prompt.analysis_result

Build Answer Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Final Answer Builder.answer_llm_output
```
