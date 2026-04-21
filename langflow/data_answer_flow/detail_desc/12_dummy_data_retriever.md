# 12. Dummy Data Retriever

조회 plan을 받아 deterministic dummy 데이터를 생성하는 테스트용 조회 노드다.

## 입력

```text
retrieval_plan
main_context     optional
domain_payload   legacy optional
agent_state      legacy optional
row_limit
```

새 구조에서는 `Retrieval Plan Builder.retrieval_plan` 안에 `main_context`가 들어 있으므로 `domain_payload`와 `agent_state`는 직접 연결하지 않아도 된다.

## 출력

```text
retrieval_result -> Data
```

## 역할

- domain의 dataset columns를 기준으로 더미 row를 만든다.
- 제품/공정 정보가 domain에 있으면 더미 row에도 반영한다.
- `followup_transform`이면 새 더미 데이터를 만들지 않고 `agent_state.current_data`를 source처럼 재사용한다.
- Oracle 조회 노드와 같은 output shape를 반환한다.

## 권장 연결

```text
Retrieval Plan Builder.retrieval_plan
-> Dummy Data Retriever.retrieval_plan

Dummy Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```
