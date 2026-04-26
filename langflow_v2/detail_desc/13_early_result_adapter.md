# 13. Early Result Adapter

## 한 줄 역할

`finish` branch를 최종 단계가 이해할 수 있는 `analysis_result` 형태로 바꾸는 노드입니다.

## 언제 쓰나?

다음과 같은 경우에는 데이터 조회를 진행하지 않고 바로 답해야 합니다.

- 필수 조건이 부족함: `production.date`가 없음
- 질문이 데이터 조회가 필요 없는 안내성 질문임
- intent 단계에서 이미 실패 또는 clarification이 결정됨

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.finish` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | final answer 단계로 넘길 표준 결과입니다. |

## 주요 함수 설명

- `_payload_from_value`: 입력 payload를 dict로 꺼냅니다.
- `build_early_analysis_result`: finish 이유, 에러, summary를 analysis_result로 정리합니다.

## 초보자 포인트

`analysis_result`라는 이름 때문에 pandas 분석 결과처럼 보일 수 있지만, 여기서는 "조회 없이 끝난 결과"도 같은 형태로 맞추는 것이 목적입니다.

뒤의 `Analysis Result Merger`는 early/direct/pandas 중 어떤 결과든 하나로 합쳐야 하기 때문에 형태를 맞춰 둡니다.

## 연결

```text
Intent Route Router.finish
-> Early Result Adapter.intent_plan

Early Result Adapter.analysis_result
-> Analysis Result Merger.early_result
```

