# 07. Normalize Intent Plan

## 한 줄 역할

LLM의 intent 응답을 실제 flow가 사용할 수 있는 `intent_plan`으로 정리하고 보정하는 노드입니다.

## 왜 중요한가

LLM은 가끔 dataset을 하나만 말하거나, 날짜를 빼먹거나, 후속 질문을 새 조회처럼 해석할 수 있습니다.
이 노드는 domain과 table catalog를 다시 확인해서 그런 실수를 줄입니다.

특히 metric에 `required_datasets`가 있으면, LLM이 하나만 말해도 필요한 dataset을 모두 retrieval plan에 추가합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Intent)`의 출력입니다. |
| `reference_date` | 테스트용 기준 날짜입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `intent_plan` | route, retrieval_jobs, filters, group_by 등을 포함한 실행 계획입니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON object를 찾습니다.
- `_extract_date`: `오늘`, `어제` 같은 표현을 날짜로 바꿉니다.
- `_dataset_hints`: 질문과 table/domain 정보를 보고 필요한 dataset 후보를 찾습니다.
- `_matched_metrics`: 질문에 맞는 metric 규칙을 domain에서 찾습니다.
- `_filters_from_question`: 공정, 제품, 조건 표현을 filter로 바꿉니다.
- `_build_job`: dataset 하나를 조회하기 위한 retrieval job을 만듭니다.
- `_normalize_plan`: 전체 intent plan을 route 가능한 형태로 완성합니다.

## 출력 예시

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "query_mode": "retrieval",
    "dataset_hints": ["production", "target"],
    "required_params": {"date": "20260426"},
    "needs_pandas": true
  },
  "retrieval_jobs": []
}
```

## 초보자 포인트

이 노드는 LLM 결과를 그대로 믿지 않습니다.
규칙 기반 보정을 함께 합니다.

예를 들어 `생산달성율`이 domain에서 `production`, `target`을 요구한다면, LLM이 `production`만 반환해도 이 노드가 `target`을 추가합니다.

## 연결

```text
LLM JSON Caller (Intent).llm_result
-> Normalize Intent Plan.llm_result

Normalize Intent Plan.intent_plan
-> Intent Route Router.intent_plan
```

