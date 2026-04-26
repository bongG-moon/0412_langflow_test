# 22. Build Final Answer Prompt

## 한 줄 역할

분석 결과를 보고 최종 자연어 답변을 만들기 위한 LLM prompt를 작성하는 노드입니다.

## 왜 필요한가

`analysis_result`에는 row, summary, source_results, error 등이 들어 있습니다.
LLM에게 이 전체를 무작정 보내면 너무 길거나 불명확할 수 있습니다.

이 노드는 필요한 정보만 정리해서 "사용자에게 어떻게 답할지"를 묻는 prompt를 만듭니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `analysis_result` | `Analysis Result Merger` 또는 `MongoDB Data Store` 출력입니다. |
| `preview_row_limit` | LLM prompt에 넣을 row 수입니다. 전체 final data 표시 수와는 다릅니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | `LLM JSON Caller (Answer)`에 넘길 prompt입니다. |

## 주요 함수 설명

- `_analysis_result`: 입력에서 실제 analysis_result를 꺼냅니다.
- `_safe_rows`: prompt에 넣을 row 수를 제한합니다.
- `_row_count_from_result`: 전체 row count를 계산합니다.
- `_source_summaries`: 조회 source별 summary를 만듭니다.
- `build_final_answer_prompt`: 최종 답변용 prompt를 만듭니다.

## 초보자 포인트

이 노드는 최종 답변을 직접 만들지 않습니다.
최종 답변 LLM이 참고할 정리된 자료를 만듭니다.

`preview_row_limit`은 LLM 비용을 줄이기 위한 값입니다.
사용자에게 보여줄 최종 데이터는 `Final Answer Builder`가 따로 처리합니다.

## 연결

```text
Analysis Result Merger.analysis_result
또는 MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result

Build Final Answer Prompt.prompt_payload
-> LLM JSON Caller (Answer).prompt_payload
```

