# 11. Oracle Data Retriever

## 이 노드 역할

`Normalize Intent Plan`이 만든 retrieval job을 실제 Oracle 조회 함수로 실행하고, 결과를 `retrieval_payload`로 반환하는 노드입니다.

## 왜 필요한가

Intent plan은 "무엇을 조회할지"만 정합니다. 실제 DB 연결, SQL 실행, fetch limit 적용, DB 설정 오류 처리는 별도의 실행 노드가 담당해야 합니다.

이 노드는 table catalog의 `tool_name`에 맞는 내부 조회 함수를 찾아 실행합니다. 예를 들어 `get_production_data`, `get_target_data`, `get_wip_status` 같은 함수가 실제 SQL을 가지고 있습니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.single_retrieval` 또는 `multi_retrieval` 출력입니다. |
| `db_config` | Oracle 연결 설정 JSON입니다. `db_key`별 DSN, user, password를 넣습니다. |
| `fetch_limit` | SQL 조회 최대 row 수입니다. 기본값은 `5000`입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | Oracle 조회 결과, `source_results`, `current_datasets`, `source_snapshots`를 담은 payload입니다. |

## 주요 함수 설명

- `parse_jsonish`: DB 설정 JSON 또는 JSON-like 문자열을 파싱합니다.
- `_db_config_from_value`: Langflow 입력값에서 DB config dict를 꺼냅니다.
- `_normalize_yyyymmdd`: 날짜 값을 `YYYYMMDD`로 정규화합니다.
- `_sql_literal`: SQL 문자열에 넣을 값을 안전한 literal 형태로 바꿉니다.
- `DBConnector`: Oracle client 연결과 SQL 실행을 담당합니다.
- `get_production_data`: 생산 실적 SQL을 실행합니다.
- `get_target_data`: 생산 목표 SQL을 실행합니다.
- `get_wip_status`: 재공 SQL을 실행합니다.
- `_missing_required_params`: job에 필요한 필수 파라미터가 빠졌는지 확인합니다.
- `_run_job`: retrieval job 하나를 실제 tool 함수 실행으로 바꿉니다.
- `retrieve_oracle_data`: 여러 job을 실행하고 `retrieval_payload`를 만듭니다.

## DB config 예시

```json
{
  "PKG_RPT": {
    "user": "USER_ID",
    "password": "PASSWORD",
    "dsn": "HOST:1521/SERVICE"
  }
}
```

`db_key`는 retrieval job의 `db_key`와 맞아야 합니다. 기본값은 `PKG_RPT`입니다.

## 초보자 확인용

Oracle retriever는 "어떤 데이터를 조회할지 판단"하지 않습니다. 그 판단은 `08 Normalize Intent Plan`이 이미 끝냈습니다.

이 노드는 `retrieval_jobs`를 보고 다음만 수행합니다.

- 어떤 tool 함수를 실행할지 선택
- 필수 파라미터가 있는지 확인
- DB config가 있는지 확인
- SQL 실행
- 결과를 공통 schema로 감싸기

## 연결

```text
Intent Route Router.single_retrieval
-> Oracle Data Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Oracle Data Retriever (Multi).intent_plan

Oracle Data Retriever.retrieval_payload
-> Retrieval Payload Merger.single_retrieval 또는 multi_retrieval
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "intent_plan": {
    "route": "single_retrieval",
    "retrieval_jobs": [
      {
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "db_key": "PKG_RPT",
        "required_params": ["date"],
        "params": {"date": "20260425"},
        "filters": {"process_name": ["D/A1"], "mode": ["DDR5"]},
        "column_filters": {}
      }
    ]
  },
  "db_config": {
    "PKG_RPT": {
      "user": "USER_ID",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  },
  "fetch_limit": "5000"
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "route": "single_retrieval",
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "data": [
          {"WORK_DT": "20260425", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 2940}
        ],
        "summary": "Oracle production query complete: 1 rows",
        "from_oracle": true
      }
    ],
    "current_datasets": {},
    "source_snapshots": [],
    "used_oracle_data": true
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_db_config_from_value` | JSON 문자열 또는 dict | `(config, errors)` | DB 설정 입력이 다양한 형태로 들어와도 dict로 맞춥니다. |
| `_normalize_yyyymmdd` | `"2026-04-25"` | `"20260425"` | SQL의 날짜 조건에 사용할 표준 날짜 형식으로 바꿉니다. |
| `DBConnector.execute_query` | db_key, SQL, limit | row dict list | Oracle 연결을 열고 SQL 결과를 dict list로 바꿉니다. |
| `_missing_required_params` | params, `["date"]` | 누락 목록 | 필수 조건이 없으면 DB 조회 전에 멈춥니다. |
| `_run_job` | retrieval job | source result | tool_name에 맞는 SQL 함수를 실행합니다. |
| `retrieve_oracle_data` | routed intent plan | retrieval payload | 여러 job을 실행하고 조회 결과 payload를 만듭니다. |
| `build_payload` | Langflow 입력값 | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
Intent Route Router에서 active branch 수신
-> skipped이면 빈 retrieval_payload 반환
-> finish route면 early_result 형태로 반환
-> followup_transform이면 current_data를 source_result처럼 감싸 반환
-> db_config 파싱
-> retrieval_jobs 반복
-> job.tool_name에 맞는 get_xxx_data 함수 실행
-> source_results, current_datasets, source_snapshots 생성
-> Retrieval Payload Merger로 전달
```

## 함수 코드 단위 해석: `_run_job`

이 함수는 retrieval job 하나를 실제 Oracle 조회 결과 하나로 바꿉니다.

### 함수 input

```json
{
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "db_key": "PKG_RPT",
  "required_params": ["date"],
  "params": {"date": "20260425"},
  "filters": {"process_name": ["D/A1"]},
  "column_filters": {}
}
```

### 함수 output

```json
{
  "success": true,
  "tool_name": "get_production_data",
  "dataset_key": "production",
  "data": [],
  "summary": "Oracle production query complete: 0 rows",
  "applied_filters": {"process_name": ["D/A1"]}
}
```

### 핵심 코드 해석

```python
tool_name = str(job.get("tool_name") or job.get("dataset_key") or "")
tool = TOOL_REGISTRY.get(tool_name) or TOOL_REGISTRY.get(str(job.get("dataset_key") or ""))
```

job의 `tool_name`으로 실행할 함수를 찾습니다. 없으면 dataset key로 한 번 더 찾습니다.

```python
missing = _missing_required_params(params, job.get("required_params", []))
if missing:
    return _error_result(job, f"Missing required parameter(s): {', '.join(missing)}", "missing_required_params")
```

`date` 같은 필수 조건이 없으면 SQL을 실행하지 않고 오류 result를 반환합니다.

```python
params.update({key: value for key, value in (job.get("filters") or {}).items() if value not in (None, "", [])})
params.update({key: value for key, value in (job.get("column_filters") or {}).items() if value not in (None, "", [])})
```

required params와 filters, column_filters를 하나의 params로 합칩니다. SQL 함수는 이 params를 보고 조건을 구성합니다.

```python
result = tool(params, connector=connector, db_key=str(job.get("db_key") or "PKG_RPT"), fetch_limit=fetch_limit)
```

실제 SQL 함수가 실행됩니다. SQL은 table catalog가 아니라 이 tool 함수 안에 있습니다.

```python
result["applied_filters"] = deepcopy(job.get("filters", {}))
result["applied_column_filters"] = deepcopy(job.get("column_filters", {}))
result["filter_plan"] = deepcopy(job.get("filter_plan", []))
```

후속 질문에서 조건 상속과 scope 판단을 할 수 있도록 적용된 필터 정보를 결과에 보존합니다.
