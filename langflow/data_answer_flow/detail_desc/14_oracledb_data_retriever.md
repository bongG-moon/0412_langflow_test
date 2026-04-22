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
tns_admin
client_lib_dir
```

권장 입력은 `retrieval_plan`과 `db_connections_json`이다. `domain_payload`, `agent_state`는 legacy/advanced 입력이다.

## 출력

```text
retrieval_result
```

## 핵심 원칙

이 노드는 LLM이나 domain item에서 SQL 문자열을 받아 실행하지 않는다.

SQL은 우선 table catalog의 dataset별 `sql_template`을 사용한다. table catalog가 비어 있거나 해당 dataset이 없을 때만 노드 코드 내부 fallback SQL을 사용한다.

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

실제 운영 DB에 맞게 수정해야 하는 부분은 우선 table catalog JSON이다. 코드 내부 `ORACLE_TOOL_SPECS`는 fallback이다.

## Table Catalog SQL 예시

```text
{
  "sql_template": """
SELECT
    WORK_DT,
    OPER_NAME,
    SUM(QTY) AS production
FROM PROD_TABLE
WHERE WORK_DT = :date
  AND NVL(DELETE_FLAG, 'N') = 'N'
  AND SITE_CODE = "K1"
GROUP BY WORK_DT, OPER_NAME
""",
  "bind_params": {
    "date": "date"
  }
}
```

`Table Catalog Loader`는 `"""..."""` SQL 블록을 실제 `sql_template` 문자열로 변환하고, Oracle 실행 시 이 문자열을 사용한다.

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

입력 필드는 `tns`, `tns_name`, `tns_alias`, `tns_info` 중 하나를 사용할 수 있다.

내부 호출은 아래 형태다.

```python
oracledb.connect(user=user, password=password, dsn=tns)
```

DNS 방식은 사용하지 않는다.

## DB 선택 방식

기본 db_key는 tool spec에 들어 있다.

예시:

```text
production -> MES
target -> PLAN
defect -> QMS
```

domain dataset item에 `db_key`, `source.db_key`, `oracle.db_key`가 있으면 그 값을 우선 사용한다. 단, SQL은 domain에서 가져오지 않는다.

## 연결

```text
Retrieval Plan Builder.retrieval_plan
-> OracleDB Data Retriever.retrieval_plan

OracleDB Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

Oracle 조회가 실패해도 노드는 죽지 않고 dataset별 실패 결과를 `source_results`에 담아 반환한다. 그래서 뒤 노드에서 실패 이유를 사용자에게 설명할 수 있다.
