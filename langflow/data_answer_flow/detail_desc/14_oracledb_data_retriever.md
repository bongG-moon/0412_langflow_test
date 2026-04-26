# 14. OracleDB Data Retriever

`Retrieval Plan Builder`가 만든 tool 실행 계획을 `oracledb`로 수행하는 노드다.

## 입력

```text
retrieval_plan
main_context
domain_payload
table_catalog_payload
db_connections_json
agent_state
fetch_limit
```

권장 입력은 `retrieval_plan`, `table_catalog_payload`, `db_connections_json`이다. `main_context`는 보통 `retrieval_plan` payload 안에 같이 전달된다. `domain_payload`, `agent_state`는 legacy/advanced 입력이다.

## 출력

```text
retrieval_result
```

## 핵심 원칙

이 노드는 LLM, domain item, table catalog에서 SQL 문자열을 받아 실행하지 않는다.

SQL은 아래 각 tool 함수 내부에 직접 작성한다. Table catalog는 SQL이 아니라 `db_key`, `table_name`, `required_params`, `format_params`, `columns` 같은 metadata를 제공한다.

```text
get_production_data
get_target_data
get_schedule_data
get_capa_data
get_defect_rate
get_equipment_status
get_wip_status
get_yield_data
get_hold_lot_data
get_scrap_data
get_recipe_condition_data
get_lot_trace_data
```

실제 운영 DB에 맞게 수정해야 하는 부분은 각 `get_*` 함수 안의 SQL이다. Dataset별 DB 연결 선택은 table catalog의 `db_key`가 있으면 우선 사용하고, 없으면 domain/source fallback과 함수 기본값을 사용한다.

## SQL 작성 방식

```python
def get_production_data(db_connector, domain, table_catalog, params, fetch_limit):
    sql = """
        SELECT WORK_DT, OPER_NAME, QTY AS production
          FROM PROD_TABLE
         WHERE WORK_DT = {0}
    """
    return _execute_sql_dataset(
        "get_production_data",
        "production",
        _resolve_db_key(domain, table_catalog, "production", "MES"),
        sql,
        db_connector,
        params,
        fetch_limit,
        ["date"],
        ["date"],
        {"date": _normalize_yyyymmdd},
    )
```

SQL placeholder는 Oracle bind variable `:date`가 아니라 Python format slot `{0}`, `{1}`을 사용한다. 값은 `_sql_literal`을 거쳐 SQL literal로 들어가며, `date`는 `2026-04-22` 또는 `20260422` 입력을 `'20260422'` 형태로 변환한다.

실행 가능한 SQL은 주석/공백 제거 후 `SELECT` 또는 `WITH`로 시작해야 한다.

## TNS 연결 JSON

```json
{
  "MES": {
    "id": "MES_USER",
    "pw": "MES_PASSWORD",
    "tns": "MES_TNS_ALIAS"
  },
  "PLAN": {
    "id": "PLAN_USER",
    "pw": "PLAN_PASSWORD",
    "tns": "PLAN_TNS_ALIAS"
  },
  "QMS": {
    "id": "QMS_USER",
    "pw": "QMS_PASSWORD",
    "tns": "QMS_TNS_ALIAS"
  },
  "default": {
    "id": "DEFAULT_USER",
    "pw": "DEFAULT_PASSWORD",
    "tns": "DEFAULT_TNS_ALIAS"
  }
}
```

입력 필드는 `dsn`, `tns`, `tns_name`, `tns_alias`, `tns_info` 중 하나를 사용할 수 있다.

내부 호출은 아래 형태다.

```python
oracledb.connect(user=user, password=password, dsn=tns)
```

Thin mode 연결만 사용하므로 `tns_admin`, `client_lib_dir` 입력은 없다.

## DB 선택 방식

기본 db_key는 각 tool 함수의 fallback 값에 들어 있다.

예시:

```text
production -> MES
target -> PLAN
defect -> QMS
```

table catalog dataset item에 `db_key`가 있으면 그 값을 우선 사용한다. 없으면 domain dataset item의 `db_key`, `source.db_key`, `oracle.db_key`를 확인하고, 그래도 없으면 tool 함수 fallback 값을 사용한다. 단, SQL은 table catalog나 domain에서 가져오지 않는다.

## 연결

```text
Retrieval Plan Builder.retrieval_plan
-> OracleDB Data Retriever.retrieval_plan

Table Catalog Loader.table_catalog_payload
-> OracleDB Data Retriever.table_catalog_payload

OracleDB Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

Oracle 조회가 실패해도 노드는 죽지 않고 dataset별 실패 결과를 `source_results`에 담아 반환한다. 그래서 뒤 노드에서 실패 이유를 사용자에게 설명할 수 있다.
