# 03. Table Catalog JSON Input

테이블 조회 메타데이터를 입력하는 helper input 노드다.

## 입력

```text
table_catalog_json
```

Langflow 화면에서는 일반 `MultilineInput`처럼 보인다. 여기에 테이블 카탈로그 내용을 붙여넣는다.

## 출력

```text
table_catalog_json_payload
```

출력은 다음 노드가 읽을 수 있도록 입력 문자열을 `Data(data={...})`로 감싼다.

```json
{
  "table_catalog_json": "사용자가 붙여넣은 전체 텍스트"
}
```

## 역할

도메인 지식과 테이블 실행 정보를 분리하기 위한 입력 노드다.

도메인에는 제품, 공정, 용어, metric 수식 같은 업무 의미를 넣고, table catalog에는 실제 조회 계획과 분석에 필요한 dataset, tool name, source type, DB key, table name, required parameter, format parameter, column 정보를 넣는다.

## 입력 작성 방식

현재 table catalog에는 SQL을 저장하지 않는다. SQL은 `OracleDB Data Retriever`의 `get_production_data`, `get_target_data` 같은 tool 함수 내부에서 작성한다.

권장 방식:

```json
{
  "datasets": {
    "production": {
      "display_name": "생산 데이터",
      "tool_name": "get_production_data",
      "source_type": "oracle",
      "db_key": "MES",
      "table_name": "PROD_TABLE",
      "required_params": ["date"],
      "format_params": ["date"],
      "columns": [
        {"name": "WORK_DT", "type": "date"},
        {"name": "OPER_NAME", "type": "string"},
        {"name": "production", "type": "number"}
      ]
    }
  }
}
```

`format_params`는 retriever 함수 내부 SQL의 `{0}`, `{1}` slot에 어떤 parameter를 순서대로 넣을지 설명하는 metadata다. 신규 입력에서는 `bind_params` 대신 `format_params`를 사용한다.

## 주의

legacy table catalog에 `sql_template`, `query_template`, `sql`, `oracle_sql` 같은 SQL 필드가 남아 있어도 loader는 호환을 위해 파싱한 뒤 해당 필드를 제거한다. 신규 문서와 Streamlit 등록 web에서는 SQL 필드를 만들지 않는다.
