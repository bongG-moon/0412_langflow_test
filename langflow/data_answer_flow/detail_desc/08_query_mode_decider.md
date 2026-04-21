# 08. Query Mode Decider

이번 질문이 새 원본 데이터 조회가 필요한지, 이전 current_data를 재사용해서 후처리만 하면 되는지 판단하는 노드다.

## 입력

```text
intent
main_context     optional
agent_state      legacy optional
domain_payload   legacy optional
```

새 구조에서는 `Request Type Router.data_question` 안에 `main_context`가 들어 있으므로 `domain_payload`를 직접 연결하지 않아도 된다.

## 출력

```text
query_mode_decision -> Data
```

출력 payload에도 `main_context`가 유지된다.

## 주요 query_mode

```text
retrieval            새 데이터 조회 필요
followup_transform   기존 current_data 재사용 가능
clarification        필수 조건 부족 또는 Phase 1 미지원
```

## 판단 기준

- 필요한 dataset이 현재 source snapshot에 없으면 새 조회로 간다.
- dataset 필수 parameter가 바뀌면 새 조회로 간다.
- 필수 parameter는 그대로이고 product/process/top_n/group_by 같은 후처리 조건만 바뀌면 `followup_transform`으로 간다.
- 현재 데이터도 없고 필수 조건도 부족하면 clarification으로 간다.

## 권장 연결

```text
Request Type Router.data_question
-> Query Mode Decider.intent

Query Mode Decider.query_mode_decision
-> Retrieval Plan Builder.query_mode_decision
```
