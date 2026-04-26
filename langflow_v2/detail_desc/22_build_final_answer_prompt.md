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
    "summary": "mode별 생산량"
  },
  "preview_row_limit": "20"
}
```

### 출력 예시

```json
{
  "prompt_payload": {
    "prompt": "Write a Korean answer using this final data...",
    "analysis_result": {
      "success": true,
      "final_rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    },
    "preview_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_analysis_result` | `{"analysis_result": {...}}` | result dict | 앞 merger/store 출력에서 실제 분석 결과를 꺼냅니다. |
| `_safe_rows` | rows, limit 20 | 최대 20개 rows | prompt에 너무 많은 row가 들어가지 않게 제한합니다. |
| `_row_count_from_result` | result, preview rows | 전체 row count | preview보다 전체 결과가 몇 건인지 답변에 알려주기 위해 계산합니다. |
| `_source_summaries` | analysis result | source 요약 배열 | 최종 답변 LLM이 어떤 데이터에서 온 결과인지 알 수 있게 합니다. |
| `build_final_answer_prompt` | analysis result | prompt payload | 최종 답변 LLM에 넣을 문장, preview, 요약을 만듭니다. |
| `build_prompt` | Langflow input | `Data(data=prompt_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
analysis_result 입력
-> final_rows preview 생성
-> row_count/source summary 계산
-> 최종 답변 LLM이 지켜야 할 규칙과 JSON schema 작성
```

### 초보자 포인트

이 노드도 LLM을 호출하지 않습니다. 최종 답변 LLM이 "최종 데이터에 근거해 답하라"고 읽을 prompt를 만드는 역할입니다.

## 함수 코드 단위 해석: `build_final_answer_prompt`

이 함수는 최종 답변 LLM에게 줄 prompt와 preview data를 만듭니다.

### 함수 input

```json
{
  "analysis_result_value": {
    "analysis_result": {
      "success": true,
      "data": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ],
      "summary": "data analysis complete: 2 rows"
    }
  },
  "preview_row_limit_value": "20"
}
```

### 함수 output

```json
{
  "prompt_payload": {
    "prompt": "You are a manufacturing data analyst...",
    "preview_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  }
}
```

### 핵심 코드 해석

```python
result = _analysis_result(analysis_result_value)
```

앞 노드에서 온 값을 실제 analysis result dict로 꺼냅니다.

```python
rows = result.get("data") if isinstance(result.get("data"), list) else []
preview_rows = _safe_rows(rows, preview_limit)
```

최종 데이터 rows를 꺼내고, prompt에 넣을 만큼만 제한합니다.

```python
row_count = _row_count_from_result(result, preview_rows)
```

전체 결과 건수를 계산합니다. preview가 20건이어도 실제 row_count가 200건이면 답변에 전체 건수를 알려줄 수 있습니다.

```python
source_summaries = _source_summaries(result)
```

결과가 어떤 source dataset에서 왔는지 요약합니다.

```python
prompt = f"""..."""
```

LLM에게 다음 규칙을 지시합니다.

- final data에 없는 내용을 지어내지 말 것
- 숫자는 final data 기준으로 말할 것
- 한국어로 답할 것
- JSON 형태로 `response`를 반환할 것

```python
return {"prompt_payload": {...}}
```

LLM Caller가 prompt를 읽고, 뒤 normalizer가 원래 analysis_result도 참고할 수 있게 context를 같이 반환합니다.
