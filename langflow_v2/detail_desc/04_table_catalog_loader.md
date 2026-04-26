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

## Python 코드 상세 해석

### 입력 예시

```json
{
  "datasets": {
    "production": {
      "display_name": "Production",
      "keywords": ["생산", "생산량", "production"],
      "tool_name": "get_production_data",
      "required_params": ["date"]
    }
  }
}
```

### 출력 예시

```json
{
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {
          "display_name": "Production",
          "keywords": ["생산", "생산량", "production"],
          "tool_name": "get_production_data",
          "required_params": ["date"]
        }
      }
    },
    "table_catalog_errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_parse_jsonish` | JSON 문자열 | `(parsed, errors)` | catalog를 직접 붙여 넣을 때 JSON 오류를 잡아줍니다. |
| `_default_catalog` | 없음 | 기본 dataset catalog | 입력이 비어 있어도 테스트가 가능하도록 기본 dataset 설명을 제공합니다. |
| `load_table_catalog` | 사용자 입력 JSON | `table_catalog_payload` | JSON을 읽고 `datasets` 구조가 없으면 기본값을 쓰거나 오류를 담습니다. |
| `build_payload` | `table_catalog_json` | `Data(data=payload)` | Langflow output method입니다. |

### 코드 흐름

```text
Table catalog JSON 입력
-> JSON 파싱
-> 비어 있으면 default catalog 사용
-> Intent LLM이 dataset/tool을 고를 수 있는 설명 payload 반환
```

### 초보자 포인트

Table catalog는 실제 데이터를 조회하지 않습니다. LLM이 "생산량이라는 말은 production dataset을 뜻한다"처럼 dataset을 고를 수 있게 도와주는 안내서 역할입니다.

## 함수 코드 단위 해석: `load_table_catalog`

이 함수는 table catalog JSON을 읽고, Intent LLM이 사용할 dataset 설명 payload로 만듭니다.

### 함수 input

```json
{
  "datasets": {
    "production": {
      "keywords": ["생산", "생산량"],
      "tool_name": "get_production_data"
    }
  }
}
```

### 함수 output

```json
{
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {
          "keywords": ["생산", "생산량"],
          "tool_name": "get_production_data"
        }
      }
    },
    "table_catalog_errors": []
  }
}
```

### 핵심 코드 해석

```python
raw, errors = _parse_jsonish(table_catalog_json)
```

Langflow 입력창에 들어온 문자열을 JSON으로 바꿉니다. 입력이 비어 있거나 잘못된 JSON이면 `errors`에 메시지를 담습니다.

```python
if not raw:
    raw = _default_catalog()
```

사용자가 catalog를 비워두면 기본 catalog를 사용합니다. 이 덕분에 local dummy 테스트는 별도 catalog 없이도 어느 정도 실행됩니다.

```python
catalog = raw.get("table_catalog") if isinstance(raw.get("table_catalog"), dict) else raw
```

입력이 이미 `{"table_catalog": {...}}`로 감싸져 있으면 안쪽만 꺼내고, 아니면 입력 자체를 catalog로 봅니다.

```python
if not isinstance(catalog.get("datasets"), dict):
    errors.append("table_catalog.datasets must be an object.")
```

Intent LLM은 `datasets`를 보고 어떤 데이터를 조회할지 결정합니다. 그래서 `datasets`가 dict인지 확인합니다.

```python
return {
    "table_catalog_payload": {
        "table_catalog": catalog,
        "table_catalog_errors": errors,
    }
}
```

다음 노드가 항상 같은 key로 읽을 수 있게 `table_catalog_payload`로 감싸서 반환합니다.
