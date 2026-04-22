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

도메인에는 제품, 공정, 용어, metric 수식 같은 업무 의미를 넣고, table catalog에는 실제 조회에 필요한 dataset, tool name, required parameter, DB key, SQL, bind parameter, column 정보를 넣는다.

## SQL 작성 방식

표준 JSON은 줄바꿈이 들어간 문자열을 그대로 지원하지 않는다. 그래서 이 프로젝트의 `Table Catalog Loader`는 SQL 전용 편의 문법을 지원한다.

권장 방식:

```text
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
```

이렇게 쓰면 SQL 안의 작은따옴표와 큰따옴표를 대부분 그대로 둘 수 있다. Loader가 실행 전에 이 블록을 안전한 JSON 문자열로 변환한 뒤 파싱한다.

## 주의

이 입력 문법은 사람이 붙여넣기 편하도록 만든 확장 JSON 형식이다. 엄밀한 `.json` 파일 검증 도구에서는 실패할 수 있지만, Langflow 노드에서는 정상적으로 처리된다.
