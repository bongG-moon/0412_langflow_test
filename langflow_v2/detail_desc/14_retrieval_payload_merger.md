# 14. Retrieval Payload Merger

## 한 줄 역할

single, multi, follow-up retrieval branch 중 실제로 실행된 payload 하나를 골라 다음 노드로 넘깁니다.

## 왜 필요한가

Langflow에서는 branch가 여러 개로 갈라져도 다시 하나로 합쳐야 뒤 처리를 공통으로 할 수 있습니다.

이 노드는 다음 세 branch를 하나로 모읍니다.

- single retrieval
- multi retrieval
- follow-up retrieval

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | 단일 조회 branch 결과입니다. |
| `multi_retrieval` | 복합 조회 branch 결과입니다. |
| `followup_retrieval` | 이전 current_data 재사용 branch 결과입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | 실제 선택된 retrieval 결과입니다. |

## 주요 함수 설명

- `_retrieval_payload`: 입력에서 실제 retrieval_payload를 꺼냅니다.
- `merge_retrieval_payloads`: skipped가 아닌 첫 번째 유효 payload를 선택합니다.

## 초보자 포인트

이 노드는 데이터를 합산하거나 join하지 않습니다.
"여러 branch 출력 중 어떤 branch가 진짜인가"를 고르는 역할입니다.

데이터 join이나 계산은 나중의 pandas 단계에서 합니다.

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
    "skipped": true
  },
  "multi_retrieval": {
    "retrieval_payload": {
      "success": true,
      "source_results": [
        {"dataset_key": "production"},
        {"dataset_key": "wip"}
      ]
    }
  },
  "followup_retrieval": {
    "skipped": true
  }
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ],
    "selected_retrieval_branch": "multi_retrieval"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_retrieval_payload` | `{"retrieval_payload": {...}}` | `{...}` | retriever 출력이 한 겹 감싸져 있어도 실제 retrieval payload를 꺼냅니다. |
| `merge_retrieval_payloads` | single/multi/followup 입력 | active retrieval payload | 여러 branch 중 skipped가 아닌 첫 번째 실제 결과를 선택합니다. |
| `build_payload` | Langflow inputs | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
single branch 확인
-> multi branch 확인
-> followup branch 확인
-> skipped가 아닌 payload 선택
-> selected_retrieval_branch 표시
```

### 초보자 포인트

Langflow에서는 여러 branch output이 동시에 다음 노드에 연결될 수 있습니다. 그래서 각 branch가 `skipped`인지 확인하고 실제 실행된 branch만 고르는 합류 지점이 필요합니다.

## 함수 코드 단위 해석: `merge_retrieval_payloads`

이 함수는 single, multi, follow-up 세 입력 중 실제 실행된 retrieval payload 하나를 고릅니다.

### 함수 input

```json
{
  "single_retrieval_value": {"skipped": true},
  "multi_retrieval_value": {
    "retrieval_payload": {
      "route": "multi_retrieval",
      "source_results": [{"dataset_key": "production"}]
    }
  },
  "followup_retrieval_value": {"skipped": true}
}
```

### 함수 output

```json
{
  "retrieval_payload": {
    "route": "multi_retrieval",
    "source_results": [{"dataset_key": "production"}],
    "selected_retrieval_branch": "multi_retrieval"
  }
}
```

### 핵심 코드 해석

```python
for branch, value in candidates:
```

single, multi, followup 후보를 순서대로 검사합니다.

```python
payload = _retrieval_payload(value)
```

각 후보에서 실제 retrieval payload를 꺼냅니다.

```python
if not payload or payload.get("skipped"):
    continue
```

값이 비어 있거나 skipped branch이면 건너뜁니다.

```python
merged = deepcopy(payload)
merged["selected_retrieval_branch"] = branch
return {"retrieval_payload": merged}
```

실제 branch를 찾으면 복사본을 만들고 어떤 branch였는지 표시한 뒤 반환합니다.

```python
return {"retrieval_payload": {"skipped": True, ...}}
```

어느 branch도 실행되지 않았으면 skipped payload를 반환합니다. 뒤 노드가 실패 원인을 알 수 있게 하기 위함입니다.
