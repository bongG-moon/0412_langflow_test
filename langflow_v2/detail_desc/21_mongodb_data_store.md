# 21. MongoDB Data Store

## 한 줄 역할

큰 row list를 MongoDB에 저장하고, flow payload에는 작은 preview와 `data_ref`만 남기는 노드입니다.

## 왜 필요한가

조회 결과가 수천 row가 되면 모든 데이터를 LLM prompt나 Langflow state에 계속 들고 있기 어렵습니다.

이 노드를 사용하면 다음처럼 바뀝니다.

```json
{
  "data": [{"preview": "rows"}],
  "data_ref": {
    "store": "mongodb",
    "ref_id": "...",
    "row_count": 1234
  },
  "data_is_reference": true
}
```

즉, 전체 데이터는 MongoDB에 있고 state에는 주소만 남습니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `payload` | row list가 포함된 payload입니다. 보통 Analysis Result Merger 출력입니다. |
| `mongo_uri` | MongoDB URI입니다. |
| `db_name` | database 이름입니다. |
| `collection_name` | row 저장 collection 이름입니다. |
| `enabled` | `true`이면 저장하고, `false`이면 통과시킵니다. |
| `preview_row_limit` | payload에 남길 미리보기 row 수입니다. |
| `min_rows` | 몇 row 이상일 때 MongoDB에 저장할지 정합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `stored_payload` | 큰 row list가 preview + data_ref 형태로 압축된 payload입니다. |

## 주요 함수 설명

- `_is_row_list`: 값이 row list인지 확인합니다.
- `_find_session_id`: payload 안에서 session_id를 찾아 저장 문서에 넣습니다.
- `_store_rows`: MongoDB에 실제 rows를 저장합니다.
- `_compact_with_refs`: payload 안을 돌며 큰 row list를 data_ref로 바꿉니다.
- `store_payload_in_mongo`: 전체 저장과 압축을 실행합니다.

## 초보자 포인트

이 노드는 선택 사항입니다.
처음 테스트할 때는 연결하지 않아도 됩니다.

데이터가 커지고 후속 질문까지 지원하려면 다음 노드와 세트로 사용합니다.

- 저장: `MongoDB Data Store`
- 다시 불러오기: `MongoDB Data Loader`

## 연결

```text
Analysis Result Merger.analysis_result
-> MongoDB Data Store.payload

MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result

MongoDB Data Store.stored_payload
-> Final Answer Builder.analysis_result
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "payload": {
    "analysis_result": {
      "state": {"session_id": "abc"},
      "final_rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    }
  },
  "enabled": "true",
  "preview_row_limit": "1",
  "min_rows": "1"
}
```

### 출력 예시

```json
{
  "stored_payload": {
    "analysis_result": {
      "final_rows": [
        {"MODE": "A", "production": 150}
      ],
      "final_rows_ref": {
        "db_name": "datagov",
        "collection_name": "langflow_v2_data_store",
        "document_id": "abc123",
        "row_count": 2
      }
    }
  },
  "stored_refs": [
    {
      "path": "analysis_result.final_rows",
      "row_count": 2
    }
  ]
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_truthy` | `"false"` | `false` | Langflow 문자열 옵션을 bool로 해석합니다. |
| `_is_row_list` | `[{"A": 1}]` | `true` | 저장 대상이 row list인지 판단합니다. |
| `_find_session_id` | payload 전체 | `"abc"` | 저장 document에 session id를 남기기 위해 payload 안에서 찾습니다. |
| `_store_rows` | collection, rows, path | data_ref dict | 큰 row list를 MongoDB에 저장하고 reference 정보를 만듭니다. |
| `_compact_with_refs` | payload 전체 | preview + ref payload | 중첩된 row list를 찾아 preview만 남기고 원본은 MongoDB ref로 바꿉니다. |
| `store_payload_in_mongo` | payload, Mongo 설정 | stored payload | 큰 데이터를 저장하고 compact payload를 반환합니다. |
| `build_payload` | Langflow input | `Data(data=stored_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
analysis_result 입력
-> enabled/min_rows 확인
-> 큰 row list 탐색
-> MongoDB에 원본 rows 저장
-> payload에는 preview rows와 data_ref만 유지
```

### 초보자 포인트

이 노드는 token 절감용입니다. LLM과 memory에는 전체 데이터를 계속 들고 다니지 않고, 필요한 경우 다시 불러올 수 있는 주소만 남깁니다.

## 함수 코드 단위 해석: `_compact_with_refs`

이 함수는 payload 안의 큰 row list를 MongoDB에 저장하고, payload에는 preview와 reference만 남깁니다.

### 함수 input

```json
{
  "analysis_result": {
    "data": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ]
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "data": [
      {"MODE": "A", "production": 150}
    ],
    "data_ref": {
      "document_id": "abc123",
      "row_count": 2
    },
    "data_is_preview": true
  }
}
```

### 핵심 코드 해석

```python
if _is_row_list(value) and len(value) >= min_rows:
```

현재 값이 row list이고, 저장 기준 건수 이상이면 compact 대상입니다.

```python
data_ref = _store_rows(collection, value, session_id, path, db_name, collection_name)
```

원본 rows를 MongoDB에 저장하고 reference 정보를 받습니다.

```python
preview = value[:preview_limit]
```

화면이나 LLM prompt에 보여줄 preview row만 남깁니다.

```python
refs.append({"path": path, **data_ref})
```

어느 위치의 rows를 저장했는지 기록합니다. 나중에 디버깅할 때 어떤 데이터가 reference로 바뀌었는지 알 수 있습니다.

```python
return {
    "data": preview,
    "data_ref": data_ref,
    "data_is_preview": True,
    ...
}
```

원본 전체 대신 preview와 ref를 가진 dict를 반환합니다.

```python
if isinstance(value, dict):
    return {key: _compact_with_refs(item, ...) for key, item in value.items()}
```

현재 값이 dict라면 내부 값을 하나씩 재귀적으로 검사합니다. 그래서 payload 깊은 곳에 있는 rows도 찾을 수 있습니다.

## 추가 함수 코드 단위 해석: `store_payload_in_mongo`

이 함수는 MongoDB Data Store 노드의 최상위 함수입니다. 저장 기능을 켤지 판단하고, payload를 compact 처리한 뒤 결과를 반환합니다.

### 함수 input

```json
{
  "payload_value": {
    "analysis_result": {
      "state": {"session_id": "abc"},
      "data": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    }
  },
  "enabled_value": "true",
  "preview_row_limit_value": "1",
  "min_rows_value": "1"
}
```

### 함수 output

```json
{
  "stored_payload": {
    "analysis_result": {
      "data": [
        {"MODE": "A", "production": 150}
      ],
      "data_ref": {"document_id": "abc123", "row_count": 2},
      "data_is_preview": true
    }
  },
  "stored_refs": [
    {"path": "analysis_result.data", "row_count": 2}
  ],
  "errors": []
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(payload_value)
```

앞 노드의 analysis result를 dict로 꺼냅니다.

```python
if not _truthy(enabled_value):
    return {"stored_payload": payload, "stored_refs": [], "errors": [], "storage_enabled": False}
```

저장 기능이 꺼져 있으면 아무것도 저장하지 않고 원본 payload를 그대로 반환합니다.

```python
preview_limit = max(0, int(preview_row_limit_value or 20))
min_rows = max(1, int(min_rows_value or 1))
```

preview로 남길 row 수와 저장을 시작할 최소 row 수를 숫자로 바꿉니다.

```python
collection_client, collection = _connect_collection(mongo_uri, db_name, collection_name)
```

MongoDB collection에 연결합니다.

```python
session_id = _find_session_id(payload)
refs: list[Dict[str, Any]] = []
compact_payload = _compact_with_refs(payload, collection, session_id, db_name, collection_name, preview_limit, min_rows, "root", refs)
```

payload 내부를 재귀적으로 훑으며 큰 row list를 MongoDB에 저장하고, payload에는 preview와 ref만 남깁니다.

```python
return {
    "stored_payload": compact_payload,
    "stored_refs": refs,
    "errors": [],
    "storage_enabled": True,
}
```

저장 후 compact payload와 저장된 ref 목록을 반환합니다.

### 왜 이 함수가 중요한가?

이 함수가 없으면 조회 결과 전체가 final prompt와 memory에 계속 들어갈 수 있습니다. 데이터가 커질수록 token 비용, latency, 화면 렌더링 문제가 생기므로 reference 방식이 필요합니다.
