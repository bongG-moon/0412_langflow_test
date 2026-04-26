# 25. Final Answer Builder

## 이 노드 역할

사용자에게 보여줄 최종 메시지, 외부에서 활용할 `final_result`, 다음 턴에 이어갈 `next_state`를 만드는 노드입니다.

이 노드는 Langflow v2 flow의 마지막 핵심 조립 단계입니다.

## 왜 필요한가

최종 답변은 단순 텍스트만 있으면 부족합니다. 다음 질문에서 조건을 이어받으려면 현재 데이터, 마지막 intent, required params, filters, column filters, filter plan이 state에 저장되어야 합니다.

이 노드는 사용자 답변과 후속 질문용 상태를 동시에 만듭니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `analysis_result` | `Analysis Result Merger` 또는 `MongoDB Data Store` 이후의 최종 분석 결과입니다. |
| `answer_text` | `Normalize Answer Text`에서 정리한 답변 문장입니다. |
| `output_row_limit` | state와 final result에 싣는 row 최대 개수입니다. |
| `display_row_limit` | 과거 호환용 입력입니다. 현재 최종 데이터는 전체 표시 기준으로 구성됩니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `answer_message` | Langflow Chat Output에 연결할 사용자 표시 메시지입니다. |
| `final_result` | API나 downstream에서 사용할 최종 payload입니다. |
| `next_state` | 다음 턴의 State Memory에 저장할 상태입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_build_final_data` | 최종 row, row count, data ref 정보를 정리합니다. |
| `_build_answer_message` | 답변 텍스트와 최종 데이터 표를 합칩니다. |
| `_fallback_response` | answer_text가 없을 때 기본 답변을 만듭니다. |
| `build_final_answer` | final_result, next_state, answer_message를 모두 생성합니다. |

## 초보자 확인용

후속 질문이 제대로 동작하려면 이 노드가 중요합니다.

예를 들어 1차 질문에서 `date=20260426`, `process_name=DA`, `mode=DDR5`로 조회했다면 이 값들이 `next_state.context.last_required_params`, `last_filters`, `last_filter_plan`에 저장됩니다. 다음 질문에서 "그중 상위 5개만" 같은 follow-up을 하면 이 상태를 기반으로 이어서 분석할 수 있습니다.

## 연결

```text
Analysis Result Merger 또는 MongoDB Data Store
-> Final Answer Builder.analysis_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text

Final Answer Builder.answer_message
-> Chat Output

Final Answer Builder.next_state
-> State Memory Message Builder.next_state
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "analysis_result": {
    "success": true,
    "data": [
      {"MODE": "DDR5", "production": 100}
    ],
    "summary": "data analysis complete: 1 rows",
    "intent_plan": {
      "required_params": {"date": "20260426"},
      "filters": {"process_name": ["D/A1"]},
      "filter_plan": [
        {"field": "process_name", "columns": ["OPER_NAME"], "values": ["D/A1"]}
      ]
    },
    "state": {
      "session_id": "demo-session",
      "pending_user_question": "오늘 DA공정 DDR5 생산 보여줘"
    }
  },
  "answer_text": "오늘 DA공정 DDR5 생산량은 100입니다."
}
```

### 출력 예시

```json
{
  "answer_message": "오늘 DA공정 DDR5 생산량은 100입니다.\n\n### 최종 데이터\n\n총 1건\n\n| MODE | production |\n| --- | --- |\n| DDR5 | 100 |",
  "final_result": {
    "response": "오늘 DA공정 DDR5 생산량은 100입니다.",
    "awaiting_analysis_choice": true,
    "state_json": "{...}"
  },
  "next_state": {
    "session_id": "demo-session",
    "context": {
      "last_required_params": {"date": "20260426"},
      "last_filters": {"process_name": ["D/A1"]},
      "last_filter_plan": [
        {"field": "process_name", "columns": ["OPER_NAME"], "values": ["D/A1"]}
      ]
    }
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_build_final_data` | result, rows | final_data | 표시 데이터와 data_ref 정보를 정리합니다. |
| `_build_answer_message` | response, final_data | markdown message | 답변과 표를 합칩니다. |
| `build_final_answer` | analysis_result, answer_text | final payload | 최종 메시지와 다음 상태를 생성합니다. |

### 코드 흐름

```text
analysis_result와 answer_text 입력
-> row 수와 data_ref 확인
-> final_data 생성
-> answer_message 생성
-> current_data 갱신
-> context에 last_* 조건 저장
-> final_result, next_state 출력
```

## 함수 코드 단위 해석: `build_final_answer`

### 함수 input

```json
{
  "analysis_result": {
    "success": true,
    "data": [{"MODE": "DDR5", "production": 100}],
    "intent_plan": {
      "required_params": {"date": "20260426"},
      "filters": {"mode": ["DDR5"]}
    }
  },
  "answer_text": "DDR5 생산량은 100입니다."
}
```

### 함수 output

```json
{
  "answer_message": "DDR5 생산량은 100입니다.\n\n### 최종 데이터...",
  "final_result": {
    "response": "DDR5 생산량은 100입니다.",
    "current_data": {
      "source_required_params": {"date": "20260426"},
      "source_filters": {"mode": ["DDR5"]}
    }
  },
  "next_state": {
    "context": {
      "last_required_params": {"date": "20260426"},
      "last_filters": {"mode": ["DDR5"]}
    }
  }
}
```

### 핵심 코드 해석

```python
result = _analysis_result(analysis_result_value)
state = result.get("state") if isinstance(result.get("state"), dict) else {}
plan = result.get("intent_plan") if isinstance(result.get("intent_plan"), dict) else {}
```

분석 결과, 기존 state, 이번 intent plan을 꺼냅니다.

```python
response = _text_from_value(answer_text_value) or _fallback_response(result, display_row_limit)
```

LLM 답변이 있으면 사용하고, 없으면 deterministic fallback 답변을 만듭니다.

```python
current_data = {
    "data": slim_rows,
    "retrieval_applied_params": result.get("retrieval_applied_params", {}),
    "source_filters": result.get("retrieval_applied_filters", plan.get("filters", {})),
    "filter_plan": result.get("filter_plan", plan.get("filter_plan", [])),
}
```

다음 턴에서 이어서 분석할 수 있도록 현재 데이터와 적용 조건을 저장합니다.

```python
context.update({
    "last_intent": plan,
    "last_required_params": plan.get("required_params", extracted_params),
    "last_filters": plan.get("filters", {}),
    "last_column_filters": plan.get("column_filters", {}),
    "last_filter_plan": plan.get("filter_plan", []),
})
```

후속 질문 판별과 필터 상속에 필요한 값을 `context`에 저장합니다.

```python
final_result = {
    "response": response,
    "answer_message": answer_message,
    "final_data": _json_safe(final_data),
    "state_json": json.dumps(_json_safe(next_state), ensure_ascii=False),
}
```

화면 출력, API 응답, state 저장에 필요한 값을 하나의 final payload로 묶습니다.

## 추가 함수 코드 단위 해석: `_build_final_data`

최종 결과에 표시할 데이터와 data_ref 정보를 정리하는 함수입니다.

```python
display_rows = _safe_rows(rows, 0)
is_preview = bool(data_ref) or row_count > len(display_rows)
```

현재 구현에서는 display rows를 모두 담되, data_ref가 있거나 전체 row 수가 표시 row 수보다 많으면 preview로 표시합니다.

```python
final_data = {
    "rows": display_rows,
    "row_count": row_count,
    "display_row_limit": "all",
    "displayed_row_count": len(display_rows),
    "columns": _rows_columns(display_rows),
```

화면이나 API에서 바로 읽을 수 있도록 rows, 전체 건수, 표시 건수, 컬럼 목록을 넣습니다.

```python
if data_ref:
    final_data["data_ref"] = deepcopy(data_ref)
    final_data["data_is_reference"] = True
```

큰 데이터가 MongoDB로 빠져 있으면 참조 정보도 함께 유지합니다.

## 추가 함수 코드 단위 해석: `_build_answer_message`

```python
rows = final_data.get("rows") if isinstance(final_data.get("rows"), list) else []
if not rows:
    return response
```

표시할 row가 없으면 자연어 답변만 반환합니다.

```python
count_text = f"총 {row_count}건" if row_count == displayed else f"전체 {row_count}건 중 {displayed}건 표시"
```

전체 row 수와 화면에 표시되는 row 수가 다를 때 사용자에게 명확히 알려줍니다.

```python
parts = [
    response,
    "",
    "### 최종 데이터",
    "",
    count_text,
    "",
    table,
]
```

자연어 답변과 markdown table을 하나의 Chat Output 메시지로 합칩니다.

## 추가 함수 코드 단위 해석: `build_final_answer`의 state context 갱신

```python
chat_history = [*chat_history, {"role": "user", "content": user_question}, {"role": "assistant", "content": response}]
next_state["chat_history"] = chat_history[-20:]
```

이번 턴의 사용자 질문과 assistant 답변을 chat history에 추가하고 최근 20개만 유지합니다.

```python
context.update({
    "last_intent": plan,
    "last_retrieval_plan": {"route": plan.get("route"), "jobs": plan.get("retrieval_jobs", [])},
    "last_required_params": plan.get("required_params", extracted_params),
    "last_filters": plan.get("filters", {}),
    "last_column_filters": plan.get("column_filters", {}),
    "last_filter_plan": plan.get("filter_plan", []),
})
```

후속 질문에서 조건을 상속하거나 신규 조회로 전환할지 판단하는 핵심 값들을 context에 저장합니다.

```python
next_state["current_data"] = current_data
```

성공한 분석 결과를 다음 턴의 현재 데이터로 저장합니다. "그중", "이 결과" 같은 질문은 이 값을 기반으로 처리됩니다.
