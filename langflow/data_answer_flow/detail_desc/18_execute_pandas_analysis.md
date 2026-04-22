# 18. Execute Pandas Analysis

LLM이 만든 pandas 코드를 안전 검증 후 실행하는 노드다.

## 입력

```text
analysis_context
analysis_plan
```

## 출력

```text
analysis_result
```

## 역할

- `analysis_context.analysis_table.data`를 pandas DataFrame으로 만든다.
- intent의 filters와 filter expressions를 먼저 적용한다.
- LLM code에 import, 파일 접근, eval, exec, OS API 같은 위험 구문이 있는지 검사한다.
- 안전한 코드만 실행하고 최종 DataFrame을 row list로 반환한다.
- LLM code가 비었거나 실패하면 간단한 fallback 분석을 시도한다.

## 출력 핵심

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "analyze_current_data",
    "data": [],
    "summary": "데이터 분석 완료: 3건",
    "generated_code": "result = df.copy()",
    "current_datasets": {},
    "source_snapshots": []
  }
}
```

## 다음 연결

```text
Execute Pandas Analysis.analysis_result
-> Build Answer Prompt.analysis_result

Execute Pandas Analysis.analysis_result
-> Final Answer Builder.analysis_result
```
