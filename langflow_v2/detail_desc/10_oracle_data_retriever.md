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

