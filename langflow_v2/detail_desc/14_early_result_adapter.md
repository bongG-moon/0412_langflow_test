# 14. Early Result Adapter

## 이 노드 역할

`finish` 또는 clarification route를 최종 답변 단계가 이해할 수 있는 `analysis_result` 형태로 바꾸는 노드입니다.

## 왜 필요한가

모든 질문이 DB 조회로 이어지는 것은 아닙니다.

예를 들어 다음과 같은 경우가 있습니다.

- 질문에 맞는 dataset을 찾지 못한 경우
- 필수 조회 조건이 부족한 경우
- 사용자에게 추가 정보를 요청해야 하는 경우
- 이미 안내 메시지를 바로 반환할 수 있는 경우

이때도 downstream의 `Analysis Result Merger`, `Build Final Answer Prompt`, `Final Answer Builder`는 `analysis_result` 형태를 기대합니다. 이 노드는 조기 종료 결과를 그 형태로 맞춥니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.finish` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | final answer 단계로 넘길 조기 종료 결과입니다. |

## 주요 함수 설명

- `_payload_from_value`: Langflow 입력값에서 dict를 꺼냅니다.
- `build_early_analysis_result`: finish branch payload를 `analysis_result`로 변환합니다.
- `build_result`: Langflow output method입니다.

## 초보자 확인용

이 노드는 조회도 pandas 분석도 하지 않습니다. "조회하지 않고 끝내야 하는 상황"을 최종 답변으로 보낼 수 있게 모양만 맞춥니다.

## 연결

```text
Intent Route Router.finish
-> Early Result Adapter.intent_plan

Early Result Adapter.analysis_result
-> Analysis Result Merger.early_result
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "intent_plan": {
    "route": "finish",
    "query_mode": "finish",
    "response": "데이터 조회에 필요한 필수 조건이 부족합니다: production.date",
    "failure_type": "missing_required_params",
    "required_params": {}
  },
  "state": {
    "session_id": "abc",
    "current_data": {}
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": false,
    "route": "finish",
    "response": "데이터 조회에 필요한 필수 조건이 부족합니다: production.date",
    "data": [],
    "columns": [],
    "row_count": 0,
    "intent_plan": {
      "route": "finish"
    }
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"intent_plan": {...}})` | `{"intent_plan": {...}}` | Router 출력 wrapper를 벗깁니다. |
| `build_early_analysis_result` | finish branch payload | `analysis_result` | 조기 종료 결과를 final answer와 같은 흐름에 태웁니다. |
| `build_result` | Langflow 입력값 | `Data(data=analysis_result)` | Langflow output method입니다. |

### 코드 흐름

```text
finish branch 입력
-> skipped이면 skipped analysis_result 반환
-> intent_plan.response 확인
-> current_data 존재 여부 확인
-> final answer가 읽을 analysis_result 형태로 변환
-> Analysis Result Merger로 전달
```

## 함수 코드 단위 해석: `build_early_analysis_result`

### 핵심 코드 해석

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
```

입력에서 실제 plan을 꺼냅니다.

```python
if payload.get("skipped"):
    return {"analysis_result": {"skipped": True, ...}}
```

선택되지 않은 branch라면 다음 merger가 무시할 수 있게 skipped 결과를 반환합니다.

```python
response = str(plan.get("response") or "요청을 완료할 수 없습니다. 조건을 조금 더 구체적으로 입력해주세요.")
```

plan에 있는 안내 메시지를 사용합니다. 없으면 기본 안내 문장을 만듭니다.

```python
"awaiting_analysis_choice": bool(state.get("current_data"))
```

이전 current_data가 있으면 사용자가 이어서 분석을 선택할 여지가 있다고 표시합니다.
