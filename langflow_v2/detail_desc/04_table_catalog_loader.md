# 04. Table Catalog Loader

## 한 줄 역할

사용 가능한 dataset과 tool 정보를 담은 Table Catalog JSON을 읽는 노드입니다.

## Table Catalog란?

도메인이 "질문을 이해하는 사전"이라면, Table Catalog는 "어떤 데이터를 어떻게 조회할 수 있는지 알려주는 목록"입니다.

예를 들면 다음을 담습니다.

- dataset key: `production`, `target`, `wip`
- tool name: `get_production_data`
- source type: `dummy`, `oracle`
- 필수 파라미터: `date`
- 컬럼 정보: `WORK_DT`, `MODE`, `production`

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `table_catalog_json` | dataset metadata JSON입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `table_catalog_payload` | 정규화된 table catalog 정보입니다. |

## 주요 함수 설명

- `_parse_jsonish`: JSON 문자열을 dict로 바꿉니다.
- `_default_catalog`: 예시용 기본 catalog를 제공합니다.
- `load_table_catalog`: 입력 JSON을 읽고 뒤 노드에서 쓸 수 있게 감쌉니다.

## 예시

```json
{
  "datasets": {
    "production": {
      "display_name": "Production",
      "tool_name": "get_production_data",
      "source_type": "oracle",
      "db_key": "PKG_RPT",
      "required_params": ["date"],
      "format_params": ["date"]
    }
  }
}
```

## 초보자 포인트

SQL은 Table Catalog에 넣지 않습니다.
SQL은 `Oracle Data Retriever` 안의 각 데이터 함수에 둡니다.

Table Catalog는 "어떤 dataset이 있고 어떤 tool을 호출해야 하는가"를 알려주는 역할입니다.

## 연결

```text
Table Catalog Loader.table_catalog_payload
-> Build Intent Prompt.table_catalog_payload
```

