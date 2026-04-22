# 12. Retrieval Plan Builder

정규화된 intent와 query mode 결과를 보고 어떤 데이터 tool을 실행할지 정하는 노드다.

필수 parameter와 tool name은 domain이 아니라 table catalog를 우선 기준으로 삼는다. table catalog가 없을 때만 기존 domain dataset 정보를 fallback으로 사용한다.

## 입력

```text
query_mode_decision
main_context
domain_payload
agent_state
table_catalog_payload
```

권장 입력은 `query_mode_decision` 하나다. 이전 노드 payload 안에 `main_context`가 같이 전달된다.

## 출력

```text
retrieval_plan
```

## 핵심 변경점

이 노드는 더 이상 SQL이나 query template을 만들지 않는다.

하는 일:

- 필요한 dataset key 결정
- metric이 요구하는 dataset 추가
- table catalog의 dataset별 필수 parameter만 `params`에 넣기
- product/process/line 같은 후처리 조건은 `post_filters`에 넣기
- table catalog의 `tool_name` 기준으로 실행할 tool name 결정

## Job 예시

```json
{
  "dataset_key": "production",
  "dataset_label": "생산 데이터",
  "tool_name": "get_production_data",
  "params": {
    "date": "2026-04-22"
  },
  "post_filters": {
    "product": "A제품"
  },
  "filter_expressions": [],
  "result_label": null
}
```

## 기본 tool 매핑

```text
production -> get_production_data
target -> get_target_data
defect -> get_defect_rate
equipment -> get_equipment_status
wip -> get_wip_status
yield -> get_yield_data
hold -> get_hold_lot_data
scrap -> get_scrap_data
recipe -> get_recipe_condition_data
lot_trace -> get_lot_trace_data
```

domain dataset item에 `tool_name` 또는 `tool.name`이 있으면 그 값을 우선 사용한다.

## 필수 parameter와 후처리 filter 구분

예를 들어 생산 데이터의 필수 조회 조건이 `date`라면:

- `오늘`, `어제` 같은 날짜 조건은 `params.date`에 들어간다.
- `A제품`, `D/A 공정`, `LINE-1` 같은 조건은 원본 조회 이후 pandas에서 거르므로 `post_filters`에 들어간다.

이 구조 때문에 후속 질문에서 날짜가 바뀌면 신규 조회가 필요하고, 제품만 바뀌면 기존 raw data를 재사용할 수 있다.
