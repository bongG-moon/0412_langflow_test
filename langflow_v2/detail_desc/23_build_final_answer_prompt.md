# 23. Build Final Answer Prompt

## 이 노드 역할

분석 결과를 사용자가 읽기 좋은 최종 답변으로 바꾸기 위한 LLM prompt를 만드는 노드입니다.

`analysis_result`의 요약, row preview, source 요약, 성공 여부를 정리해서 마지막 답변 생성 LLM에 전달합니다.

## 왜 필요한가

pandas 분석 결과는 row 목록과 metadata 중심입니다. 사용자는 보통 "무슨 의미인지", "몇 건인지", "핵심 값이 무엇인지"를 자연어로 알고 싶어 합니다.

이 노드는 최종 답변 LLM이 과장하지 않고 실제 결과에 근거해 답변하도록 필요한 정보만 정리합니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `analysis_result` | `MongoDB Data Store`를 거친 분석 결과입니다. |
| `preview_row_limit` | final answer prompt에 포함할 row preview 개수입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `prompt_payload` | 최종 답변 LLM에 전달할 prompt와 분석 결과 context입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_analysis_result` | 입력 wrapper에서 실제 analysis result를 꺼냅니다. |
| `_safe_rows` | prompt에 넣을 row preview를 제한합니다. |
| `_row_count_from_result` | 전체 row 수를 계산합니다. |
| `_source_summaries` | analysis result 안의 source별 요약 정보를 추출합니다. |
| `build_final_answer_prompt` | 최종 답변 생성을 위한 prompt payload를 만듭니다. |

## 초보자 확인용

이 노드는 최종 답변을 직접 만들지는 않습니다. 다음 LLM 호출이 답변 문장을 만들 수 있도록 재료를 정리합니다.

전체 데이터가 MongoDB로 저장되어 있어도 prompt에는 preview만 들어가고, 전체 row 수와 data reference 정보는 metadata로 유지됩니다.

## 연결

```text
MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result

Build Final Answer Prompt.prompt_payload
-> LLM JSON Caller.prompt_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "analysis_result": {
    "success": true,
    "summary": "data analysis complete: 2 rows",
    "data": [
      {"MODE": "DDR5", "production": 100},
      {"MODE": "LPDDR5", "production": 80}
    ],
    "intent_plan": {
      "analysis_goal": "모드별 생산량 확인"
    }
  }
}
```

### 출력 예시

```json
{
  "prompt_payload": {
    "prompt": "You are writing the final Korean answer...",
    "analysis_result": {
      "success": true,
      "summary": "data analysis complete: 2 rows"
    },
    "preview_rows": [
      {"MODE": "DDR5", "production": 100}
    ],
    "row_count": 2
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_safe_rows` | rows, limit | preview rows | prompt에 넣을 row 수를 제한합니다. |
| `_row_count_from_result` | analysis result | 숫자 | 실제 전체 row 수를 추정합니다. |
| `_source_summaries` | analysis result | 요약 list | 어느 dataset에서 온 결과인지 정리합니다. |
| `build_final_answer_prompt` | analysis_result | prompt_payload | 답변 LLM 호출용 prompt를 만듭니다. |

### 코드 흐름

```text
analysis_result 입력
-> success/error, summary 확인
-> data preview와 row_count 계산
-> source summary 생성
-> 최종 답변용 prompt 작성
```

## 함수 코드 단위 해석: `build_final_answer_prompt`

### 함수 input

```json
{
  "analysis_result": {
    "success": true,
    "data": [{"MODE": "DDR5", "production": 100}],
    "summary": "data analysis complete: 1 rows"
  }
}
```

### 함수 output

```json
{
  "prompt_payload": {
    "prompt": "최종 답변 작성 지시문",
    "preview_rows": [{"MODE": "DDR5", "production": 100}],
    "row_count": 1
  }
}
```

### 핵심 코드 해석

```python
result = _analysis_result(analysis_result_value)
```

입력값에서 실제 analysis result를 꺼냅니다.

```python
rows = result.get("data") if isinstance(result.get("data"), list) else []
preview_rows = _safe_rows(rows, preview_limit)
```

답변 prompt에 넣을 row preview를 만듭니다.

```python
row_count = _row_count_from_result(result, rows)
```

`row_count`, `data_ref.row_count`, 실제 rows 길이 중 가능한 값을 사용해 전체 row 수를 계산합니다.

```python
source_summaries = _source_summaries(result)
```

여러 데이터셋에서 온 결과라면 source별 summary도 prompt에 포함할 수 있게 정리합니다.

```python
return {"prompt_payload": {...}}
```

LLM JSON Caller가 그대로 사용할 수 있는 prompt payload를 반환합니다.

## 추가 함수 코드 단위 해석: `_row_count_from_result`

최종 답변 prompt에서 전체 row 수를 정확히 쓰기 위한 함수입니다.

```python
for key in ("row_count", "total_row_count"):
    try:
        if result.get(key) is not None:
            return int(result[key])
```

analysis result에 명시 row count가 있으면 그 값을 우선 사용합니다.

```python
data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
if data_ref.get("row_count") is not None:
    return int(data_ref["row_count"])
```

MongoDB data_ref로 큰 데이터가 빠져 있는 경우 ref metadata의 row count를 사용합니다.

```python
return len(rows)
```

명시 값이 없으면 현재 payload에 남아 있는 rows 길이를 사용합니다.

## 추가 함수 코드 단위 해석: `_source_summaries`

여러 source result를 최종 답변 prompt에 넣기 좋은 요약 형태로 바꿉니다.

```python
for item in result.get("source_results", []):
    if not isinstance(item, dict):
        continue
```

source_results 안에서 dict 항목만 처리합니다.

```python
rows = item.get("data") if isinstance(item.get("data"), list) else []
data_ref = item.get("data_ref") if isinstance(item.get("data_ref"), dict) else {}
```

source data가 직접 들어 있는 경우와 MongoDB ref로 빠져 있는 경우를 모두 고려합니다.

```python
"summary": item.get("summary") or item.get("error_message", ""),
"row_count": item.get("row_count") or data_ref.get("row_count") or len(rows),
"has_data_ref": bool(data_ref),
```

답변 LLM이 source별 성공 여부와 row 규모를 알 수 있도록 필요한 정보만 추립니다.

## 추가 함수 코드 단위 해석: `build_final_answer_prompt`의 prompt context

```python
prompt_context = {
    "user_question": user_question,
    "success": bool(result.get("success")),
    "summary": result.get("summary", ""),
    "error_message": result.get("error_message", ""),
```

최종 답변에 필요한 기본 상태를 context로 묶습니다.

```python
"result_preview_rows": preview_rows,
"result_has_data_ref": bool(data_ref),
"columns": list(preview_rows[0].keys()) if preview_rows else [],
```

전체 데이터를 넣지 않고 preview rows와 컬럼 정보만 prompt에 넣습니다.

```python
"filter_notes": result.get("filter_notes", []),
"merge_notes": result.get("merge_notes", []),
```

pandas executor의 필터 적용 결과와 source merge 정보를 답변 LLM이 참고할 수 있게 합니다.
