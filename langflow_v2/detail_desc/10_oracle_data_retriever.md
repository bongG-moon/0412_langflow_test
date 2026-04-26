# 10. Oracle Data Retriever

## 한 줄 역할

intent plan에 들어 있는 retrieval job을 보고 Oracle DB에서 실제 데이터를 조회하는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | single 또는 multi retrieval branch에서 온 조회 계획입니다. |
| `db_config` | Oracle 접속 정보 JSON입니다. triple-quoted DSN도 처리합니다. |
| `fetch_limit` | 최대 조회 row 수입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | Oracle 조회 결과를 source_results와 current_data 형태로 담습니다. |

## db_config 예시

```json
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=svc)))"
  }
}
```

DSN이 길면 다음처럼 triple quote도 가능합니다.

```python
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": """(DESCRIPTION=
      (ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))
      (CONNECT_DATA=(SERVICE_NAME=svc))
    )"""
  }
}
```

## 주요 함수 설명

- `_normalize_triple_quoted_json`: `""" ... """` 안의 DSN을 JSON 문자열로 바꿉니다.
- `parse_jsonish`: JSON 또는 Python dict처럼 보이는 입력을 안전하게 파싱합니다.
- `DBConnector`: Oracle 연결과 SQL 실행을 담당하는 작은 class입니다.
- `_execute_oracle_sql`: SQL 실행 후 row list를 만듭니다.
- `get_production_data`, `get_target_data` 등: dataset별 실제 SQL을 담는 함수입니다.
- `_run_job`: retrieval job을 보고 적절한 dataset 함수를 호출합니다.
- `retrieve_oracle_data`: 전체 job 목록을 실행하고 결과를 합칩니다.

## 초보자 포인트

이 노드에서 실제 SQL을 관리합니다.
Table Catalog에는 SQL을 넣지 않고, `tool_name`과 `db_key`만 둡니다.

예를 들어 catalog에서 `tool_name`이 `get_production_data`이면 이 파일 안의 같은 이름 함수를 호출합니다.

## 자주 나는 오류

- `DB connections JSON parse failed`: JSON 문법 오류 또는 따옴표 문제입니다.
- `Unknown Target DB`: `db_key`가 `db_config`에 없습니다.
- 필수 조건 부족: job에 `date` 같은 값이 없습니다.

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
    "retrieval_jobs": [
      {
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "params": {
          "date": "20260425",
          "process": "DA"
        },
        "required_params": ["date"]
      }
    ]
  },
  "db_config": {
    "PKG_RPT": {
      "user": "USER",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  },
  "fetch_limit": 5000
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "data": [
          {"WORK_DT": "20260425", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 1200}
        ],
        "summary": "total rows 1, production 1200"
      }
    ],
    "errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_normalize_triple_quoted_json` | `{"dsn": """HOST/SVC"""}` | 파싱 가능한 JSON 문자열 | DSN이나 SQL이 triple quote로 들어와도 JSON 파싱 실패를 줄입니다. |
| `parse_jsonish` | DB config 문자열 | `(dict, errors)` | Langflow 입력창의 DB JSON을 안전하게 dict로 바꿉니다. |
| `_db_config_from_value` | `db_config` 입력 | `(config, errors)` | Oracle 연결에 필요한 user/password/dsn 구조를 검증합니다. |
| `_sql_literal` | `"D/A1"` | `"'D/A1'"` | SQL 문자열에 들어갈 값을 안전하게 따옴표 처리합니다. |
| `DBConnector.get_connection` | `"PKG_RPT"` | Oracle connection | target DB 이름으로 설정을 찾아 `oracledb.connect`를 실행합니다. |
| `DBConnector.execute_query` | target DB, SQL | row dict list | cursor 결과를 `[{컬럼: 값}]` 형태로 바꿉니다. |
| `_execute_oracle_sql` | SQL, connector | source result | SQL 실행 성공/실패를 표준 retrieval 결과로 감쌉니다. |
| `get_production_data` 등 | params, connector | source result | dataset별 SQL을 만들고 실행하는 실제 조회 함수입니다. |
| `_missing_required_params` | params, `["date"]` | 누락 목록 | 필수 날짜 같은 값이 없으면 DB 조회 전에 막습니다. |
| `_run_job` | retrieval job | source result | `tool_name`에 맞는 Oracle 조회 함수를 실행합니다. |
| `retrieve_oracle_data` | intent plan, db_config | retrieval payload | 여러 job을 실행하고 `source_results`로 묶습니다. |

### 코드 흐름

```text
DB config JSON 파싱
-> DBConnector 생성
-> retrieval_jobs 반복
-> 필수 params 확인
-> tool_name별 SQL 생성
-> Oracle execute
-> source_results와 current_data 구성
```

### 초보자 포인트

Oracle 노드는 "어떤 데이터를 조회할지 판단"하지 않습니다. 이미 `07 Normalize Intent Plan`이 만든 `retrieval_jobs`를 보고, 각 job을 실제 SQL 실행으로 바꾸는 역할입니다.

## 함수 코드 단위 해석: `DBConnector.execute_query`

이 함수는 Oracle에 SQL을 실행하고 결과를 `list[dict]` 형태로 바꾸는 함수입니다.

### 함수 input

```json
{
  "target_db": "PKG_RPT",
  "sql": "SELECT WORK_DT, MODE, production FROM AAA_TABLE WHERE WORK_DT = '20260425'",
  "fetch_limit": 5000
}
```

### 함수 output

```json
[
  {"WORK_DT": "20260425", "MODE": "DDR5", "production": 1200},
  {"WORK_DT": "20260425", "MODE": "LPDDR5", "production": 900}
]
```

### 핵심 코드 해석

```python
conn = self.get_connection(target_db)
cursor = conn.cursor()
```

`target_db` 이름으로 DB 설정을 찾고 Oracle connection을 엽니다. 그 다음 SQL 실행을 위한 cursor를 만듭니다.

```python
cursor.execute(sql)
```

실제 SQL이 Oracle DB로 전송되는 부분입니다.

```python
columns = [col[0] for col in cursor.description]
```

Oracle cursor의 description에는 조회 결과 컬럼 정보가 들어 있습니다. 여기서 컬럼명만 뽑습니다.

예:

```json
["WORK_DT", "MODE", "production"]
```

```python
rows = cursor.fetchmany(fetch_limit) if fetch_limit else cursor.fetchall()
```

`fetch_limit`이 있으면 최대 그 건수만 가져옵니다. 없으면 전체를 가져옵니다. 운영에서는 너무 많은 데이터를 한 번에 가져오지 않기 위해 limit을 두는 것이 좋습니다.

```python
return [dict(zip(columns, row)) for row in rows]
```

Oracle cursor row는 보통 tuple처럼 나옵니다.

```python
("20260425", "DDR5", 1200)
```

`zip(columns, row)`를 쓰면 컬럼명과 값을 짝지을 수 있습니다.

```python
{"WORK_DT": "20260425", "MODE": "DDR5", "production": 1200}
```

이렇게 바꾸는 이유는 뒤 Langflow/pandas 노드가 컬럼명으로 값을 읽기 쉽게 하기 위해서입니다.

```python
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
```

성공하든 실패하든 cursor와 connection을 닫습니다. DB 연결을 계속 열어두면 운영 환경에서 connection이 부족해질 수 있습니다.

## 함수 코드 단위 해석: `_run_job`

이 함수는 `retrieval_jobs`의 job 하나를 실제 Oracle 조회 함수로 연결합니다.

### 핵심 흐름

```text
job 입력
-> tool_name 확인
-> 필수 params 누락 확인
-> TOOL_REGISTRY에서 함수 찾기
-> get_production_data 같은 함수 실행
-> source result 반환
```

예를 들어 job이 다음과 같으면:

```json
{
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "params": {"date": "20260425"}
}
```

`TOOL_REGISTRY["get_production_data"]`를 찾아 `get_production_data(params, connector, ...)`를 실행합니다.

이렇게 registry를 쓰는 이유는 if/elif를 길게 쓰지 않고도 `tool_name`으로 함수를 선택할 수 있게 하기 위해서입니다.

## 추가 함수 코드 단위 해석: `_db_config_from_value`

이 함수는 Langflow 입력창에 들어온 DB 설정을 Oracle 연결에 쓸 수 있는 dict로 바꿉니다.

### 함수 input

```json
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": "HOST:1521/SERVICE"
  }
}
```

문자열로 들어오면 다음처럼 들어올 수도 있습니다.

```text
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": """HOST:1521/SERVICE"""
  }
}
```

### 함수 output

```json
[
  {
    "PKG_RPT": {
      "user": "USER",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  },
  []
]
```

두 번째 값은 errors list입니다.

### 핵심 코드 해석

```python
payload, errors = parse_jsonish(value)
```

입력값이 dict인지 JSON 문자열인지 확인하고 파싱합니다. triple quote 문자열도 앞단에서 보정합니다.

```python
if not isinstance(payload, dict):
    return {}, ["DB config must be a JSON object."]
```

DB 설정은 반드시 dict여야 합니다. list나 단순 문자열이면 연결 정보를 찾을 수 없으므로 오류를 반환합니다.

```python
for key, conf in payload.items():
```

`PKG_RPT`, `MES`, `ERP`처럼 target DB 이름별 설정을 하나씩 확인합니다.

```python
if not isinstance(conf, dict):
    errors.append(f"{key} config must be an object.")
    continue
```

각 DB 설정도 dict여야 합니다. 아니면 해당 DB 설정을 건너뜁니다.

```python
cleaned[str(key)] = {
    "user": str(conf.get("user") or ""),
    "password": str(conf.get("password") or ""),
    "dsn": str(conf.get("dsn") or ""),
}
```

Oracle 연결에 필요한 세 값을 문자열로 정리합니다.

- `user`
- `password`
- `dsn`

### 왜 이 함수가 중요한가?

Oracle 연결 오류 중 상당수는 DB config 입력 형식 문제에서 발생합니다. 그래서 이 함수에서 입력을 최대한 유연하게 받아주고, 실패할 때는 어떤 설정이 문제인지 `errors`로 알려줍니다.

## 추가 함수 코드 단위 해석: `retrieve_oracle_data`

이 함수는 Intent Plan의 retrieval jobs를 실제 Oracle 조회 결과로 바꾸는 최상위 함수입니다.

### 함수 input

```json
{
  "intent_plan_value": {
    "intent_plan": {
      "route": "single_retrieval",
      "retrieval_jobs": [
        {
          "dataset_key": "production",
          "tool_name": "get_production_data",
          "params": {"date": "20260425"}
        }
      ]
    }
  },
  "db_config_value": {
    "PKG_RPT": {
      "user": "USER",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  }
}
```

### 함수 output

```json
{
  "retrieval_payload": {
    "route": "single_retrieval",
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "data": []
      }
    ],
    "used_oracle_data": true
  }
}
```

### 핵심 코드 해석

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
```

router에서 넘어온 값에서 실제 intent plan을 꺼냅니다.

```python
db_config, config_errors = _db_config_from_value(db_config_value)
```

Langflow 입력의 DB config를 Oracle connector가 읽을 수 있는 형태로 정리합니다.

```python
if config_errors:
    ...
```

DB config가 잘못되면 Oracle에 접속하기 전에 retrieval 실패 payload를 만들 수 있습니다.

```python
connector = DBConnector(db_config)
```

DB 연결과 SQL 실행을 담당하는 connector 객체를 만듭니다.

```python
jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
source_results = [_run_job(job, connector, fetch_limit) for job in jobs if isinstance(job, dict)]
```

각 retrieval job을 `_run_job`으로 실행합니다. `_run_job` 내부에서 `get_production_data` 같은 SQL 함수가 호출됩니다.

```python
return {
    "retrieval_payload": {
        "route": plan.get("route", "single_retrieval"),
        "source_results": source_results,
        "current_datasets": _build_current_datasets(source_results),
        ...
    }
}
```

Oracle 조회 결과를 dummy retriever와 같은 구조로 반환합니다. 이렇게 해야 뒤 노드들이 데이터 source가 dummy인지 Oracle인지 몰라도 같은 방식으로 처리할 수 있습니다.
