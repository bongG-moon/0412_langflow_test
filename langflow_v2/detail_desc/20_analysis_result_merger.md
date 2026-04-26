# 20. Analysis Result Merger

## 한 줄 역할

early, direct, pandas branch 중 실제 결과 하나를 골라 `analysis_result`로 통합하는 노드입니다.

## 왜 필요한가

앞 흐름은 여러 branch로 나뉩니다.

- 조건 부족으로 빨리 끝난 결과
- 조회만 하고 바로 답하는 결과
- pandas 분석을 거친 결과

최종 답변 단계는 하나의 입력만 받는 것이 편하므로 이 노드가 branch를 다시 합칩니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `early_result` | `Early Result Adapter` 출력입니다. |
| `direct_result` | `Direct Result Adapter` 출력입니다. |
| `pandas_result` | `Pandas Analysis Executor` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | 선택된 최종 분석 결과입니다. |

## 주요 함수 설명

- `_analysis_result`: 입력에서 실제 result payload를 꺼냅니다.
- `merge_analysis_results`: skipped가 아닌 유효 결과를 우선순위대로 선택합니다.

## 초보자 포인트

이 노드는 데이터를 계산하지 않습니다.
"이번 턴에서 살아남은 branch 결과가 무엇인가"를 고릅니다.

## 연결

```text
Early Result Adapter.analysis_result
-> Analysis Result Merger.early_result

Direct Result Adapter.analysis_result
-> Analysis Result Merger.direct_result

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result

Analysis Result Merger.analysis_result
-> Build Final Answer Prompt.analysis_result
```

