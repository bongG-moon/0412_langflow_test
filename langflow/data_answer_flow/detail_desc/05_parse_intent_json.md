# 05. Parse Intent JSON

intent 추출 LLM 결과를 표준 intent JSON으로 파싱하는 노드다.

## 입력

```text
llm_result
llm_text
```

`llm_result`는 `Data`, `Message`, `Text`, `JSON` 타입을 받을 수 있다.

## 출력

```text
intent_raw
```

## 역할

- built-in LLM output 또는 `LLM JSON Caller.llm_result`에서 텍스트를 꺼낸다.
- markdown code fence가 섞여 있어도 JSON object만 추출한다.
- intent의 기본 필드를 보정한다.
- `request_type`, `dataset_hints`, `metric_hints`, `required_params`, `filters`, `group_by`, `top_n` 등을 표준 shape으로 만든다.

## 기본 연결

```text
built-in LLM output
-> Parse Intent JSON.llm_result

Parse Intent JSON.intent_raw
-> Normalize Intent With Domain.intent_raw
```

## fallback 연결

```text
LLM JSON Caller.llm_result
-> Parse Intent JSON.llm_result
```
