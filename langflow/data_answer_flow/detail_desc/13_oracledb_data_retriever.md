# 13. OracleDB Data Retriever

조회 plan을 받아 `oracledb`로 실제 Oracle SQL을 실행하는 조회 노드다.

## 입력

```text
retrieval_plan
db_connections_json
main_context      optional
domain_payload    legacy optional
agent_state       legacy optional
fetch_limit
tns_admin
client_lib_dir
```

새 구조에서는 `Retrieval Plan Builder.retrieval_plan` 안에 `main_context`가 들어 있으므로 `domain_payload`와 `agent_state`는 직접 연결하지 않아도 된다.

## Oracle TNS 연결 예시

```json
{
  "MES": {
    "id": "MES_USER",
    "pw": "MES_PASSWORD",
    "tns": "MES_TNS_ALIAS"
  },
  "default": {
    "id": "DEFAULT_USER",
    "pw": "DEFAULT_PASSWORD",
    "tns": "DEFAULT_TNS_ALIAS"
  }
}
```

사용자 설정 key는 `tns`, `tns_name`, `tns_alias`, `tns_info` 중 하나를 사용한다. 코드 내부에서 `oracledb.connect(user=..., password=..., dsn=tns)`를 호출하지만, 여기서 `dsn`은 Python 라이브러리 인자명이고 flow 설정은 TNS 기준이다.

## 출력

```text
retrieval_result -> Data
```

## 역할

- retrieval job의 `db_key`로 연결 정보를 선택한다.
- domain dataset의 `query_template` 또는 `sql`을 실행한다.
- job `params`를 SQL bind parameter로 넘긴다.
- 실패한 dataset은 `success=false`, `error_message`를 담아 반환한다.
- Dummy 조회 노드와 같은 output shape를 반환한다.

## 권장 연결

```text
Retrieval Plan Builder.retrieval_plan
-> OracleDB Data Retriever.retrieval_plan

OracleDB Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```
