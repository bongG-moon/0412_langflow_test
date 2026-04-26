# 13. Early Result Adapter

## 한 줄 역할

`finish` branch를 최종 단계가 이해할 수 있는 `analysis_result` 형태로 바꾸는 노드입니다.

## 언제 쓰나?

다음과 같은 경우에는 데이터 조회를 진행하지 않고 바로 답해야 합니다.

- 필수 조건이 부족함: `production.date`가 없음
- 질문이 데이터 조회가 필요 없는 안내성 질문임
- intent 단계에서 이미 실패 또는 clarification이 결정됨

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.finish` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `analysis_result` | final answer 단계로 넘길 표준 결과입니다. |

## 주요 함수 설명

- `_payload_from_value`: 입력 payload를 dict로 꺼냅니다.
- `build_early_analysis_result`: finish 이유, 에러, summary를 analysis_result로 정리합니다.

## 초보자 포인트

`analysis_result`라는 이름 때문에 pandas 분석 결과처럼 보일 수 있지만, 여기서는 "조회 없이 끝난 결과"도 같은 형태로 맞추는 것이 목적입니다.

뒤의 `Analysis Result Merger`는 early/direct/pandas 중 어떤 결과든 하나로 합쳐야 하기 때문에 형태를 맞춰 둡니다.

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
    "query_mode": "clarification",
    "missing_params": ["production.date"],
    "response": "조회에 필요한 날짜 조건이 필요합니다."
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": false,
    "result_type": "early_finish",
    "response": "조회에 필요한 날짜 조건이 필요합니다.",
    "errors": ["missing required params: production.date"],
    "source_results": [],
    "final_rows": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"intent_plan": {...}})` | `{"intent_plan": {...}}` | router output을 dict로 꺼냅니다. |
| `build_early_analysis_result` | finish branch payload | analysis result | 조회 없이 끝나는 branch도 뒤의 `Analysis Result Merger`가 읽을 수 있는 표준 결과로 바꿉니다. |
| `build_result` | Langflow input | `Data(data=analysis_result)` | Langflow output method입니다. |

### 코드 흐름

```text
finish/clarification branch 입력
-> 사용자에게 바로 보여줄 response와 errors 구성
-> source_results/final_rows는 빈 배열로 맞춤
-> Analysis Result Merger로 전달
```

### 초보자 포인트

모든 branch가 최종 답변으로 가려면 출력 모양이 같아야 합니다. 이 노드는 "조회 안 함" branch를 analysis_result 모양으로 맞추는 변환기입니다.

## 함수 코드 단위 해석: `build_early_analysis_result`

이 함수는 조회 없이 끝나는 상황을 최종 답변 흐름에 맞는 `analysis_result`로 바꿉니다.

### 함수 input

```json
{
  "intent_plan": {
    "route": "finish",
    "response": "데이터 조회에 필요한 필수 조건이 부족합니다: production.date",
    "failure_type": "missing_required_params"
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "success": false,
    "tool_name": "early_finish",
    "data": [],
    "summary": "데이터 조회에 필요한 필수 조건이 부족합니다: production.date",
    "error_message": "데이터 조회에 필요한 필수 조건이 부족합니다: production.date",
    "analysis_logic": "missing_required_params"
  }
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
```

router output에서 실제 intent plan을 꺼냅니다.

```python
response = str(plan.get("response") or "요청을 완료하기 위한 정보가 부족합니다.")
```

사용자에게 보여줄 안내 문장을 정합니다. plan에 response가 없으면 기본 문구를 씁니다.

```python
result = {
    "success": False,
    "tool_name": "early_finish",
    "data": [],
    ...
}
```

조회하지 않았으므로 `success=False`, `data=[]`입니다. 하지만 뒤 노드가 읽을 수 있게 `tool_name`, `summary`, `analysis_logic` 같은 key는 채워 둡니다.

```python
return {"analysis_result": result}
```

최종 답변 builder까지 같은 경로로 보낼 수 있도록 analysis_result로 감쌉니다.
