# 04. Table Catalog Loader

`Table Catalog JSON Input`에서 받은 테이블 카탈로그 텍스트를 파싱하고, main flow에서 쓰기 좋은 구조로 정리하는 노드다.

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

`table_catalog`는 조회 실행용 전체 정보다.

- `required_params`
- `tool_name`
- `source_type`
- `db_key`
- `table_name`
- `sql_template`
- `bind_params`
- `columns`

`table_catalog_prompt_context`는 LLM prompt에 넣을 가벼운 요약 정보다.

- dataset key
- display name
- description
- keywords
- question_examples
- required_params
- 주요 columns

LLM prompt에는 실제 SQL, table name, db_key를 넣지 않는다. 이 정보는 토큰을 많이 쓰고 보안상 민감할 수 있으므로 조회 실행 노드만 `table_catalog`에서 사용한다.

## 어떤 질문에 어떤 데이터가 필요한지

두 종류의 정보가 함께 사용된다.

1. `table_catalog.datasets[].keywords`, `question_examples`
   - “생산량”, “목표량”, “LOT 추적” 같은 질문 표현이 어떤 dataset 후보와 연결되는지 알려준다.
2. domain의 `metrics[].required_datasets`
   - “생산 달성율 = 생산량 / 목표량”처럼 여러 dataset이 필요한 metric 관계를 알려준다.

예를 들어 “오늘 생산 달성율 알려줘”라는 질문에서는 domain metric이 `production`, `target`이 필요하다고 알려주고, table catalog가 각 dataset의 `tool_name`, `required_params`, `sql_template`을 제공한다.

## SQL 입력 형태

권장 방식은 SQL을 그대로 붙여넣는 block 방식이다.

```text
{
  "datasets": {
    "production": {
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
"""
    }
  }
}
```

지원되는 SQL key는 다음과 같다.

- `sql_template`
- `query_template`
- `sql`
- `sql_text`
- `query`
- `oracle_sql`

기존 방식도 계속 지원한다.

```json
{
  "sql_template_lines": [
    "SELECT WORK_DT, OPER_NAME,",
    "       QTY AS production",
    "  FROM PROD_TABLE",
    " WHERE WORK_DT = :date"
  ]
}
```

다만 운영자가 SQL을 그대로 붙여넣는 상황에서는 block 방식이 더 편하다.
