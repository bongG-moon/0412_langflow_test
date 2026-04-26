# 19. Pandas Analysis Executor

## 한 줄 역할

`analysis_plan_payload` 안의 pandas 코드를 실행해서 최종 분석 row를 만드는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `analysis_plan_payload` | `Normalize Pandas Plan` 출력입니다. |
| `retrieval_payload` | 실험용 override입니다. 보통 연결하지 않아도 됩니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | pandas 분석 결과입니다. |

## 주요 함수 설명

- `_merge_sources`: 여러 source result를 pandas DataFrame으로 만들 row list로 합칩니다.
- `_apply_filters`: intent filter를 DataFrame에 적용합니다.
- `_validate_code`: 실행 전에 코드가 너무 위험하지 않은지 간단히 확인합니다.
- `_execute_code`: 제한된 환경에서 pandas 코드를 실행합니다.
- `execute_pandas_analysis`: 전체 실행 과정을 관리합니다.

## 실행 결과 구조

```json
{
  "analysis_result": {
    "success": true,
    "data": [],
    "summary": "분석 결과 ...",
    "intent_plan": {}
  }
}
```

## 초보자 포인트

이 노드는 실제로 코드를 실행하므로 가장 조심해야 하는 부분입니다.

그래서 실행 환경에 `pd`, `df`, `source_frames` 같은 필요한 값만 넣고, 위험한 built-in 사용은 제한합니다.

## 연결

```text
Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result
```

