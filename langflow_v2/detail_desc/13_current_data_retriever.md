# 13. Current Data Retriever

## 이 노드 역할

이전 턴의 `state.current_data`를 새 조회 없이 재사용해서 `retrieval_payload` 형태로 감싸는 노드입니다.

## 왜 필요한가

사용자가 "그 결과를 mode별로 정리해줘", "이때 가장 생산량이 많은 mode는?"처럼 이전 결과를 이어서 분석할 수 있습니다.

이 경우 Oracle이나 dummy retriever로 새 조회를 하면 안 됩니다. 이미 있는 current data를 pandas 분석 단계로 넘겨야 합니다. 이 노드가 그 변환을 담당합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.followup_transform` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | current_data를 source_result처럼 감싼 payload입니다. |

## 주요 함수 설명

- `_payload_from_value`: Langflow 입력에서 dict를 꺼냅니다.
- `_rows_columns`: row list에서 컬럼명을 추출합니다.
- `_build_current_datasets`: source_results를 dataset별 current dataset 구조로 바꿉니다.
- `_source_result_from_current_data`: current_data 하나를 source_result 형태로 변환합니다.
- `retrieve_current_data`: follow-up intent plan에서 current data retrieval payload를 만듭니다.
- `build_payload`: Langflow output method입니다.

## 초보자 확인용

이 노드는 DB를 조회하지 않습니다. 이전 결과를 "조회 결과처럼 보이게" 포장하는 노드입니다.

`current_data`가 없으면 source_results가 빈 상태로 반환됩니다. 그래서 후속 질문이 제대로 동작하려면 `25 Final Answer Builder`가 이전 턴에서 `next_state.current_data`를 잘 저장해야 합니다.

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
    "query_mode": "followup_transform",
    "group_by": ["MODE"],
    "state": {
      "current_data": {
        "data": [
          {"MODE": "DDR5", "production": 2940},
          {"MODE": "HBM3", "production": 1800}
        ],
        "source_dataset_keys": ["production"],
        "source_required_params": {"date": "20260425"},
        "source_filters": {"process_name": ["D/A1"]}
      }
    }
  }
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "route": "followup_transform",
    "source_results": [
      {
        "success": true,
        "tool_name": "current_data",
        "dataset_key": "production",
        "data": [
          {"MODE": "DDR5", "production": 2940}
        ],
        "reused_current_data": true
      }
    ],
    "current_datasets": {
      "production": {
        "row_count": 2,
        "columns": ["MODE", "production"]
      }
    }
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_rows_columns` | `[{"MODE": "DDR5"}]` | `["MODE"]` | current data의 컬럼 요약을 만들기 위해 사용합니다. |
| `_build_current_datasets` | source_results | dataset별 요약 | pandas prompt가 dataset별 schema를 볼 수 있게 합니다. |
| `_source_result_from_current_data` | `current_data` | source result | 기존 데이터를 조회 결과와 같은 형태로 맞춥니다. |
| `retrieve_current_data` | follow-up intent plan | retrieval payload | 후속 분석용 retrieval payload를 만듭니다. |
| `build_payload` | Langflow 입력값 | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
followup_transform branch 입력
-> skipped이면 빈 retrieval_payload 반환
-> state.current_data 확인
-> current_data를 source_result로 변환
-> current_datasets 요약 생성
-> Retrieval Payload Merger로 전달
```

## 함수 코드 단위 해석: `retrieve_current_data`

### 핵심 코드 해석

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
```

Router에서 넘어온 payload에서 intent plan과 state를 꺼냅니다.

```python
if payload.get("skipped"):
    return {"retrieval_payload": {"skipped": True, ...}}
```

선택되지 않은 branch라면 아무 작업도 하지 않고 skipped payload를 반환합니다.

```python
current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
source_results = [_source_result_from_current_data(current_data)] if current_data else []
```

이전 state에 current_data가 있으면 source_result 형태로 변환합니다.

```python
"used_current_data": True
```

이 payload가 새 조회 결과가 아니라 기존 데이터를 재사용한 결과임을 표시합니다.

## 추가 함수 코드 단위 해석: `_source_result_from_current_data`

이 함수는 `state.current_data`를 retriever가 만든 `source_result`처럼 보이도록 바꿉니다.

```python
rows = [row for row in current_data.get("data", []) if isinstance(row, dict)] if isinstance(current_data.get("data"), list) else []
```

현재 데이터 안에서 dict row만 추려냅니다.

```python
dataset_keys = current_data.get("source_dataset_keys") if isinstance(current_data.get("source_dataset_keys"), list) else []
```

이전 조회가 어떤 dataset에서 왔는지 확인합니다.

```python
"dataset_key": dataset_keys[0] if dataset_keys else current_data.get("dataset_key", "current_data"),
```

source dataset key가 있으면 첫 번째 값을 사용하고, 없으면 `current_data`로 표시합니다.

```python
"applied_params": deepcopy(current_data.get("source_required_params", current_data.get("retrieval_applied_params", {}))),
"applied_filters": deepcopy(current_data.get("source_filters", {})),
"applied_column_filters": deepcopy(current_data.get("source_column_filters", {})),
```

이전 조회에 적용된 조건을 source result에도 보존합니다. 후속 분석에서 필터 범위를 판단하는 근거가 됩니다.

```python
if isinstance(current_data.get("data_ref"), dict):
    result["data_ref"] = deepcopy(current_data["data_ref"])
    result["data_is_reference"] = True
```

현재 데이터가 MongoDB reference 형태라면 ref 정보도 함께 넘깁니다. 뒤에서 MongoDB Data Loader가 실제 rows를 다시 채울 수 있습니다.

## 추가 함수 코드 단위 해석: `_build_current_datasets`

```python
for result in source_results:
    dataset_key = str(result.get("dataset_key") or result.get("tool_name") or "current_data")
```

source result별 dataset key를 정합니다.

```python
data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
```

rows가 직접 없고 data_ref만 있는 경우도 고려합니다.

```python
"row_count": result.get("row_count") or data_ref.get("row_count") or len(rows),
"columns": _rows_columns(rows) or data_ref.get("columns", []),
```

현재 데이터의 row 수와 컬럼 목록을 요약합니다. 이 정보는 prompt와 follow-up 판단에서 사용됩니다.
