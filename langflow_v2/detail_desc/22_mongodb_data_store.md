# 22. MongoDB Data Store

## 이 노드 역할

큰 row list를 MongoDB에 저장하고, flow payload 안에는 미리보기 row와 `data_ref`만 남기는 노드입니다.

데이터가 많을 때 Langflow payload가 너무 커지는 문제를 줄이고, 최종 결과에는 참조 정보만 보존할 수 있게 합니다.

## 왜 필요한가

제조 데이터는 조회 결과가 수백 건, 수천 건으로 커질 수 있습니다. 모든 row를 매 노드 payload에 계속 싣고 다니면 Langflow 화면과 LLM prompt가 무거워집니다.

이 노드는 row list를 MongoDB에 저장한 뒤 `ref_id`, `row_count`, `columns`, `path` 같은 참조 정보를 남깁니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `payload` | 보통 `Analysis Result Merger.analysis_result`가 들어옵니다. |
| `mongo_uri` | row data reference를 저장할 MongoDB URI입니다. |
| `db_name` | 저장할 database 이름입니다. 기본값은 `datagov`입니다. |
| `collection_name` | 저장할 collection 이름입니다. 기본값은 `manufacturing_agent_data_refs`입니다. |
| `enabled` | 저장 기능 사용 여부입니다. |
| `preview_row_limit` | payload에 남길 미리보기 row 수입니다. |
| `min_rows` | 몇 건 이상일 때 MongoDB로 저장할지 결정합니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `stored_payload` | 원본 payload에 `mongo_data_refs`, `mongo_data_store`, `data_ref`가 추가된 결과입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_find_session_id` | payload 내부에서 session id를 찾습니다. |
| `_connect_collection` | MongoDB collection에 연결합니다. |
| `_store_rows` | row list를 MongoDB document로 저장하고 ref 정보를 반환합니다. |
| `_compact_with_refs` | payload를 재귀적으로 돌며 큰 `data` list를 `data_ref`로 바꿉니다. |
| `store_payload_in_mongo` | 전체 저장 흐름을 제어합니다. |

## 초보자 확인용

이 노드는 LLM과 직접 관련이 없습니다. 데이터가 커졌을 때 payload를 가볍게 만들기 위한 저장 보조 노드입니다.

Mongo URI가 비어 있거나 저장 중 오류가 나도 원본 payload는 최대한 유지하고, 오류는 `mongo_data_store.errors`에 남깁니다.

## 연결

```text
Analysis Result Merger.analysis_result
-> MongoDB Data Store.payload

MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "analysis_result": {
    "success": true,
    "state": {"session_id": "demo-session"},
    "data": [
      {"MODE": "DDR5", "production": 100},
      {"MODE": "DDR5", "production": 120}
    ]
  }
}
```

### 출력 예시

```json
{
  "analysis_result": {
    "success": true,
    "data": [
      {"MODE": "DDR5", "production": 100}
    ],
    "data_ref": {
      "store": "mongodb",
      "ref_id": "abc123",
      "row_count": 2,
      "columns": ["MODE", "production"],
      "path": "analysis_result.data"
    },
    "data_is_reference": true,
    "data_is_preview": true,
    "row_count": 2
  },
  "mongo_data_store": {
    "enabled": true,
    "stored": true,
    "ref_count": 1,
    "errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_is_row_list` | `[{"a": 1}]` | `true` | dict row 목록인지 확인합니다. |
| `_store_rows` | rows, session_id, path | data_ref | MongoDB에 rows를 저장합니다. |
| `_compact_with_refs` | payload | compacted payload | 큰 data list를 preview와 ref로 치환합니다. |
| `store_payload_in_mongo` | payload, mongo 설정 | stored payload | 저장 활성화, 오류 처리, 결과 metadata를 관리합니다. |

### 코드 흐름

```text
payload 입력
-> enabled 확인
-> MongoDB 연결
-> session_id 탐색
-> payload 안의 data row list 탐색
-> MongoDB 저장 후 data_ref 생성
-> preview row만 payload에 남김
```

## 함수 코드 단위 해석: `_compact_with_refs`

### 함수 input

```json
{
  "analysis_result": {
    "data": [
      {"MODE": "DDR5", "production": 100},
      {"MODE": "DDR5", "production": 120}
    ]
  }
}
```

### 함수 output

```json
{
  "analysis_result": {
    "data": [
      {"MODE": "DDR5", "production": 100}
    ],
    "data_ref": {
      "store": "mongodb",
      "row_count": 2,
      "path": "analysis_result.data"
    },
    "data_is_reference": true,
    "data_is_preview": true
  }
}
```

### 핵심 코드 해석

```python
if isinstance(value, dict):
    result = {}
```

payload가 dict이면 내부 key를 하나씩 재귀적으로 확인합니다.

```python
if key == "data" and not already_ref and _is_row_list(item) and len(item) >= min_rows:
```

`data` key이고, 아직 ref가 없고, row list이며, 저장 기준 row 수 이상이면 저장 대상으로 판단합니다.

```python
data_ref = _store_rows(collection, item, session_id, current_path, db_name, collection_name)
```

MongoDB에 실제 rows를 저장하고 참조 정보를 받습니다.

```python
result["data"] = deepcopy(item[:preview_limit])
result["data_ref"] = data_ref
result["data_is_reference"] = True
```

payload에는 preview row와 `data_ref`만 남깁니다.
