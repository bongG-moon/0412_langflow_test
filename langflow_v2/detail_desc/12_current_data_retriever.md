# 12. Current Data Retriever

## 한 줄 역할

후속 질문에서 이전 결과인 `state.current_data`를 새 조회 결과처럼 다시 꺼내는 노드입니다.

## 언제 쓰나?

첫 질문:

```text
오늘 DA공정 생산량 알려줘
```

후속 질문:

```text
이때 가장 생산량이 많았던 MODE 알려줘
```

두 번째 질문은 DB를 새로 조회할 필요가 없습니다.
이전 결과를 pandas로 다시 분석하면 됩니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.followup_transform` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | 이전 current_data를 source_results처럼 감싼 payload입니다. |

## 주요 함수 설명

- `_source_result_from_current_data`: current_data를 source_result 형태로 바꿉니다.
- `_build_current_datasets`: 현재 데이터의 dataset 요약을 만듭니다.
- `retrieve_current_data`: 후속 분석에 필요한 retrieval_payload를 만듭니다.

## 초보자 포인트

이름은 Retriever지만 DB 조회를 하지 않습니다.
이미 가지고 있는 데이터를 "조회 결과처럼" 포장해서 뒤 노드들이 같은 방식으로 처리하게 만듭니다.

## 연결

```text
Intent Route Router.followup_transform
-> Current Data Retriever.intent_plan

Current Data Retriever.retrieval_payload
-> Retrieval Payload Merger.followup_retrieval
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "intent_plan": {
    "route": "followup_transform",
    "state": {
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 10},
          {"MODE": "B", "production": 20}
        ],
        "summary": "previous production result"
      }
    }
  }
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "success": true,
    "query_mode": "followup_transform",
    "source_results": [
      {
        "success": true,
        "dataset_key": "current_data",
        "tool_name": "current_data",
        "data": [
          {"MODE": "A", "production": 10},
          {"MODE": "B", "production": 20}
        ]
      }
    ],
    "current_data": {
      "rows": [
        {"MODE": "A", "production": 10},
        {"MODE": "B", "production": 20}
      ]
    }
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_rows_columns` | `[{"MODE": "A", "production": 10}]` | `["MODE", "production"]` | 현재 데이터의 컬럼 정보를 요약합니다. |
| `_build_current_datasets` | source_results | `{"current_data": {"rows": [...]}}` | 후속 질문에서도 current_data 구조를 유지합니다. |
| `_source_result_from_current_data` | state.current_data | source result | 이전 결과를 retriever가 조회한 것처럼 같은 schema로 감쌉니다. |
| `retrieve_current_data` | intent plan | retrieval payload | 후속 질문 branch에서 이전 데이터를 다시 분석 가능한 payload로 만듭니다. |
| `build_payload` | Langflow input | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
intent_plan.state.current_data 확인
-> rows 또는 datasets에서 기존 데이터 추출
-> source_results 형식으로 변환
-> Retrieval Payload Merger에 전달
```

### 초보자 포인트

이 노드는 DB를 새로 조회하지 않습니다. "이때", "위 결과" 같은 후속 질문에서 이전 결과를 다시 조회 결과처럼 포장해 다음 분석 단계로 넘깁니다.

## 함수 코드 단위 해석: `retrieve_current_data`

이 함수는 state 안의 `current_data`를 조회 결과처럼 바꿔 줍니다.

### 함수 input

```json
{
  "intent_plan": {
    "route": "followup_transform",
    "state": {
      "current_data": {
        "data": [
          {"MODE": "A", "production": 10}
        ],
        "summary": "previous result"
      }
    }
  }
}
```

### 함수 output

```json
{
  "retrieval_payload": {
    "route": "followup_transform",
    "source_results": [
      {
        "dataset_key": "current_data",
        "data": [
          {"MODE": "A", "production": 10}
        ]
      }
    ]
  }
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
```

router에서 넘어온 값을 dict로 바꾸고 실제 intent plan을 꺼냅니다.

```python
state = payload.get("state") if isinstance(payload.get("state"), dict) else plan.get("state", {})
current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
```

후속 분석의 기준이 되는 `current_data`를 state에서 찾습니다.

```python
source_results = [_source_result_from_current_data(current_data)] if current_data else []
```

current_data가 있으면 source result 하나로 감쌉니다. 이렇게 해야 뒤의 `Retrieval Payload Merger`와 pandas 노드가 신규 조회 결과와 같은 방식으로 처리할 수 있습니다.

```python
return {"retrieval_payload": {...}}
```

후속 질문 branch도 retrieval payload 형식으로 반환합니다. 뒤 노드는 이것이 DB 조회인지 current data 재사용인지 몰라도 같은 구조로 읽습니다.
