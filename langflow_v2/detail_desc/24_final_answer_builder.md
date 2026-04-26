# 24. Final Answer Builder

## 한 줄 역할

사용자에게 보여줄 최종 메시지, API용 final_result, 다음 턴용 next_state를 만드는 노드입니다.

## 왜 가장 중요한가

이 노드는 flow의 최종 출구입니다.

여기서 세 가지가 만들어집니다.

1. `answer_message`: Playground Chat Output에 보낼 메시지
2. `final_result`: API나 저장용 전체 결과
3. `next_state`: 후속 질문을 위해 저장할 상태

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `analysis_result` | 분석 결과입니다. |
| `answer_text` | Normalize Answer Text의 자연어 답변입니다. 비어 있으면 fallback 답변을 만듭니다. |
| `output_row_limit` | final_result에 담을 최대 row 수입니다. |
| `display_row_limit` | 과거 호환용입니다. 현재는 기본적으로 전체 final data를 표시합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `answer_message` | 사용자에게 보여줄 답변 메시지입니다. |
| `final_result` | response, final_data, current_data 등을 포함한 전체 payload입니다. |
| `next_state` | 다음 질문에서 사용할 상태입니다. |

## 주요 함수 설명

- `_build_final_data`: 최종 데이터 테이블 정보를 만듭니다.
- `_build_answer_message`: 자연어 답변과 final data table을 하나의 markdown 메시지로 만듭니다.
- `_fallback_response`: LLM 답변이 없을 때 규칙 기반 답변을 만듭니다.
- `build_final_answer`: 세 출력값을 모두 생성합니다.

## final_result 핵심 구조

```json
{
  "response": "최종 답변",
  "final_data": {
    "rows": [],
    "row_count": 12,
    "columns": []
  },
  "current_data": {},
  "state_json": "{...}"
}
```

## 초보자 포인트

후속 질문이 잘 되려면 `next_state`가 중요합니다.
`next_state` 안에 `current_data`, `context`, `chat_history`가 들어가야 다음 턴에서 `이때`, `그 결과` 같은 표현을 이해할 수 있습니다.

## 연결

```text
Analysis Result Merger.analysis_result
또는 MongoDB Data Store.stored_payload
-> Final Answer Builder.analysis_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text

Final Answer Builder.answer_message
-> Chat Output.input

Final Answer Builder.next_state
-> State Memory Message Builder.next_state
```

