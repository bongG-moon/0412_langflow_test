# 07. Normalize Intent Plan

## 한 줄 역할

LLM의 intent 응답을 실제 flow가 사용할 수 있는 `intent_plan`으로 정리하고 보정하는 노드입니다.

## 왜 중요한가

LLM은 가끔 dataset을 하나만 말하거나, 날짜를 빼먹거나, 후속 질문을 새 조회처럼 해석할 수 있습니다.
이 노드는 domain과 table catalog를 다시 확인해서 그런 실수를 줄입니다.

특히 metric에 `required_datasets`가 있으면, LLM이 하나만 말해도 필요한 dataset을 모두 retrieval plan에 추가합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Intent)`의 출력입니다. |
| `reference_date` | 테스트용 기준 날짜입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `intent_plan` | route, retrieval_jobs, filters, group_by 등을 포함한 실행 계획입니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON object를 찾습니다.
- `_extract_date`: `오늘`, `어제` 같은 표현을 날짜로 바꿉니다.
- `_dataset_hints`: 질문과 table/domain 정보를 보고 필요한 dataset 후보를 찾습니다.
- `_matched_metrics`: 질문에 맞는 metric 규칙을 domain에서 찾습니다.
- `_filters_from_question`: 공정, 제품, 조건 표현을 filter로 바꿉니다.
- `_build_job`: dataset 하나를 조회하기 위한 retrieval job을 만듭니다.
- `_normalize_plan`: 전체 intent plan을 route 가능한 형태로 완성합니다.

## 출력 예시

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "query_mode": "retrieval",
    "dataset_hints": ["production", "target"],
    "required_params": {"date": "20260426"},
    "needs_pandas": true
  },
  "retrieval_jobs": []
}
```

## 초보자 포인트

이 노드는 LLM 결과를 그대로 믿지 않습니다.
규칙 기반 보정을 함께 합니다.

예를 들어 `생산달성율`이 domain에서 `production`, `target`을 요구한다면, LLM이 `production`만 반환해도 이 노드가 `target`을 추가합니다.

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
    "llm_text": "{\"query_mode\":\"retrieval\",\"datasets\":[\"production\"],\"filters\":{\"process\":\"WB\"},\"needs_pandas\":true}",
    "prompt_payload": {
      "state": {
        "pending_user_question": "어제 WB공정 생산달성률을 mode별로 알려줘",
        "current_data": null
      },
      "domain": {
        "metrics": {
          "achievement_rate": {
            "aliases": ["달성률"],
            "required_datasets": ["production", "wip"]
          }
        }
      },
      "table_catalog": {
        "datasets": {
          "production": {"tool_name": "get_production_data", "required_params": ["date"]},
          "wip": {"tool_name": "get_wip_status", "required_params": ["date"]}
        }
      }
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
    "datasets": ["production", "wip"],
    "filters": {"process": "WB"},
    "group_by": ["MODE"],
    "needs_pandas": true,
    "retrieval_jobs": [
      {"dataset_key": "production", "tool_name": "get_production_data", "params": {"process": "WB", "date": "20260425"}},
      {"dataset_key": "wip", "tool_name": "get_wip_status", "params": {"process": "WB", "date": "20260425"}}
    ]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_normalize_triple_quoted_json` | `{"dsn": """abc"""}` | 유효한 JSON 문자열 | 사용자가 `""" """`로 넣은 DB/JSON 문자열이 파싱되도록 보정합니다. |
| `_extract_json_object` | LLM 설명문 + JSON | JSON dict | LLM이 JSON 앞뒤로 말을 붙여도 실제 JSON만 꺼냅니다. |
| `_extract_date` | `"어제 생산량"`, 기준일 `2026-04-26` | `"20260425"` | 오늘/어제 같은 자연어 날짜를 조회 파라미터로 바꿉니다. |
| `_dataset_hints` | 질문, catalog, domain | `["production"]` | 질문 속 keyword를 보고 필요한 dataset 후보를 찾습니다. |
| `_matched_metrics` | `"생산달성률"` | `{"achievement_rate": {...}}` | domain metric alias와 질문을 매칭합니다. |
| `_filters_from_question` | `"WB공정 mode별"` | `{"process": "WB"}` | 질문에서 공정, 제품군 같은 filter를 추출합니다. |
| `_group_by_from_question` | `"mode별"` | `["MODE"]` | pandas 집계 기준 컬럼을 추정합니다. |
| `_required_params` | 질문, state | `{"date": "20260425"}` | dataset 조회에 꼭 필요한 날짜 같은 값을 채웁니다. |
| `_build_job` | dataset config, params | retrieval job dict | retriever가 바로 실행할 수 있는 작업 단위로 만듭니다. |
| `_normalize_plan` | LLM plan + domain/catalog | 표준 intent plan | LLM 결과, domain required_datasets, fallback 추론을 합쳐 최종 route를 정합니다. |
| `normalize_intent_plan` | `llm_result` | `intent_plan` payload | Langflow에서 받은 LLM 결과를 실제 flow가 쓰는 형태로 바꿉니다. |

### 코드 흐름

```text
LLM raw text 파싱
-> prompt_payload에서 question/state/domain/catalog 복원
-> 질문에서 날짜/filter/group_by 추출
-> metric required_datasets 반영
-> retrieval_jobs 생성
-> finish/single/multi/followup route 결정
```

### 초보자 포인트

이 노드는 v2 flow의 핵심 안전장치입니다. LLM이 dataset을 하나만 말해도, domain metric에 `required_datasets`가 있으면 여기서 여러 dataset으로 확장합니다.

## 함수 코드 단위 해석: `_normalize_plan`

이 함수는 LLM이 반환한 raw plan을 실제 Langflow route와 retrieval job으로 바꾸는 핵심 함수입니다.

### 함수 input

```json
{
  "raw_plan": {
    "query_mode": "retrieval",
    "datasets": ["production"],
    "filters": {"process": "WB"},
    "needs_pandas": true
  },
  "question": "어제 WB공정 생산달성률을 mode별로 알려줘",
  "state": {"current_data": null},
  "domain": {
    "metrics": {
      "achievement_rate": {
        "aliases": ["달성률"],
        "required_datasets": ["production", "wip"]
      }
    }
  },
  "table_catalog": {
    "datasets": {
      "production": {"tool_name": "get_production_data", "required_params": ["date"]},
      "wip": {"tool_name": "get_wip_status", "required_params": ["date"]}
    }
  }
}
```

### 함수 output

```json
{
  "query_mode": "retrieval",
  "route": "multi_retrieval",
  "needed_datasets": ["production", "wip"],
  "filters": {"process": "WB", "process_name": ["W/B1", "W/B2"]},
  "group_by": ["MODE"],
  "needs_pandas": true,
  "retrieval_jobs": [
    {"dataset_key": "production", "tool_name": "get_production_data", "params": {"date": "20260425"}},
    {"dataset_key": "wip", "tool_name": "get_wip_status", "params": {"date": "20260425"}}
  ]
}
```

### 핵심 코드 해석

```python
configs = _dataset_configs(table_catalog)
matched_metrics = _matched_metrics(question, domain)
```

- `configs`: table catalog에서 dataset 설정만 꺼낸 dict입니다.
- `matched_metrics`: 질문 안에 `"달성률"` 같은 metric alias가 있는지 domain에서 찾은 결과입니다.

```python
needed_datasets = _unique_strings([
    *_as_list(raw_plan.get("needed_datasets")),
    *_as_list(raw_plan.get("dataset_keys")),
    *_as_list(raw_plan.get("datasets")),
])
```

LLM이 dataset을 어떤 key 이름으로 반환할지 완전히 고정하기 어렵기 때문에 여러 후보 key를 모두 읽습니다.

- `needed_datasets`
- `dataset_keys`
- `datasets`

`*_as_list(...)`는 값이 문자열 하나여도 list처럼 합치기 위한 코드입니다.

```python
if str(raw_plan.get("query_mode") or "").strip() != "followup_transform":
    for metric in matched_metrics.values():
        needed_datasets.extend(str(item) for item in _as_list(metric.get("required_datasets")))
```

후속 분석이 아니라 신규 조회라면, metric이 요구하는 dataset을 강제로 추가합니다.

예를 들어 LLM이 `production`만 골랐더라도 `achievement_rate.required_datasets`가 `["production", "wip"]`이면 `wip`이 추가됩니다.

```python
if not needed_datasets:
    needed_datasets = _dataset_hints(question, table_catalog, domain)
```

LLM이 dataset을 못 골랐을 때는 질문 키워드와 catalog/domain을 보고 fallback으로 찾습니다.

```python
needed_datasets = [key for key in _unique_strings(needed_datasets) if key in configs]
```

중복을 제거하고, table catalog에 실제로 존재하는 dataset만 남깁니다. 모르는 dataset 이름이 들어오면 여기서 제거됩니다.

```python
raw_filters = raw_plan.get("filters") if isinstance(raw_plan.get("filters"), dict) else {}
filters = {**_filters_from_question(question, domain), **raw_filters}
```

필터는 두 출처를 합칩니다.

1. 질문에서 rule 기반으로 추출한 필터
2. LLM이 JSON으로 반환한 필터

뒤에 있는 `raw_filters`가 같은 key를 덮어쓸 수 있습니다.

```python
params = _normalize_param_values({
    **_required_params(question, state, reference_date),
    **_drop_empty_params(raw_params)
})
```

날짜 같은 필수 조회 파라미터를 만듭니다. `"어제"` 같은 표현은 `_required_params`에서 기준일 기반 날짜로 바뀝니다.

```python
if query_mode not in {"retrieval", "followup_transform", "finish", "clarification"}:
    query_mode = "followup_transform" if _has_current_data(state) and followup_like and not explicit_fresh else "retrieval"
```

LLM이 query_mode를 이상하게 반환했거나 비워 둔 경우 fallback을 정합니다.

- 이전 current data가 있고
- 질문이 `"이때"`, `"위 결과"`처럼 후속 질문처럼 보이고
- 사용자가 `"새로 조회"`라고 하지 않았다면

`followup_transform`으로 봅니다. 아니면 신규 조회 `retrieval`입니다.

```python
if query_mode == "followup_transform" and not _has_current_data(state):
    query_mode = "retrieval"
```

후속 질문이라고 판단했더라도 실제 이전 데이터가 없으면 분석할 수 없습니다. 그래서 신규 조회로 되돌립니다.

```python
needs_pandas = bool(raw_plan.get("needs_pandas") or raw_plan.get("needs_post_processing") or group_by)
```

LLM이 pandas가 필요하다고 했거나, group_by가 있으면 pandas 분석이 필요하다고 봅니다.

```python
if _contains_any(question, ["별", "기준", "top", "상위", "하위", "정렬", "비교", "달성률", "달성율", "비율", "rate", "ratio", "group", "by"]) or query_mode == "followup_transform" or len(needed_datasets) > 1 or bool(matched_metrics):
    needs_pandas = True
```

질문이 집계/정렬/비율/metric 계산 성격이면 pandas가 필요하다고 강제합니다. 특히 여러 dataset이 필요한 경우에는 거의 항상 후처리가 필요합니다.

```python
for dataset_key in needed_datasets:
    job = _build_job(dataset_key, configs.get(dataset_key, {}), params, filters)
    ...
    jobs.append(job)
```

dataset마다 retriever가 실행할 job을 만듭니다. 이 job이 뒤의 Dummy/Oracle Retriever에서 실제 조회 단위가 됩니다.

```python
route = "followup_transform" if query_mode == "followup_transform" else ("multi_retrieval" if len(jobs) > 1 else "single_retrieval")
```

최종 route를 결정합니다.

- 후속 분석이면 `followup_transform`
- 조회 job이 2개 이상이면 `multi_retrieval`
- 조회 job이 1개면 `single_retrieval`

## 추가 함수 코드 단위 해석: `_dataset_hints`

이 함수는 LLM이 dataset을 명확히 못 골랐을 때, 질문 문장과 table catalog/domain 정보를 보고 dataset 후보를 찾습니다.

### 함수 input

```json
{
  "question": "오늘 DA공정 생산량 알려줘",
  "table_catalog": {
    "datasets": {
      "production": {
        "display_name": "Production",
        "keywords": ["생산", "생산량"]
      },
      "wip": {
        "display_name": "WIP",
        "keywords": ["재공", "wip"]
      }
    }
  },
  "domain": {
    "metrics": {}
  }
}
```

### 함수 output

```json
["production"]
```

### 핵심 코드 해석

```python
normalized_question = _normalize_text(question)
found: list[str] = []
```

질문을 비교하기 쉬운 형태로 정규화하고, 찾은 dataset key를 담을 list를 만듭니다.

```python
for dataset_key, dataset in _dataset_configs(table_catalog).items():
```

table catalog 안의 dataset을 하나씩 확인합니다. 예를 들어 `production`, `wip`, `target`을 차례로 봅니다.

```python
candidates = [
    dataset_key,
    dataset.get("display_name", ""),
    dataset.get("description", ""),
    *DEFAULT_DATASET_KEYWORDS.get(str(dataset_key), []),
    *_as_list(dataset.get("keywords")),
    *_as_list(dataset.get("aliases")),
    *_as_list(dataset.get("question_examples")),
]
```

이 dataset을 뜻할 수 있는 모든 단어 후보를 모읍니다.

- dataset key: `production`
- 표시 이름: `Production`
- 설명 문장
- 기본 keyword
- catalog에 등록한 keywords/aliases/question_examples

```python
if any(_normalize_text(item) and _normalize_text(item) in normalized_question for item in candidates):
    found.append(dataset_key)
```

후보 단어 중 하나라도 질문에 들어 있으면 해당 dataset을 찾은 것으로 봅니다. 예를 들어 `"생산량"`이 질문에 있으면 `production`을 추가합니다.

```python
for _metric_key, metric in _matched_metrics(question, domain).items():
    if isinstance(metric, dict):
        found.extend(str(item) for item in _as_list(metric.get("required_datasets")))
```

질문이 metric을 말하고 있다면, metric에 등록된 `required_datasets`도 추가합니다. 생산달성률처럼 여러 dataset이 필요한 질문을 놓치지 않기 위한 코드입니다.

```python
return _unique_strings(found)
```

중복을 제거하고 dataset 목록을 반환합니다.

## 추가 함수 코드 단위 해석: `_filters_from_question`

이 함수는 질문 문장에서 공정, 공정 그룹, mode 같은 filter 조건을 rule 기반으로 추출합니다.

### 함수 input

```json
{
  "question": "어제 WB공정 DDR5 생산량 알려줘",
  "domain": {
    "process_groups": {
      "wb": {
        "aliases": ["WB공정", "W/B"],
        "processes": ["W/B1", "W/B2"]
      }
    }
  }
}
```

### 함수 output

```json
{
  "process_name": ["W/B1", "W/B2"],
  "mode": ["DDR5"]
}
```

### 핵심 코드 해석

```python
filters: Dict[str, Any] = {}
```

추출한 filter를 담을 빈 dict를 만듭니다.

```python
process_matches = re.findall(r"\b(?:D/A|DA|W/B|WB)\s*-?\s*\d+\b", question, flags=re.IGNORECASE)
```

질문에서 `D/A1`, `DA1`, `W/B2`, `WB2` 같은 구체 공정명을 정규식으로 찾습니다.

```python
for item in process_matches:
    text = re.sub(r"\s+", "", item.upper())
    if text.startswith("DA"):
        text = text.replace("DA", "D/A", 1)
    if text.startswith("WB"):
        text = text.replace("WB", "W/B", 1)
    normalized_processes.append(text)
```

사용자가 `DA1`처럼 써도 내부 표준인 `D/A1`로 바꿉니다. `WB1`도 `W/B1`로 바꿉니다.

```python
if normalized_processes:
    filters["process_name"] = _unique_strings(normalized_processes)
elif _contains_any(question, ["DA공정", "D/A공정", "DA process"]):
    filters["process_name"] = ["D/A1", "D/A2", "D/A3"]
elif _contains_any(question, ["WB공정", "W/B공정", "WB process"]):
    filters["process_name"] = ["W/B1", "W/B2"]
```

구체 공정명이 있으면 그것을 쓰고, `DA공정`, `WB공정`처럼 그룹만 말하면 그룹에 속한 공정 목록으로 확장합니다.

```python
groups = (domain or {}).get("process_groups") if isinstance((domain or {}).get("process_groups"), dict) else {}
```

MongoDB/domain JSON에 등록된 process group도 확인합니다.

```python
if any(_normalize_text(item) and _normalize_text(item) in _normalize_text(question) for item in aliases):
    processes = [str(item) for item in _as_list(group.get("processes")) if str(item).strip()]
    if processes and not filters.get("process_name"):
        filters["process_name"] = processes
```

질문이 domain에 등록된 alias와 매칭되면 해당 group의 processes를 filter로 넣습니다.

```python
modes = [token for token in ("DDR5", "LPDDR5", "HBM3", "HBM") if token.lower() in question.lower()]
if modes:
    filters["mode"] = _unique_strings(modes)
```

질문에 `DDR5`, `HBM3` 같은 mode 단어가 있으면 `mode` filter로 추가합니다.
