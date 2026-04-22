# 13. Dummy Data Retriever

`Retrieval Plan Builder`가 만든 tool 실행 계획을 더미 데이터로 수행하는 노드다.

## 입력

```text
retrieval_plan
main_context
domain_payload
agent_state
row_limit
```

권장 입력은 `retrieval_plan`이다. domain과 state는 payload 안의 `main_context`에서 읽는다.

## 출력

```text
retrieval_result
```

## 역할

- `retrieval_plan.jobs`를 하나씩 읽는다.
- job의 `tool_name`에 해당하는 더미 tool 함수를 호출한다.
- product/process/line 같은 조건은 여기서 강제로 거르지 않고 `post_filters`로 다음 pandas 분석 단계에 넘긴다.
- 지원하지 않는 tool이면 공통 더미 데이터를 억지로 만들지 않고 실패 결과를 반환한다.

## Tool별 독립 더미 생성

이 노드는 더 이상 공통 row builder에 dataset key만 넘겨서 데이터를 만들지 않는다.

각 tool 함수가 자기 parameter를 직접 읽고, 자기 output schema에 맞는 row를 직접 생성한다.

| Tool | 주요 parameter | 생성되는 주요 컬럼 |
| --- | --- | --- |
| `get_production_data` | `date` | `WORK_DT`, `OPER_NAME`, `LINE`, product columns, `production`, `lot_count` |
| `get_target_data` | `date`, `plan_version` | `WORK_DT`, `PLAN_VERSION`, product/process columns, `target` |
| `get_schedule_data` | `date` | `SCHD_SEQ`, `schedule_input_qty`, `schedule_output_qty`, product/process columns |
| `get_capa_data` | `date` | `WORK_DT`, `OPER_NAME`, product/process columns, `capa_qty` |
| `get_defect_rate` | `date`, `inspection_type` | `inspection_qty`, `defect_qty`, `defect_rate`, `top_defect_code` |
| `get_equipment_status` | `date`, `equipment_area` | `EQUIPMENT_ID`, `planned_hours`, `actual_hours`, `down_minutes`, `utilization_rate`, `status` |
| `get_wip_status` | `date`, `snapshot_time` | `wip_qty`, `avg_wait_minutes`, `aging_bucket` |
| `get_yield_data` | `date`, `test_step` | `tested_qty`, `pass_qty`, `yield_rate` |
| `get_hold_lot_data` | `date`, `hold_reason_group` | `hold_qty`, `hold_hours`, `hold_reason` |
| `get_scrap_data` | `date`, `scrap_type` | `input_qty`, `scrap_qty`, `scrap_rate` |
| `get_recipe_condition_data` | `date`, `process` | `RECIPE_ID`, `condition_name`, `condition_value`, `lower_limit`, `upper_limit` |
| `get_lot_trace_data` | `lot_id`, `date` | `LOT_ID`, `SEQ`, `move_in_time`, `move_out_time`, `stay_hours`, `lot_status` |

실제 필수 parameter 검증은 `Retrieval Plan Builder`가 domain의 `required_params`를 기준으로 먼저 수행한다. Dummy tool 함수는 테스트 편의를 위해 parameter가 없으면 안전한 기본값을 사용한다.

## 반환 예시

```json
{
  "retrieval_result": {
    "route": "single_retrieval",
    "source_results": [
      {
        "success": true,
        "tool_name": "get_production_data",
        "dataset_key": "production",
        "dataset_label": "생산 데이터",
        "data": [],
        "summary": "production dummy data 120 rows",
        "applied_params": {
          "date": "2026-04-22"
        },
        "post_filters": {},
        "filter_expressions": [],
        "source_tag": "source_1",
        "from_dummy": true
      }
    ]
  }
}
```

## 연결

```text
Retrieval Plan Builder.retrieval_plan
-> Dummy Data Retriever.retrieval_plan

Dummy Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```
