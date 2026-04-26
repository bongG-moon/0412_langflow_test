# 18. Normalize Pandas Plan

## 한 줄 역할

LLM이 만든 pandas 분석 계획을 파싱하고, 실행 가능한 `analysis_plan_payload`로 정리하는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Pandas)` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_plan_payload` | pandas 코드, 입력 row, 컬럼, intent plan을 담은 실행 계획입니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON을 찾습니다.
- `_fallback_code`: LLM 응답이 없거나 깨졌을 때 기본 pandas 코드를 만듭니다.
- `normalize_pandas_plan`: 코드, 설명, warnings, retrieval payload를 정리합니다.

## LLM이 기대하는 반환 형태

```json
{
  "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
  "explanation": "MODE별 생산량 합계를 계산합니다."
}
```

## 초보자 포인트

이 노드는 LLM 코드를 바로 실행하지 않습니다.
실행 전 한 번 구조를 정리하는 안전장치입니다.

LLM이 실패해도 fallback code를 만들어 flow가 완전히 멈추지 않게 합니다.

## 연결

```text
LLM JSON Caller (Pandas).llm_result
-> Normalize Pandas Plan.llm_result

Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload
```

