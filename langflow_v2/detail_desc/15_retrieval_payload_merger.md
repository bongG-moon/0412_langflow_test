# 15. Retrieval Payload Merger

## 이 노드 역할

single retrieval, multi retrieval, follow-up retrieval 중 실제 active branch 하나를 골라 하나의 `retrieval_payload`로 합치는 노드입니다.

## 왜 필요한가

Langflow 화면에서는 route별 branch가 여러 갈래로 나뉩니다.

- `single_retrieval`
- `multi_retrieval`
- `followup_retrieval`

하지만 다음 `Retrieval Postprocess Router`는 하나의 retrieval payload만 받는 것이 단순합니다. 그래서 이 노드가 여러 branch 입력 중 skipped가 아닌 첫 번째 active payload를 선택합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | single retrieval branch의 조회 결과입니다. |
| `multi_retrieval` | multi retrieval branch의 조회 결과입니다. |
| `followup_retrieval` | `Current Data Retriever`의 후속 분석용 조회 payload입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | downstream에서 사용할 active retrieval payload입니다. |

## 주요 함수 설명

- `_payload_from_value`: Langflow 입력값을 dict로 꺼냅니다.
- `_retrieval_payload`: wrapper 안의 실제 `retrieval_payload`를 꺼냅니다.
- `merge_retrieval_payloads`: 여러 branch 중 active retrieval payload 하나를 선택합니다.
- `build_payload`: Langflow output method입니다.

## 초보자 확인용

이 노드는 데이터를 합산하거나 join하지 않습니다. 여러 route branch 중 "이번 턴에 실제로 선택된 조회 결과" 하나를 고르는 노드입니다.

multi retrieval의 여러 dataset 결과는 이미 `multi_retrieval` payload 안의 `source_results`에 들어 있습니다. 이 노드는 single과 multi를 합치는 것이 아니라 branch를 선택합니다.

## 연결

```text
Dummy/Oracle Retriever (Single).retrieval_payload
-> Retrieval Payload Merger.single_retrieval

Dummy/Oracle Retriever (Multi).retrieval_payload
-> Retrieval Payload Merger.multi_retrieval

Current Data Retriever.retrieval_payload
-> Retrieval Payload Merger.followup_retrieval

Retrieval Payload Merger.retrieval_payload
-> Retrieval Postprocess Router.retrieval_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "single_retrieval": {
    "retrieval_payload": {
      "skipped": true,
      "skip_reason": "selected route is multi_retrieval"
    }
  },
  "multi_retrieval": {
    "retrieval_payload": {
      "route": "multi_retrieval",
      "source_results": [
        {"dataset_key": "production"},
        {"dataset_key": "target"}
      ]
    }
  },
  "followup_retrieval": {}
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "route": "multi_retrieval",
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "target"}
    ],
    "merged_from": "multi_retrieval",
    "skipped_retrieval_branches": [
      {
        "source": "single_retrieval",
        "skip_reason": "selected route is multi_retrieval"
      }
    ]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"retrieval_payload": {...}})` | `{"retrieval_payload": {...}}` | Langflow wrapper를 벗깁니다. |
| `_retrieval_payload` | `{"retrieval_payload": {"route": "single"}}` | `{"route": "single"}` | 실제 retrieval payload만 꺼냅니다. |
| `merge_retrieval_payloads` | single, multi, followup | active retrieval payload | 여러 branch 중 skipped가 아닌 payload를 선택합니다. |
| `build_payload` | Langflow 입력값 | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
single/multi/followup branch 입력
-> 각 입력에서 retrieval_payload 추출
-> 순서대로 skipped 여부 확인
-> 첫 번째 active payload 선택
-> merged_from 표시
-> skipped branch 목록 보존
-> 다음 postprocess router로 전달
```

## 함수 코드 단위 해석: `merge_retrieval_payloads`

이 함수는 branch별 retrieval payload 중 실제 사용할 하나를 선택합니다.

### 함수 input

```json
{
  "single_retrieval_value": {"retrieval_payload": {"skipped": true}},
  "multi_retrieval_value": {"retrieval_payload": {"route": "multi_retrieval", "source_results": []}},
  "followup_retrieval_value": null
}
```

### 함수 output

```json
{
  "retrieval_payload": {
    "route": "multi_retrieval",
    "source_results": [],
    "merged_from": "multi_retrieval"
  }
}
```

### 핵심 코드 해석

```python
candidates = [
    ("single_retrieval", _retrieval_payload(single_retrieval_value)),
    ("multi_retrieval", _retrieval_payload(multi_retrieval_value)),
    ("followup_transform", _retrieval_payload(followup_retrieval_value)),
]
```

세 branch 입력을 같은 형태의 후보 목록으로 만듭니다.

```python
if retrieval.get("skipped"):
    skipped.append({"source": source, "skip_reason": retrieval.get("skip_reason", "")})
    continue
```

선택되지 않은 branch는 skipped 목록에 기록하고 다음 후보를 봅니다.

```python
merged = deepcopy(retrieval)
merged["merged_from"] = source
return {"retrieval_payload": merged}
```

skipped가 아닌 첫 번째 payload를 선택하고, 어디서 왔는지 `merged_from`에 기록합니다.

```python
return {
    "retrieval_payload": {
        "skipped": True,
        "skip_reason": "No active retrieval branch produced a retrieval payload.",
        ...
    }
}
```

모든 branch가 비어 있거나 skipped라면 downstream이 안전하게 멈출 수 있도록 skipped payload를 반환합니다.
