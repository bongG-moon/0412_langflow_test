# 20. Final Answer Builder

최종 답변과 다음 턴에서 사용할 state를 만드는 노드다.

## 입력

```text
answer_llm_output
analysis_result
store_tables
output_row_limit
db_name
collection_name
```

## 출력

```text
final_result
next_state
answer_message
```

## 역할

- built-in LLM 답변 텍스트를 `response`로 사용한다.
- LLM 답변이 비어 있으면 `analysis_result.summary`를 fallback response로 사용한다.
- `tool_results`, `current_data`, `extracted_params`, `awaiting_analysis_choice`를 포함한 final payload를 만든다.
- chat history에 현재 사용자 질문과 assistant 답변을 추가한다.
- `current_data`와 `source_snapshots`를 state에 저장해 후속 질문에서 재사용할 수 있게 한다.
- Playground 출력이 너무 커지지 않도록 원본 table은 MongoDB에 저장하고 `table_ref_id`만 반환한다.
- 마지막 pandas 분석 결과는 `Output Row Limit`만큼 preview로 남긴다.
- Playground나 Chat Output에는 `answer_message`를 연결해 긴 JSON 대신 짧은 답변과 markdown table preview만 표시할 수 있다.

## MongoDB 저장

기본 저장 위치:

```text
Database Name: datagov
Collection Name: manufacturing_flow_tables
```

저장 document 핵심:

```json
{
  "table_ref_id": "source_result_...",
  "table_kind": "source_result",
  "row_count": 1000,
  "columns": ["WORK_DT", "OPER_NAME", "production"],
  "metadata": {},
  "rows": []
}
```

최종 payload에는 table 전체 대신 다음 정보가 남는다.

```json
{
  "table_ref_id": "analysis_result_...",
  "data_stored_in_mongodb": true,
  "row_count": 1000,
  "columns": ["WORK_DT", "OPER_NAME", "production"],
  "data": [],
  "data_is_preview": true
}
```

`source_result`, `source_snapshot`, `current_dataset`의 `data`는 output에서 비우고 MongoDB ref만 남긴다. `analysis_result`는 마지막 답변에 사용된 데이터이므로 preview row만 남긴다.

## 다음 턴 연결

```text
Final Answer Builder.next_state
-> Previous State JSON Input 또는 Session State Loader.previous_state_payload
```

Langflow canvas에서 다음 질문을 수동 테스트할 때는 `next_state.state_json` 값을 Previous State JSON Input에 넣으면 된다.

## Playground 표시 연결

```text
Final Answer Builder.answer_message
-> Chat Output
```

`final_result`는 전체 JSON payload라 Playground에서 매우 길게 보일 수 있다. 사용자에게 보이는 답변은 `answer_message`를 사용하고, `final_result`는 디버깅이나 외부 시스템 연동용으로만 확인하는 것을 권장한다.

`Display Row Limit` advanced input으로 message에 표시할 preview row 수를 조절할 수 있다. 기본값은 10이다.
