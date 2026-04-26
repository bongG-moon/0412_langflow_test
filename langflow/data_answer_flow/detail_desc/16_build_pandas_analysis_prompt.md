# 16. Build Pandas Analysis Prompt

조회된 raw data를 사용자의 질문 의도에 맞게 pandas로 전처리하도록 LLM prompt를 만드는 노드다.

## 입력

```text
template
analysis_context
main_context
domain_payload
```

권장 입력은 `analysis_context`다.

## 출력

```text
prompt
prompt_payload
```

권장 연결은 `prompt_payload`다.

```text
Build Pandas Analysis Prompt.prompt_payload
-> LLM API Caller.prompt
```

## prompt_payload 구조

```json
{
  "prompt": "...",
  "prompt_type": "pandas_analysis"
}
```

`LLM API Caller.response_mode=auto`에서는 JSON 응답 모드로 처리된다.

## Domain 사용 방식

이 노드는 전체 domain을 그대로 prompt에 넣지 않는다.

아래 정보만 추려서 넣는다.

- 현재 retrieval plan의 dataset
- 사용자 intent의 metric hint
- metric이 요구하는 required dataset
- 현재 dataframe profile
- 실제 조회 결과에서 확인된 allowed dataframe columns
- sample rows

즉 pandas 코드 생성에 필요한 실제 column, formula, metric 정보만 전달해 token 사용량을 줄인다. Domain이나 table catalog에 적힌 column보다 조회 결과 DataFrame의 column list가 우선이며, prompt에는 이 목록을 authoritative source로 안내한다.

## LLM 응답 형식

LLM은 JSON만 반환해야 한다.

```json
{
  "intent": "short summary",
  "operations": ["filter", "groupby", "agg"],
  "output_columns": [],
  "group_by_columns": [],
  "filters": [],
  "sort_by": "",
  "sort_order": "desc",
  "top_n": null,
  "metric_column": "",
  "warnings": [],
  "code": "result = df.copy()"
}
```

뒤 노드인 `Parse Pandas Analysis JSON`이 이 JSON을 검증하고, `Execute Pandas Analysis`가 안전성 검사를 거쳐 실행한다.

LLM이 실제 DataFrame에 없는 컬럼을 써야 하는 상황이면 code를 비워 두고 `warnings`에 누락 컬럼을 설명하도록 유도한다.
