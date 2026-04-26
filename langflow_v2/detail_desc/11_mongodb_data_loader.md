# 11. MongoDB Data Loader

## 한 줄 역할

`data_ref`만 남아 있는 payload에서 MongoDB에 저장된 실제 row list를 다시 불러오는 노드입니다.

## 왜 필요한가

큰 데이터 전체를 Langflow state에 계속 들고 있으면 토큰과 메모리를 많이 씁니다.
그래서 `MongoDB Data Store`가 큰 row list를 MongoDB에 저장하고 state에는 주소만 남길 수 있습니다.

후속 질문에서 실제 row가 다시 필요하면 이 노드가 그 주소를 따라가 row를 복원합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `payload` | `data_ref`가 포함된 payload입니다. 보통 follow-up branch에서 들어옵니다. |
| `mongo_uri` | row 저장소 MongoDB URI입니다. |
| `db_name` | database 이름입니다. |
| `collection_name` | row data ref collection 이름입니다. |
| `enabled` | `true`이면 로드하고, `false`이면 통과시킵니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `loaded_payload` | data_ref가 실제 data row로 복원된 payload입니다. |

## 주요 함수 설명

- `_connect_collection`: MongoDB collection에 연결합니다.
- `_load_rows`: data_ref에 있는 `ref_id`로 저장된 row를 찾습니다.
- `_hydrate_refs`: payload 안을 재귀적으로 돌며 data_ref를 실제 row로 바꿉니다.
- `load_payload_from_mongo`: 전체 로딩 작업을 실행합니다.

## 초보자 포인트

이 노드는 모든 질문에서 꼭 필요하지는 않습니다.

`MongoDB Data Store`를 사용해서 큰 데이터를 ref로 저장하는 구조를 쓸 때, 후속 분석 branch 앞에 연결합니다.

## 연결

```text
Intent Route Router.followup_transform
-> MongoDB Data Loader (Follow-up).payload

MongoDB Data Loader.loaded_payload
-> Current Data Retriever.intent_plan
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "payload": {
    "intent_plan": {
      "state": {
        "current_data": {
          "rows": [],
          "data_ref": {
            "db_name": "datagov",
            "collection_name": "langflow_v2_data_store",
            "document_id": "abc123"
          }
        }
      }
    }
  },
  "mongo_uri": "mongodb://localhost:27017",
  "enabled": "true"
}
```

### 출력 예시

```json
{
  "loaded_payload": {
    "intent_plan": {
      "state": {
        "current_data": {
          "rows": [
            {"MODE": "A", "production": 10}
          ],
          "data_ref": {
            "document_id": "abc123"
          }
        }
      }
    }
  },
  "loaded_refs": [
    {
      "path": "intent_plan.state.current_data",
      "row_count": 1
    }
  ],
  "errors": []
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_truthy` | `"true"` | `true` | Langflow 입력값은 문자열이 많으므로 enabled 같은 옵션을 bool로 바꿉니다. |
| `_connect_collection` | mongo uri/db/collection | collection 객체 | MongoDB collection에 연결합니다. |
| `_load_rows` | `{"document_id": "abc123"}` | row list | 저장된 큰 데이터 document에서 rows를 읽습니다. |
| `_hydrate_refs` | payload 전체 | data_ref 위치가 rows로 채워진 payload | 중첩된 dict/list 안의 `data_ref`를 찾아 실제 rows로 복원합니다. |
| `load_payload_from_mongo` | payload, Mongo 설정 | loaded payload | follow-up 분석 전에 compact payload를 실제 데이터 포함 payload로 바꿉니다. |
| `build_payload` | Langflow 입력값 | `Data(data=loaded_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
payload 입력
-> enabled 확인
-> MongoDB collection 연결
-> payload 내부 data_ref 탐색
-> 각 ref의 rows 로드
-> 원래 payload 위치에 rows 삽입
```

### 초보자 포인트

이 노드는 큰 데이터를 "저장"하지 않고 "다시 불러오는" 노드입니다. 후속 질문에서 `current_data`가 reference만 가지고 있을 때 pandas 분석이 가능하도록 원본 row를 복원합니다.

## 함수 코드 단위 해석: `_hydrate_refs`

이 함수는 payload 안을 재귀적으로 돌면서 `data_ref`를 찾아 실제 rows로 바꿉니다.

### 함수 input

```json
{
  "value": {
    "current_data": {
      "data_ref": {"document_id": "abc123"},
      "data": []
    }
  },
  "path": "root"
}
```

### 함수 output

```json
{
  "current_data": {
    "data_ref": {"document_id": "abc123"},
    "data": [
      {"MODE": "A", "production": 10}
    ]
  }
}
```

### 핵심 코드 해석

```python
if isinstance(value, dict):
```

현재 검사 중인 값이 dict인지 확인합니다. `current_data`, `analysis_result` 같은 payload는 대부분 dict입니다.

```python
data_ref = value.get("data_ref") or value.get("final_rows_ref")
```

이 dict 안에 MongoDB reference가 있는지 찾습니다. 저장 노드가 `data_ref` 또는 `final_rows_ref` 같은 key로 주소를 남겼기 때문입니다.

```python
if isinstance(data_ref, dict):
    rows = _load_rows(collection, data_ref)
```

reference가 dict이면 MongoDB에서 실제 rows를 불러옵니다.

```python
hydrated = deepcopy(value)
hydrated["data"] = rows
```

원본 payload를 직접 고치지 않고 복사본을 만든 뒤 `data`에 rows를 채웁니다.

```python
for key, item in value.items():
    hydrated[key] = _hydrate_refs(item, collection, loaded, f"{path}.{key}")
```

dict 안에 또 다른 dict/list가 있을 수 있으므로 재귀적으로 계속 탐색합니다. `path`는 디버깅할 때 어느 위치에서 ref를 찾았는지 기록하기 위한 문자열입니다.
