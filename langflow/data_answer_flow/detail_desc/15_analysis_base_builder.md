# 15. Analysis Base Builder

조회 결과를 pandas 분석이 가능한 `analysis_context`로 정리하는 노드다.

## 입력

```text
retrieval_result
main_context     optional
domain_payload   legacy optional
agent_state      legacy optional
```

새 구조에서는 `Dummy/Oracle Data Retriever.retrieval_result` 안에 `main_context`가 들어 있으므로 `domain_payload`와 `agent_state`는 직접 연결하지 않아도 된다.

## 출력

```text
analysis_context -> Data
```

## 역할

- 조회 실패나 clarification은 `early_result`로 유지한다.
- source dataset이 하나면 그대로 analysis table로 사용한다.
- source dataset이 여러 개면 domain의 `join_rules` 또는 공통 column 기준으로 병합한다.
- 병합 결과, source_results, current_datasets, source_snapshots, intent, agent_state, main_context를 하나의 context로 묶는다.

## 권장 연결

```text
Dummy Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

또는:

```text
OracleDB Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

다음:

```text
Analysis Base Builder.analysis_context
-> Build Pandas Analysis Prompt.analysis_context

Analysis Base Builder.analysis_context
-> Execute Pandas Analysis.analysis_context
```
