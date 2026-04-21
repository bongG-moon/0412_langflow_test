# 16. Parse Pandas Analysis JSON

built-in LLM이 반환한 pandas 분석 계획 JSON을 파싱하는 노드다.

## 입력

```text
llm_output
```

## 출력

```text
analysis_plan
```

## 역할

- Message, Data, Text 형태의 LLM output에서 텍스트를 꺼낸다.
- markdown code fence가 있어도 JSON object만 추출한다.
- `operations`, `group_by_columns`, `warnings`, `code` 등을 표준 shape으로 정리한다.
- 코드가 비어 있으면 parse error에 기록하지만, 다음 실행 노드에서 fallback 분석을 시도할 수 있다.

## 다음 연결

```text
Parse Pandas Analysis JSON.analysis_plan
-> Execute Pandas Analysis.analysis_plan
```
