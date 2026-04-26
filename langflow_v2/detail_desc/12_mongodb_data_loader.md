# 12. MongoDB Data Loader

## 이 노드 역할

payload 안에 들어 있는 `data_ref`를 보고 MongoDB에서 전체 row를 다시 불러오는 노드입니다.

## 왜 필요한가

큰 조회 결과를 모든 노드 payload에 계속 들고 다니면 Langflow 화면과 API payload가 무거워집니다. 그래서 `22 MongoDB Data Store`는 큰 row list를 MongoDB에 저장하고 payload에는 `data_ref`만 남길 수 있습니다.

이 노드는 나중에 그 `data_ref`를 다시 실제 `data`로 복원합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `payload` | `data_ref`를 포함할 수 있는 payload입니다. |
| `mongo_uri` | MongoDB 연결 문자열입니다. |
| `db_name` | MongoDB database 이름입니다. 기본값은 `datagov`입니다. |
| `collection_name` | data ref가 저장된 collection 이름입니다. |
| `enabled` | loader 사용 여부입니다. `false`면 원본 payload를 그대로 반환합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `loaded_payload` | `data_ref`가 실제 `data`로 hydrate된 payload입니다. |

## 주요 함수 설명

- `_truthy`: 문자열 입력을 boolean처럼 해석합니다.
- `_json_safe`: MongoDB에서 읽은 값을 JSON 저장 가능한 값으로 바꿉니다.
- `_connect_collection`: MongoDB client와 collection을 엽니다.
- `_load_rows`: `ref_id`로 저장된 rows를 조회합니다.
- `_hydrate_refs`: payload 전체를 재귀적으로 돌며 `data_ref`를 실제 rows로 바꿉니다.
- `load_payload_from_mongo`: 전체 loader 동작을 수행합니다.
- `build_payload`: Langflow output method입니다.

## 초보자 확인용

이 노드는 새 데이터를 조회하는 노드가 아닙니다. 이미 MongoDB에 저장된 row list를 `data_ref`로 다시 불러오는 노드입니다.

`enabled=false`이거나 `mongo_uri`가 비어 있으면 실제 MongoDB 조회를 하지 않습니다.

## 연결

```text
MongoDB Data Store.stored_payload
-> MongoDB Data Loader.payload

MongoDB Data Loader.loaded_payload
-> 후속 pandas 또는 final 처리 노드
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "payload": {
    "analysis_result": {
      "data_ref": {
        "ref_id": "abc-123",
        "row_count": 1000
      },
      "data": [
        {"preview": true}
      ],
      "data_is_preview": true
    }
  },
  "mongo_uri": "mongodb://localhost:27017",
  "db_name": "datagov",
  "collection_name": "manufacturing_agent_data_refs",
  "enabled": "true"
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "data_ref": {
      "ref_id": "abc-123",
      "row_count": 1000
    },
    "data": [
      {"WORK_DT": "20260425", "MODE": "DDR5", "production": 2940}
    ],
    "row_count": 1000,
    "data_ref_loaded": true,
    "data_is_preview": false
  },
  "mongo_data_load": {
    "enabled": true,
    "loaded": true,
    "ref_count": 1,
    "errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_truthy` | `"false"` | `false` | Langflow text input을 boolean처럼 해석합니다. |
| `_connect_collection` | uri, db, collection | client, collection | MongoDB collection 객체를 엽니다. |
| `_load_rows` | collection, `{"ref_id": "abc"}` | rows | 저장된 row list를 ref_id로 조회합니다. |
| `_hydrate_refs` | payload dict | data가 채워진 payload | payload 어디에 있든 `data_ref`를 찾아 실제 rows로 바꿉니다. |
| `load_payload_from_mongo` | payload, Mongo 설정 | loaded payload | Mongo 로딩 전체를 수행하고 metadata를 붙입니다. |
| `build_payload` | Langflow 입력값 | `Data(data=loaded_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
payload 입력
-> enabled 확인
-> mongo_uri 확인
-> MongoDB collection 연결
-> payload 전체에서 data_ref 재귀 탐색
-> ref_id로 rows 조회
-> data, row_count, data_ref_loaded 설정
-> mongo_data_load metadata 추가
```

## 함수 코드 단위 해석: `_hydrate_refs`

이 함수는 payload 전체를 훑으며 `data_ref`가 있는 dict를 찾아 실제 rows를 채웁니다.

### 함수 input

```json
{
  "data_ref": {"ref_id": "abc-123"},
  "data": [{"preview": true}],
  "data_is_preview": true
}
```

### 함수 output

```json
{
  "data_ref": {"ref_id": "abc-123"},
  "data": [{"WORK_DT": "20260425"}],
  "row_count": 1,
  "data_ref_loaded": true,
  "data_is_preview": false
}
```

### 핵심 코드 해석

```python
if isinstance(value, dict):
    result = {}
    for key, item in value.items():
        result[key] = _hydrate_refs(item, collection, loaded, current_path)
```

payload가 dict이면 내부 key를 하나씩 재귀적으로 처리합니다. `data_ref`가 깊은 곳에 있어도 찾기 위한 구조입니다.

```python
data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
if data_ref:
    rows = _load_rows(collection, data_ref)
```

현재 dict에 `data_ref`가 있으면 MongoDB에서 rows를 불러옵니다.

```python
result["data"] = _json_safe(rows)
result["row_count"] = len(rows)
result["data_ref_loaded"] = True
result["data_is_preview"] = False
```

저장된 rows를 실제 `data`로 채우고 preview 상태가 아니라고 표시합니다.
