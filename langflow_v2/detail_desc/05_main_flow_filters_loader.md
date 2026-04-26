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
