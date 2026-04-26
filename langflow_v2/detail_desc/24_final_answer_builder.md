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

## Python 코드 상세 해석

### 입력 예시

```json
{
  "analysis_result": {
    "success": true,
    "final_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "state": {
      "session_id": "abc",
      "chat_history": []
    }
  },
  "answer_text": {
    "response": "MODE A가 150으로 가장 많습니다."
  },
  "display_row_limit": "0",
  "output_row_limit": "200"
}
```

### 출력 예시

`answer_message`:

```text
MODE A가 150으로 가장 많습니다.

## 최종 데이터
2건 중 2건 표시

| MODE | production |
| --- | --- |
| A | 150 |
| B | 30 |
```

`final_result`:

```json
{
  "response": "MODE A가 150으로 가장 많습니다.",
  "success": true,
  "final_data": {
    "rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  },
  "current_data": {
    "rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ]
  }
}
```

`next_state`:

```json
{
  "state": {
    "session_id": "abc",
    "current_data": {
      "rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    },
    "context": {}
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_make_message` | 답변 문자열 | Langflow Message | Chat Output에 자연어 메시지로 표시하기 위해 씁니다. |
| `_safe_rows` | rows, limit | 제한된 rows | API output이나 memory가 너무 커지지 않게 row 수를 제한합니다. |
| `_preview_table` | rows | markdown table | 사용자 화면에 최종 데이터를 표 형태로 보여줍니다. |
| `_build_final_data` | result, rows, row_count, ref | final_data dict | 답변에 사용한 최종 가공 데이터를 표준 구조로 만듭니다. |
| `_build_answer_message` | response, final_data | 화면 출력 문자열 | 답변 문장과 최종 데이터 표를 합쳐 Chat Output 메시지를 만듭니다. |
| `_fallback_response` | result | 답변 문장 | LLM 답변이 없을 때 final data로 최소 답변을 만듭니다. |
| `build_final_answer` | analysis result, answer text | final payload | `answer_message`, `final_result`, `next_state`를 한 번에 만듭니다. |
| `_payload` | 없음 | cached final payload | output이 3개라 같은 계산을 반복하지 않도록 내부 cache처럼 씁니다. |
| `build_answer_message` | 없음 | Message | 사용자에게 보이는 출력입니다. |
| `build_final_result` | 없음 | Data | API/저장용 전체 결과입니다. |
| `build_next_state` | 없음 | Data | 다음 턴 memory에 저장할 state입니다. |

### 코드 흐름

```text
analysis_result와 answer_text 입력
-> response 결정
-> final_rows로 final_data 생성
-> 답변 + 최종 데이터 markdown 생성
-> final_result와 next_state 구성
-> 세 output port로 각각 반환
```

### 초보자 포인트

이 노드는 사용자에게 보이는 최종 모양을 결정합니다. "답변 문장만"이 아니라 "답변에 사용된 최종 데이터"도 함께 보여달라는 요구가 여기서 반영됩니다.

## 함수 코드 단위 해석: `build_final_answer`

이 함수는 최종 답변 문장, 최종 데이터, 다음 턴 state를 한 번에 만드는 핵심 함수입니다.

### 함수 input

```json
{
  "analysis_result_value": {
    "analysis_result": {
      "success": true,
      "tool_name": "analyze_current_data",
      "data": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ],
      "summary": "data analysis complete: 2 rows",
      "state": {
        "session_id": "abc",
        "chat_history": []
      },
      "intent_plan": {
        "route": "followup_transform"
      }
    }
  },
  "answer_text_value": {
    "answer_text": {
      "response": "MODE A가 150으로 가장 많습니다."
    }
  },
  "output_row_limit_value": "200",
  "display_row_limit_value": "0"
}
```

### 함수 output

```json
{
  "answer_message": "MODE A가 150으로 가장 많습니다.\n\n### 최종 데이터\n...",
  "final_result": {
    "response": "MODE A가 150으로 가장 많습니다.",
    "final_data": {
      "rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ],
      "row_count": 2
    }
  },
  "next_state": {
    "state": {
      "session_id": "abc",
      "current_data": {
        "data": [
          {"MODE": "A", "production": 150},
          {"MODE": "B", "production": 30}
        ]
      }
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

앞 노드에서 온 analysis result를 꺼내고, 그 안의 state와 intent plan도 따로 꺼냅니다.

```python
response = _text_from_value(answer_text_value) or _fallback_response(result, display_row_limit)
```

최종 답변 LLM이 만든 문장을 먼저 사용합니다. 만약 비어 있으면 분석 결과를 보고 fallback 답변을 만듭니다.

```python
rows = result.get("data") if isinstance(result.get("data"), list) else []
actual_row_count = _row_count_from_result(result, rows)
slim_rows = _safe_rows(rows, output_row_limit)
```

- `rows`: 최종 분석 데이터입니다.
- `actual_row_count`: 전체 결과 건수입니다.
- `slim_rows`: API payload나 memory에 넣을 때 너무 커지지 않게 제한한 row 목록입니다.

```python
data_ref = deepcopy(result.get("data_ref")) if isinstance(result.get("data_ref"), dict) else None
final_data = _build_final_data(result, rows, actual_row_count, display_row_limit, data_ref)
answer_message = _build_answer_message(response, final_data)
```

최종 데이터 구조를 만들고, 사용자에게 보여줄 message를 만듭니다. `data_ref`가 있으면 원본 데이터는 MongoDB에 있고 화면에는 preview만 있을 수 있음을 표시합니다.

```python
current_data = state.get("current_data")
if result.get("success"):
    current_data = {
        "success": True,
        "tool_name": result.get("tool_name", "analyze_current_data"),
        "data": slim_rows,
        "row_count": actual_row_count,
        ...
    }
```

다음 턴 후속 질문을 위해 `current_data`를 새 결과로 갱신합니다. 사용자가 "이때 가장 큰 값은?"이라고 물으면 다음 턴에서 이 데이터가 기준이 됩니다.

```python
next_state = deepcopy(state)
next_state.pop("pending_user_question", None)
```

기존 state를 복사해 다음 턴 state를 만듭니다. `pending_user_question`은 이번 턴에서만 필요한 값이므로 제거합니다.

```python
if user_question:
    chat_history = [*chat_history, {"role": "user", "content": user_question}, {"role": "assistant", "content": response}]
next_state["chat_history"] = chat_history[-20:]
```

현재 질문과 답변을 chat history에 추가합니다. 너무 길어지지 않게 최근 20개만 유지합니다.

```python
context.update({
    "last_intent": plan,
    "last_retrieval_plan": {"route": plan.get("route"), "jobs": plan.get("retrieval_jobs", [])},
    "last_extracted_params": extracted_params,
    "last_analysis_summary": result.get("summary", "")
})
```

다음 턴에서 참고할 맥락을 저장합니다.

- 마지막 의도
- 마지막 조회 계획
- 마지막 필터/날짜 파라미터
- 마지막 분석 요약

```python
tool_result = {
    "success": result.get("success", False),
    "tool_name": result.get("tool_name", "analyze_current_data"),
    "data": slim_rows,
    "row_count": actual_row_count,
    ...
}
```

API나 디버깅 화면에서 보기 좋은 tool result를 만듭니다. 여기에도 최종 데이터 일부와 row count가 들어갑니다.

### 왜 이 함수가 중요한가?

이 함수는 v2 flow의 마지막 계약을 만듭니다.

- 사용자가 보는 메시지: `answer_message`
- 외부 시스템이 읽을 결과: `final_result`
- 다음 질문을 위한 기억: `next_state`

이 세 가지가 여기서 동시에 만들어지기 때문에, 최종 출력 형식을 바꾸려면 이 함수를 가장 먼저 확인하면 됩니다.

## 추가 함수 코드 단위 해석: `_build_final_data`

이 함수는 사용자에게 보여줄 최종 데이터 묶음을 만듭니다.

### 함수 input

```json
{
  "rows": [
    {"MODE": "A", "production": 150},
    {"MODE": "B", "production": 30}
  ],
  "row_count": 2,
  "data_ref": null
}
```

### 함수 output

```json
{
  "rows": [
    {"MODE": "A", "production": 150},
    {"MODE": "B", "production": 30}
  ],
  "row_count": 2,
  "display_row_limit": "all",
  "displayed_row_count": 2,
  "columns": ["MODE", "production"],
  "data_is_preview": false
}
```

### 핵심 코드 해석

```python
display_rows = _safe_rows(rows, 0)
```

사용자 화면에 보여줄 rows를 준비합니다. 현재 문서 기준으로 `0`은 전체 표시를 의미합니다.

```python
is_preview = bool(data_ref) or row_count > len(display_rows)
```

원본 데이터가 MongoDB reference로 저장되어 있거나, 전체 row_count가 화면에 표시된 row 수보다 많으면 preview라고 표시합니다.

```python
final_data = {
    "rows": display_rows,
    "row_count": row_count,
    "display_row_limit": "all",
    "displayed_row_count": len(display_rows),
    "columns": _rows_columns(display_rows),
    ...
}
```

최종 데이터의 row, 전체 건수, 표시 건수, 컬럼 목록을 한곳에 모읍니다.

```python
if data_ref:
    final_data["data_ref"] = deepcopy(data_ref)
    final_data["data_is_reference"] = True
```

원본 전체 데이터가 MongoDB에 저장되어 있으면 그 주소도 같이 담습니다.

## 추가 함수 코드 단위 해석: `_build_answer_message`

이 함수는 자연어 답변과 최종 데이터 표를 합쳐 Chat Output에 보여줄 문자열을 만듭니다.

### 함수 input

```json
{
  "response": "MODE A가 150으로 가장 많습니다.",
  "final_data": {
    "rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  }
}
```

### 함수 output

```text
MODE A가 150으로 가장 많습니다.

### 최종 데이터

총 2건

| MODE | production |
| --- | --- |
| A | 150 |
| B | 30 |
```

### 핵심 코드 해석

```python
rows = final_data.get("rows") if isinstance(final_data.get("rows"), list) else []
if not rows:
    return response
```

최종 데이터 row가 없으면 답변 문장만 반환합니다.

```python
row_count = final_data.get("row_count") or len(rows)
displayed = len(rows)
table = _preview_table(rows, 0)
```

전체 건수, 표시 건수, markdown table을 준비합니다.

```python
count_text = f"총 {row_count}건" if row_count == displayed else f"전체 {row_count}건 중 {displayed}건 표시"
```

전체가 다 표시되면 `총 n건`, 일부만 표시되면 `전체 n건 중 m건 표시`라고 문구를 다르게 만듭니다.

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
return "\n".join(str(part) for part in parts).strip()
```

답변 문장, 제목, 건수, 표를 줄바꿈으로 합쳐 최종 메시지를 만듭니다.
