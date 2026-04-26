# 04. Table Catalog Loader

`Table Catalog JSON Input`에서 받은 테이블 카탈로그 텍스트를 파싱하고, retrieval plan과 data retriever에서 쓰기 좋은 metadata 구조로 정리하는 노드다.

## 입력

```text
table_catalog_json_payload
```

보통 아래처럼 연결한다.

```text
Table Catalog JSON Input.table_catalog_json_payload
-> Table Catalog Loader.table_catalog_json_payload
```

## 출력

```text
table_catalog_payload
```

반환 구조는 다음과 같다.

```json
{
  "table_catalog": {
    "catalog_id": "manufacturing_table_catalog",
    "status": "active",
    "datasets": {}
  },
  "table_catalog_prompt_context": {
    "datasets": {}
  },
  "table_catalog_errors": []
}
```

## table_catalog와 table_catalog_prompt_context 차이

`table_catalog`는 조회 계획과 실행 노드가 참고하는 metadata다.

- `required_params`
- `tool_name`
- `source_type`
- `db_key`
- `table_name`
- `format_params`
- `columns`

`table_catalog_prompt_context`는 metadata의 가벼운 요약 정보다. 현재 intent prompt에는 table catalog를 넣지 않고, 후단 retrieval 노드가 `table_catalog`를 직접 사용한다.

- dataset key
- display name
- description
- keywords
- question_examples
- required_params
- 주요 columns

LLM prompt에는 table catalog를 처음부터 싣지 않는다. Table catalog는 토큰 절감을 위해 `Main Flow Context Builder`를 거치지 않고 `Retrieval Plan Builder`와 `OracleDB Data Retriever`에 직접 연결한다.

## 어떤 질문에 어떤 데이터가 필요한지

두 종류의 정보가 함께 사용된다.

1. `table_catalog.datasets[].keywords`, `question_examples`
   - “생산량”, “목표량”, “LOT 추적” 같은 질문 표현이 어떤 dataset 후보와 연결되는지 알려준다.
2. domain의 `metrics[].required_datasets`
   - “생산 달성율 = 생산량 / 목표량”처럼 여러 dataset이 필요한 metric 관계를 알려준다.

예를 들어 “오늘 생산 달성율 알려줘”라는 질문에서는 domain metric이 `production`, `target`이 필요하다고 알려주고, table catalog가 각 dataset의 `tool_name`, `source_type`, `db_key`, `required_params`, `format_params`, `columns`를 제공한다.

## SQL 필드 처리

현재 구조에서는 table catalog에 SQL을 저장하지 않는다. SQL은 Oracle retriever의 각 `get_*` 함수 내부에서 작성한다.

신규 권장 입력:

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

아래 SQL key는 legacy 입력 호환을 위해 읽을 수 있지만 normalize 결과에서는 제거된다.

- `sql_template`
- `query_template`
- `sql`
- `sql_text`
- `query`
- `oracle_sql`

기존 `bind_params`가 들어오면 가능한 경우 `format_params`로 변환해 후단 metadata로 넘긴다. 신규 입력에서는 `format_params`를 직접 사용한다.
