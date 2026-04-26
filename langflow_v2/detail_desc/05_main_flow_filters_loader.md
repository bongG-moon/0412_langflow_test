# 05 Main Flow Filters Loader

## 역할

`Main Flow Filters Loader`는 intent planner가 공통으로 사용할 표준 의미 필터 정의를 로드합니다.

이 노드는 `Table Catalog Loader`와 domain 규칙과 일부러 분리되어 있습니다.

- `main_flow_filters`는 `process_name`, `mode`, `line`, `product_name`, `equipment_id`, `den`, `tech`, `mcp_no`처럼 여러 데이터셋에서 공통으로 쓰는 의미 key를 정의합니다.
- `table_catalog.filter_mappings`는 그 의미 key를 각 데이터셋의 실제 컬럼명으로 매핑합니다.
- `domain.process_groups`는 `DA공정 -> D/A1, D/A2, D/A3`처럼 공정 그룹 alias와 확장 값을 정의합니다.

예를 들어 intent plan은 계속 `process_name`을 사용할 수 있고, 각 테이블은 자기 컬럼명에 맞게 매핑할 수 있습니다.

```json
{
  "production": {"filter_mappings": {"process_name": ["OPER_NAME"]}},
  "some_other_table": {"filter_mappings": {"process_name": ["process_nm"]}}
}
```

## 입력

- `main_flow_filters_json`: JSON 또는 JSON-like text입니다.

권장 형태:

```json
{
  "required_params": {
    "date": {
      "value_type": "date",
      "value_shape": "scalar",
      "normalized_format": "YYYYMMDD",
      "aliases": ["date", "work_date", "WORK_DT", "일자", "날짜"]
    }
  },
  "filters": {
    "process_name": {
      "value_type": "string",
      "value_shape": "list",
      "operator": "in",
      "aliases": ["process", "process_name", "process_nm", "oper", "operation", "공정"]
    },
    "mode": {
      "value_type": "string",
      "value_shape": "list",
      "operator": "in",
      "aliases": ["mode", "product mode", "모드"]
    }
  }
}
```

이 입력은 작게 유지하는 것을 권장합니다. 여기에는 모든 가능한 값을 다 넣기보다, 표준 의미 key와 그 key를 부르는 다른 이름만 정의하는 편이 관리하기 쉽습니다.

`required_params.date.normalized_format`은 intent plan에서 일자를 `YYYYMMDD`로 만들라는 planner용 가이드입니다. 이것은 Table Catalog의 `param_format`이 아닙니다. DB나 tool별로 필요한 날짜 변환은 retriever 함수가 담당합니다.

제조 필터의 기본 권장 형식은 `value_type: "string"`, `value_shape: "list"`, `operator: "in"`입니다. 이렇게 두면 intent plan의 필터 구조가 일관되고, 실제 컬럼 적용은 `filter_plan`과 retriever에서 처리할 수 있습니다.

공정 그룹 확장은 `domain.process_groups`에 둡니다.

```json
{
  "process_groups": {
    "DA": {
      "aliases": ["DA", "D/A", "DA공정"],
      "processes": ["D/A1", "D/A2", "D/A3"]
    },
    "WB": {
      "aliases": ["WB", "W/B", "WB공정"],
      "processes": ["W/B1", "W/B2"]
    }
  }
}
```

`known_values`나 `value_aliases` 같은 고급 필드는 특수한 경우에 사용할 수 있습니다. 하지만 기본 운영에서는 권장하지 않습니다. 값 확장 규칙까지 `main_flow_filters`에 넣으면 JSON이 커지고 유지보수가 어려워지기 때문입니다.

## 출력

- `main_flow_filters_payload`

Payload 형태:

```json
{
  "main_flow_filters_payload": {
    "main_flow_filters": {
      "required_params": {},
      "filters": {}
    },
    "main_flow_filter_errors": []
  }
}
```

## 사용 방식

`Build Intent Prompt`는 이 정의를 LLM에게 전달합니다.

`Normalize Intent Plan`은 이 정보를 사용해 다음 일을 합니다.

- 사용자 질문과 LLM 출력에서 표준 의미 필터 key를 이해합니다.
- 후속 질문에서 이전 필터를 상속합니다.
- 표준 의미 key와 `table_catalog.filter_mappings`를 합쳐 `filter_plan`을 만듭니다.
- `main_flow_filters`에 정의되지 않았지만 실제 테이블 컬럼으로 존재하는 조건은 `column_filters`로 유지합니다.

이후 질문에서 `date` 같은 required parameter가 바뀌면, normalizer는 그 질문을 기존 current data 후속 분석으로 보지 않고 새 retrieval로 라우팅합니다.

## 함수 코드 단위 해석: `_normalize_filter`

이 함수는 `main_flow_filters.filters`에 들어온 각 표준 필터 정의를 같은 형식으로 정리합니다.

### 함수 input

```json
{
  "key": "process_name",
  "value": {
    "display_name": "Process",
    "aliases": ["process", "공정"],
    "known_values": ["D/A1", "W/B1"]
  }
}
```

### 함수 output

```json
{
  "display_name": "Process",
  "description": "",
  "value_type": "string",
  "value_shape": "list",
  "operator": "in",
  "aliases": ["process_name", "process", "공정"],
  "known_values": ["D/A1", "W/B1"]
}
```

### 핵심 코드 해석

```python
payload = deepcopy(value) if isinstance(value, dict) else {"description": str(value or "")}
```

필터 정의가 dict면 복사해서 사용하고, 문자열처럼 들어오면 description만 가진 dict로 바꿉니다.

```python
aliases = _unique_strings([key, *_as_list(payload.get("aliases"))])
```

필터 key 자체도 alias에 포함합니다. 그래서 사용자가 alias를 비워도 `process_name` 같은 표준 key는 항상 인식됩니다.

```python
known_values = _unique_strings(_as_list(payload.get("known_values") or payload.get("values")))
```

선택적으로 관리하는 대표 값 목록을 정리합니다. 모든 실제 값을 넣을 필요는 없고 자주 쓰는 값만 넣어도 됩니다.

```python
value_aliases = payload.get("value_aliases") if isinstance(payload.get("value_aliases"), dict) else {}
```

현재 설계에서는 값 alias를 필수로 관리하지 않습니다. 입력에 있을 때만 정규화해서 보존합니다.

```python
"value_type": str(payload.get("value_type") or "string").strip(),
"value_shape": str(payload.get("value_shape") or "list").strip(),
"operator": str(payload.get("operator") or "in").strip(),
```

표준 필터는 기본적으로 문자열 list를 `in` 조건으로 적용한다고 명시합니다.

## 추가 함수 코드 단위 해석: `_normalize_required_param`

일자 같은 필수 조회 파라미터를 정규화하는 함수입니다.

```python
payload = deepcopy(value) if isinstance(value, dict) else {"description": str(value or "")}
```

입력이 dict가 아니어도 description 기반의 설정으로 바꿉니다.

```python
"value_shape": str(payload.get("value_shape") or "scalar").strip(),
```

필수 파라미터는 기본적으로 단일 값입니다. 예를 들어 `date`는 하나의 `YYYYMMDD` 문자열입니다.

```python
"normalized_format": str(payload.get("normalized_format") or payload.get("format") or "").strip(),
```

`date`처럼 형식이 중요한 값은 `YYYYMMDD` 같은 normalized format을 보존합니다.

```python
"aliases": _unique_strings([key, *_as_list(payload.get("aliases"))]),
```

`date`, `WORK_DT`, `일자`, `날짜`처럼 같은 의미의 표현을 하나의 required param으로 묶습니다.

## 추가 함수 코드 단위 해석: `load_main_flow_filters`

이 함수는 사용자가 입력한 main flow filters와 기본 필터 정의를 병합합니다.

```python
parsed, errors = _parse_jsonish(main_flow_filters_json)
```

JSON 문자열, dict, Python literal 스타일 입력을 모두 받아 파싱합니다.

```python
if isinstance(parsed, dict) and isinstance(parsed.get("main_flow_filters"), dict):
    config = deepcopy(parsed["main_flow_filters"])
elif isinstance(parsed, dict) and isinstance(parsed.get("filters"), dict):
    config = deepcopy(parsed)
elif isinstance(parsed, dict) and parsed:
    config = {"filters": deepcopy(parsed)}
else:
    config = _default_filters()
```

입력 구조가 `{"main_flow_filters": ...}`여도 되고, 바로 `{"filters": ...}`여도 됩니다. 비어 있으면 기본 필터를 사용합니다.

```python
merged = {key: deepcopy(value) for key, value in default_filters.items()}
merged.update({str(key): value for key, value in filters.items() if isinstance(value, dict)})
```

기본 필터를 먼저 깔고 사용자 정의가 있으면 덮어씁니다. 사용자가 일부 필터만 정의해도 나머지 기본 필터는 유지됩니다.

```python
config["filters"] = {key: _normalize_filter(key, value) for key, value in merged.items()}
```

최종적으로 모든 필터를 동일한 구조로 정규화합니다.
