# 11. Retrieval Plan Builder

`Query Mode Decider` 결과를 실제 조회 job 목록으로 바꾸는 노드다.

## 입력

```text
query_mode_decision
main_context     optional
domain_payload   legacy optional
agent_state      legacy optional
```

새 구조에서는 `Query Mode Decider.query_mode_decision` 안에 `main_context`가 들어 있으므로 `domain_payload`와 `agent_state`는 직접 연결하지 않아도 된다.

## 출력

```text
retrieval_plan -> Data
```

출력 payload 예시:

```json
{
  "retrieval_plan": {
    "route": "single_retrieval",
    "query_mode": "retrieval",
    "dataset_keys": ["production"],
    "jobs": [
      {
        "dataset_key": "production",
        "params": {"date": "2026-04-21"},
        "query_template": "SELECT ... WHERE WORK_DT = :date",
        "db_key": "MES"
      }
    ]
  },
  "retrieval_jobs": [],
  "retrieval_route": "single_retrieval",
  "intent": {},
  "agent_state": {},
  "main_context": {}
}
```

## 역할

- `followup_transform`이면 새 조회 job을 만들지 않고 기존 데이터를 재사용하도록 표시한다.
- `retrieval`이면 domain의 dataset 정의를 보고 필요한 dataset별 job을 만든다.
- dataset `required_params`가 부족하면 `early_result`를 만들어 뒤 노드가 바로 안내 답변으로 끝낼 수 있게 한다.
- metric이 여러 dataset을 요구하면 여러 job을 만든다.

## 다음 연결

더미 조회:

```text
Retrieval Plan Builder.retrieval_plan
-> Dummy Data Retriever.retrieval_plan
```

Oracle 조회:

```text
Retrieval Plan Builder.retrieval_plan
-> OracleDB Data Retriever.retrieval_plan
```
