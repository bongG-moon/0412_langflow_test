# 08. Normalize Intent Plan

## 이 노드 역할

LLM의 intent 응답을 실제 flow가 사용할 수 있는 `intent_plan`으로 정리하고 보정하는 노드입니다.

## 왜 필요한가

LLM 응답은 초안입니다. 다음과 같은 실수가 있을 수 있습니다.

- dataset을 하나만 말했지만 metric 계산에는 여러 dataset이 필요할 수 있습니다.
- `오늘`, `어제` 같은 날짜를 잘못된 날짜로 뽑을 수 있습니다.
- 후속 질문처럼 보이지만 실제로는 날짜나 필터가 바뀐 새 조회일 수 있습니다.
- 표준 필터 key가 아니라 실제 컬럼명을 섞어서 반환할 수 있습니다.

이 노드는 domain, table catalog, main flow filters, 이전 state를 다시 확인해서 실행 가능한 계획으로 고칩니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Intent)` 출력입니다. LLM text와 prompt context가 들어 있습니다. |
| `reference_date` | 날짜 해석 기준일 override입니다. 비어 있으면 prompt payload의 reference_date를 사용합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `intent_plan` | route, retrieval_jobs, filters, column_filters, filter_plan 등을 포함한 실행 계획입니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON object를 꺼냅니다.
- `_extract_date`: `오늘`, `어제`, `20260425`, `2026-04-25` 같은 날짜 표현을 `YYYYMMDD`로 바꿉니다.
- `_dataset_hints`: 질문과 catalog/domain 정보를 보고 필요한 dataset 후보를 찾습니다.
- `_matched_metrics`: 질문과 맞는 metric 정의를 domain에서 찾습니다.
- `_filters_from_question`: domain의 제품/공정 그룹/용어 filter와 main flow filter 힌트를 표준 `filters`로 변환합니다.
- `_column_filters_from_question`: 표준 필터에 없지만 실제 컬럼으로 보이는 조건을 `column_filters`로 만듭니다.
- `_merge_conditions`: 이전 턴 조건과 현재 턴 조건을 합칩니다.
- `_required_param_changed`: `date` 같은 required parameter가 이전 턴과 달라졌는지 확인합니다.
- `_filters_within_current_scope`: 현재 데이터 안에서 후속 필터 처리가 가능한지 확인합니다.
- `_filter_plan`: 표준 필터 key를 dataset별 실제 컬럼명으로 풀어 줍니다.
- `_build_job`: dataset 하나를 조회하기 위한 retrieval job을 만듭니다.
- `_normalize_plan`: 전체 plan을 route 가능한 최종 형태로 만듭니다.
- `normalize_intent_plan`: Langflow에서 호출되는 최상위 정규화 함수입니다.

## 출력 예시

```json
{
  "intent_plan": {
    "request_type": "data_question",
    "query_mode": "retrieval",
    "route": "multi_retrieval",
    "needed_datasets": ["production", "target"],
    "required_params": {"date": "20260425"},
    "filters": {"process_name": ["W/B1", "W/B2"]},
    "column_filters": {},
    "filter_plan": [
      {
        "kind": "semantic",
        "field": "process_name",
        "dataset_key": "production",
        "columns": ["OPER_NAME"],
        "operator": "in",
        "value_type": "string",
        "value_shape": "list",
        "values": ["W/B1", "W/B2"]
      }
    ],
    "group_by": ["MODE"],
    "needs_pandas": true,
    "metric_keys": ["achievement_rate"],
    "retrieval_jobs": [
      {
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "params": {"date": "20260425"},
        "filters": {"process_name": ["W/B1", "W/B2"]}
      },
      {
        "dataset_key": "target",
        "tool_name": "get_target_data",
        "params": {"date": "20260425"},
        "filters": {"process_name": ["W/B1", "W/B2"]}
      }
    ]
  }
}
```

## 초보자 확인용

이 노드는 LLM 결과를 그대로 믿지 않습니다.

예를 들어 `생산달성률` 질문에서 LLM이 `production`만 말해도, domain metric이 `production`과 `target`을 요구하면 이 노드가 `target`을 추가합니다.

또 `오늘`이라고 물었는데 LLM이 엉뚱한 날짜를 반환해도, 질문 원문에서 날짜를 다시 추출해 `reference_date` 기준으로 보정합니다.

## 연결

```text
LLM JSON Caller (Intent).llm_result
-> Normalize Intent Plan.llm_result

Normalize Intent Plan.intent_plan
-> Intent Route Router.intent_plan
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "llm_result": {
    "llm_text": "{\"query_mode\":\"retrieval\",\"needed_datasets\":[\"production\"],\"filters\":{\"process_name\":[\"W/B1\",\"W/B2\"]},\"needs_pandas\":true}",
    "prompt_payload": {
      "state": {
        "pending_user_question": "어제 WB공정 생산달성률을 mode별로 알려줘",
        "current_data": null
      },
      "domain": {
        "metrics": {
          "achievement_rate": {
            "aliases": ["달성률", "달성율"],
            "required_datasets": ["production", "target"]
          }
        }
      },
      "table_catalog": {
        "datasets": {
          "production": {
            "tool_name": "get_production_data",
            "required_params": ["date"],
            "filter_mappings": {"process_name": ["OPER_NAME"]}
          },
          "target": {
            "tool_name": "get_target_data",
            "required_params": ["date"],
            "filter_mappings": {"process_name": ["OPER_NAME"]}
          }
        }
      },
      "main_flow_filters": {
        "filters": {
          "process_name": {"operator": "in", "value_type": "string", "value_shape": "list"}
        }
      },
      "reference_date": "2026-04-26"
    }
  }
}
```

### 출력 예시

```json
{
  "intent_plan": {
    "query_mode": "retrieval",
    "route": "multi_retrieval",
    "needed_datasets": ["production", "target"],
    "required_params": {"date": "20260425"},
    "filters": {"process_name": ["W/B1", "W/B2"]},
    "group_by": ["MODE"],
    "needs_pandas": true,
    "planner_source": "llm"
  },
  "retrieval_jobs": [
    {"dataset_key": "production", "tool_name": "get_production_data"},
    {"dataset_key": "target", "tool_name": "get_target_data"}
  ]
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_extract_json_object` | `"설명... {\"route\":\"single_retrieval\"}"` | `{"route": "single_retrieval"}` | LLM이 JSON 앞뒤에 설명을 붙여도 실제 JSON만 꺼냅니다. |
| `_extract_date` | `"어제 생산"`, 기준일 `2026-04-26` | `"20260425"` | 자연어 날짜를 조회 파라미터 형식으로 바꿉니다. |
| `_dataset_hints` | 질문, catalog, domain | `["production"]` | LLM fallback이 필요할 때 질문 키워드로 dataset 후보를 찾습니다. |
| `_matched_metrics` | `"생산달성률"` | `{"achievement_rate": {...}}` | metric alias를 찾아 필요한 dataset과 계산 목표를 보정합니다. |
| `_filters_from_question` | `"WB공정 DDR5"` + domain | `{"process_name": ["W/B1", "W/B2"], "mode": ["DDR5"]}` | domain에 등록된 alias/filter 규칙으로 표준 필터 조건을 추출합니다. |
| `_column_filters_from_question` | `"PKG_TYPE1 PKG_A만"` | `{"PKG_TYPE1": ["PKG_A"]}` | main_flow_filters에 없는 실제 컬럼 조건을 보존합니다. |
| `_filter_plan` | filters, catalog mapping | `[{"field": "process_name", "columns": ["OPER_NAME"]}]` | 표준 key를 실제 dataset 컬럼명으로 연결합니다. |
| `_build_job` | dataset config, params, filters | retrieval job dict | retriever가 바로 실행할 작업 단위를 만듭니다. |
| `_normalize_plan` | raw LLM plan + context | 최종 intent plan | route, jobs, 상속, 보정을 모두 처리합니다. |
| `normalize_intent_plan` | `llm_result` | `{"intent_plan": ...}` | Langflow output method가 사용하는 최상위 함수입니다. |

### 코드 흐름

```text
LLM result 입력
-> llm_text에서 JSON 추출
-> prompt_payload에서 state/domain/catalog/main_flow_filters 복원
-> LLM JSON이 비어 있거나 깨졌으면 heuristic fallback 생성
-> 날짜, dataset, metric, filter 보정
-> 이전 조건 상속
-> required param 변경과 current_data scope 검사
-> filter_plan 생성
-> retrieval_jobs 생성
-> route 결정
-> intent_plan 반환
```

## 함수 코드 단위 해석: `_normalize_plan`

이 함수는 LLM이 만든 raw plan을 실제 실행 가능한 최종 plan으로 바꿉니다.

### 함수 input

```json
{
  "raw_plan": {
    "query_mode": "retrieval",
    "needed_datasets": ["production"],
    "filters": {"process_name": ["W/B1", "W/B2"]},
    "needs_pandas": true
  },
  "question": "어제 WB공정 생산달성률을 mode별로 알려줘",
  "reference_date": "2026-04-26"
}
```

### 함수 output

```json
{
  "query_mode": "retrieval",
  "route": "multi_retrieval",
  "needed_datasets": ["production", "target"],
  "required_params": {"date": "20260425"},
  "filters": {"process_name": ["W/B1", "W/B2"]},
  "group_by": ["MODE"],
  "needs_pandas": true,
  "retrieval_jobs": [
    {"dataset_key": "production"},
    {"dataset_key": "target"}
  ]
}
```

### 핵심 코드 해석

```python
matched_metrics = _matched_metrics(question, domain)
```

질문에서 metric alias를 찾습니다. `생산달성률`처럼 복합어 안에 `달성률`이 들어 있어도 matching되도록 정규화합니다.

```python
for metric in matched_metrics.values():
    needed_datasets.extend(str(item) for item in _as_list(metric.get("required_datasets")))
```

metric이 요구하는 dataset을 추가합니다. LLM이 `production`만 반환해도 `target`이 필요하면 여기서 추가됩니다.

```python
explicit_filters = {**_filters_from_question(question, domain, main_flow_filters), **raw_filters}
```

질문에서 deterministic하게 뽑은 필터와 LLM이 반환한 필터를 합칩니다. 같은 key가 있으면 LLM raw filter가 뒤에서 덮어씁니다.

```python
explicit_params = _normalize_param_values({**_drop_empty_params(raw_params), **_explicit_required_params(question, reference_date)})
```

질문 원문에 명시된 날짜나 lot_id를 다시 추출합니다. 이 때문에 LLM이 날짜를 잘못 뽑아도 `오늘`, `어제` 같은 표현이 기준일에 맞게 보정됩니다.

```python
required_changed = _required_param_changed(previous_params if isinstance(previous_params, dict) else {}, explicit_params)
```

이전 턴의 required parameter와 현재 질문에서 명시한 required parameter가 달라졌는지 확인합니다. 예를 들어 `오늘`에서 `어제`로 바뀌면 새 retrieval로 보내야 합니다.

```python
if query_mode == "followup_transform" and (required_changed or not _filters_within_current_scope(state, filters, column_filters)):
    query_mode = "retrieval"
```

LLM이 후속 질문이라고 판단했더라도, 날짜가 바뀌었거나 현재 데이터 범위 밖의 필터가 들어오면 새 조회로 바꿉니다.

```python
resolved_filter_plan = _filter_plan(filters, column_filters, needed_datasets, table_catalog, main_flow_filters, _current_columns(state))
```

표준 필터 key를 실제 컬럼명으로 연결합니다. 예를 들어 `process_name`은 production dataset에서 `OPER_NAME`이 될 수 있습니다.

```python
route = "followup_transform" if query_mode == "followup_transform" else ("multi_retrieval" if len(jobs) > 1 else "single_retrieval")
```

최종 route를 정합니다. 조회 job이 여러 개면 `multi_retrieval`, 하나면 `single_retrieval`, 기존 데이터 후속 분석이면 `followup_transform`입니다.

## 후속 질문 판단 예시

```text
1차: 오늘 DA공정 DDR5 생산 보여줘
2차: 어제 WB공정은?
```

2차 질문은 짧지만 날짜와 공정이 모두 바뀌었습니다. 따라서 기존 current_data 후속 분석이 아니라 새 retrieval입니다.

```text
1차: 어제 WB공정 생산 보여줘
2차: 그 결과를 mode별로 정리해줘
```

2차 질문은 날짜와 필터가 바뀌지 않고 현재 결과를 가리키므로 `followup_transform`입니다.

## 추가 함수 코드 단위 해석: `_extract_date`

이 함수는 사용자 질문에서 날짜를 `YYYYMMDD` 형식으로 추출합니다.

```python
base = _runtime_today(reference_date)
```

기준 날짜를 가져옵니다. 테스트나 재현이 필요하면 `reference_date`를 넣고, 비어 있으면 Asia/Seoul 기준 현재 날짜를 사용합니다.

```python
if any(token in lowered for token in ("today", "금일", "오늘")):
    return base.strftime("%Y%m%d")
```

"오늘" 계열 표현은 기준 날짜로 변환합니다.

```python
if any(token in lowered for token in ("yesterday", "어제", "전일")):
    return (base - timedelta(days=1)).strftime("%Y%m%d")
```

"어제" 계열 표현은 기준 날짜에서 하루를 뺍니다.

```python
match = re.search(r"\b(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?([0-2]\d|3[01])\b", str(question or ""))
```

`2026-04-26`, `20260426`, `2026.04.26` 같은 명시 날짜를 찾습니다.

## 추가 함수 코드 단위 해석: `_dataset_hints`

이 함수는 LLM 응답이 비었거나 dataset이 누락됐을 때 질문에서 dataset 후보를 찾습니다. 특정 dataset keyword를 Python 코드에 직접 넣지 않고 table catalog와 domain만 사용합니다.

```python
domain_dataset = _domain_dataset_config(domain, dataset_key)
```

현재 dataset key에 대응되는 `domain.datasets[dataset_key]` 정의를 가져옵니다.

```python
candidates = [
    dataset_key,
    dataset.get("display_name", ""),
    dataset.get("description", ""),
    *_as_list(dataset.get("keywords")),
    *_as_list(dataset.get("aliases")),
    *_as_list(dataset.get("question_examples")),
    *_alias_candidates(str(dataset_key), domain_dataset),
]
```

dataset 후보 문자열은 table catalog와 domain dataset 정의에서만 모읍니다. 예를 들어 `생산`, `실적`, `output` 같은 말은 `DEFAULT_DATASET_KEYWORDS`가 아니라 catalog/domain에 등록되어 있어야 합니다.

```python
for _metric_key, metric in _matched_metrics(question, domain).items():
    found.extend(str(item) for item in _as_list(metric.get("required_datasets")))
```

질문이 domain metric alias와 매칭되면 metric의 `required_datasets`를 추가합니다. 예를 들어 달성률이 production과 target을 요구한다는 정보는 `domain.metrics.achievement_rate.required_datasets`에서 옵니다.

## 추가 함수 코드 단위 해석: `_matches_alias`

domain alias를 질문과 비교하는 공통 함수입니다.

```python
if re.fullmatch(r"[A-Za-z0-9]{1,3}", text):
    if re.search(rf"(?i)(?<![A-Za-z0-9]){re.escape(text)}(?![A-Za-z0-9])", str(question or "")):
        return True
```

`DA`, `WB`처럼 짧은 영문 alias는 `data` 같은 단어 일부와 잘못 매칭될 수 있습니다. 그래서 짧은 영문/숫자 alias는 앞뒤가 영문/숫자가 아닌 독립 토큰일 때만 매칭합니다.

```python
if normalized_alias in normalized_question:
    return True
```

그 외 한글 alias, 긴 제품명, `D/A`처럼 특수문자가 들어간 alias는 공백 제거 후 부분 포함으로 매칭합니다.

## 추가 함수 코드 단위 해석: `_filters_from_question`

이 함수는 질문 문장에서 표준 의미 필터를 deterministic하게 추출합니다. 단, 실제 공정명이나 제품군 값은 코드에 직접 박지 않고 domain에서 읽습니다.

```python
filters: Dict[str, Any] = _domain_filter_matches(question, domain)
```

먼저 domain에 등록된 제품, 공정 그룹, 용어 규칙을 확인합니다. 예를 들어 `domain.process_groups.WB.aliases`에 `WB공정`이 있고 `processes`에 `W/B1`, `W/B2`가 있으면 `process_name` 필터로 확장됩니다.

```python
process_groups = domain.get("process_groups") if isinstance(domain.get("process_groups"), dict) else {}
```

공정 그룹은 domain에서만 읽습니다. 그래서 사내 공정 체계가 바뀌면 Python 코드를 고치지 않고 domain 문서만 수정하면 됩니다.

```python
if _matches_alias(question, _alias_candidates(str(group_key), group)):
    group_filters = group.get("filters") if isinstance(group.get("filters"), dict) else {}
    if group_filters:
        for field, values in group_filters.items():
            _merge_filter_values(filters, str(field), values)
    elif processes:
        _merge_filter_values(filters, "process_name", processes)
```

공정 그룹에 `filters`가 있으면 그 정의를 우선 사용하고, 없으면 기존 `processes` 목록을 `process_name`으로 해석합니다. 이 fallback은 domain schema 호환을 위한 것이지 특정 공정명을 코드에 넣는 방식은 아닙니다.

```python
for section_name in ("products", "terms"):
    section = domain.get(section_name) if isinstance(domain.get(section_name), dict) else {}
```

제품군이나 용어도 domain에서 읽습니다. 예를 들어 `domain.products.DDR5.filters = {"mode": ["DDR5"]}`처럼 등록하면 질문의 `DDR5`가 mode 필터로 변환됩니다.

```python
value_aliases = definition.get("value_aliases") if isinstance(definition.get("value_aliases"), dict) else {}
known_values = definition.get("known_values") or definition.get("values")
```

main flow filters에 선택적으로 들어 있는 값 alias나 known values도 사용합니다. 다만 이 값들은 필수가 아니라 보조 힌트입니다.

## 추가 함수 코드 단위 해석: `_filter_plan`

이 함수는 표준 의미 필터를 실제 dataset 컬럼에 매핑한 실행 계획으로 바꿉니다.

```python
configs = _dataset_configs(table_catalog)
active_datasets = needed_datasets or list(configs.keys())
```

조회할 dataset이 정해져 있으면 그 dataset만 대상으로 하고, 비어 있으면 catalog 전체를 대상으로 filter plan을 만듭니다.

```python
columns = _dataset_filter_columns(dataset, filter_key)
```

`process_name` 같은 표준 key가 해당 dataset의 어떤 실제 컬럼에 연결되는지 찾습니다. 이때 table catalog의 `filter_mappings`가 핵심입니다.

```python
plan.append({
    "kind": "semantic",
    "field": filter_key,
    "dataset_key": dataset_key,
    "columns": columns,
    "operator": definition.get("operator", "in"),
    "value_type": definition.get("value_type", "string"),
    "value_shape": definition.get("value_shape", "list"),
    "values": _as_list(values),
    "definition": definition,
})
```

후속 Retriever나 pandas executor가 그대로 사용할 수 있도록 field, dataset, 실제 columns, 값, 값 형식을 모두 포함합니다.

```python
for column, values in column_filters.items():
    if str(column) not in all_columns:
        continue
```

main flow filters에 정의되지 않았더라도 실제 테이블 컬럼이면 column filter로 허용합니다.

## 추가 함수 코드 단위 해석: `_required_param_changed`

후속 질문처럼 보이더라도 필수 조회 조건이 바뀌면 신규 조회로 돌리기 위한 판단 함수입니다.

```python
for key, value in explicit_params.items():
    if value in (None, "", []):
        continue
```

이번 질문에서 명시적으로 추출된 required param만 확인합니다.

```python
if previous.get(key) not in (None, "", []) and str(previous.get(key)) != str(value):
    return True
```

이전 값이 있고 이번 값과 다르면 변경으로 봅니다. 예를 들어 이전 질문이 `오늘`이고 다음 질문이 `어제`면 `date`가 바뀐 것입니다.

```python
return False
```

명시 변경이 없으면 기존 required param 상속이 가능합니다.

## 추가 함수 코드 단위 해석: `_normalize_plan`의 follow-up 판별

```python
followup_like = _contains_any(question, ["그 결과", "이 결과", "현재 결과", "그중", "그 중", "여기서", "방금", ...])
```

사용자가 이전 결과를 가리키는 표현을 썼는지 확인합니다.

```python
query_mode = "followup_transform" if _has_current_data(state) and followup_like and not explicit_fresh else "retrieval"
```

현재 데이터가 있고, 질문이 이전 결과를 가리키며, 새로 조회하라는 표현이 없으면 후속 분석으로 판단합니다.

```python
if query_mode == "followup_transform" and (required_changed or not _filters_within_current_scope(state, filters, column_filters)):
    query_mode = "retrieval"
```

핵심 안전장치입니다. 날짜 같은 필수 조건이 바뀌거나 새 필터가 현재 데이터 범위를 벗어나면 후속 분석이 아니라 신규 조회로 바꿉니다.

```python
route = "followup_transform" if query_mode == "followup_transform" else ("multi_retrieval" if len(jobs) > 1 else "single_retrieval")
```

최종적으로 router가 사용할 route를 결정합니다.
