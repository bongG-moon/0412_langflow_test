# 06. Build Intent Prompt

## 이 노드 역할

사용자 질문, 이전 상태, domain, table catalog, main flow filters를 모아서 intent 분류용 LLM prompt를 만드는 노드입니다.

## 왜 필요한가

LLM이 intent를 잘 판단하려면 질문 하나만 보면 부족합니다. 다음 정보가 함께 있어야 합니다.

- 이전 질문에서 조회한 현재 데이터가 있는지
- 어떤 dataset을 조회할 수 있는지
- `production`, `target` 같은 dataset이 어떤 tool과 연결되는지
- `process_name`, `mode`, `line` 같은 표준 필터 key가 무엇인지
- `date` required parameter는 어떤 형식으로 반환해야 하는지
- `달성률` 같은 metric이 어떤 dataset을 필요로 하는지

이 노드는 위 정보를 하나의 prompt로 모아서 다음 `LLM JSON Caller`가 호출할 수 있게 준비합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `state_payload` | `State Loader` 출력입니다. 현재 질문과 이전 state가 들어 있습니다. |
| `domain_payload` | MongoDB 또는 JSON Loader에서 읽은 domain 규칙입니다. 공정 그룹, metric, alias 등이 들어 있습니다. |
| `table_catalog_payload` | 조회 가능한 dataset과 tool 정보를 담은 catalog입니다. |
| `main_flow_filters_payload` | 표준 필터와 required parameter 정의입니다. 예: `process_name`, `mode`, `date`. |
| `reference_date` | `오늘`, `어제` 해석 기준일입니다. 테스트에서는 `2026-04-26`처럼 고정해서 넣을 수 있습니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | LLM JSON Caller에 넘길 prompt 문자열과 원본 context입니다. |

## 주요 함수 설명

- `_payload_from_value`: Langflow `Data`, dict, JSON 문자열 등에서 실제 dict를 꺼냅니다.
- `_unwrap_state`: `state_payload` 안에서 실제 `state`만 꺼냅니다.
- `_unwrap_domain`: `domain_payload` 안에서 실제 `domain`만 꺼냅니다.
- `_unwrap_catalog`: `table_catalog_payload` 안에서 실제 `table_catalog`만 꺼냅니다.
- `_unwrap_main_flow_filters`: `main_flow_filters_payload` 안에서 실제 `main_flow_filters`만 꺼냅니다.
- `_current_data_summary`: 이전 결과가 있을 때 전체 row 대신 row 수, 컬럼, data_ref 같은 작은 요약만 만듭니다.
- `build_intent_prompt`: LLM에게 줄 instruction, JSON schema, context를 합쳐 `prompt_payload`를 만듭니다.

## 예시

```json
{
  "state_payload": {
    "user_question": "어제 WB공정 생산달성률을 mode별로 알려줘",
    "state": {
      "session_id": "abc",
      "current_data": null
    }
  },
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "aliases": ["달성률", "달성율", "목표 대비"],
          "required_datasets": ["production", "target"]
        }
      }
    }
  },
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {"tool_name": "get_production_data"},
        "target": {"tool_name": "get_target_data"}
      }
    }
  },
  "main_flow_filters_payload": {
    "main_flow_filters": {
      "required_params": {
        "date": {"normalized_format": "YYYYMMDD"}
      },
      "filters": {
        "process_name": {},
        "mode": {}
      }
    }
  }
}
```

## 초보자 확인용

이 노드는 LLM을 호출하지 않습니다. LLM에게 줄 "시험지"를 만드는 역할입니다.

결과가 이상하면 먼저 `prompt_payload.prompt` 안에 다음 정보가 들어갔는지 확인하면 됩니다.

- 사용자 질문
- 현재 state와 current_data 요약
- table catalog의 datasets
- domain의 metrics와 process_groups
- main flow filters
- required parameter definitions
- reference_date

## 연결

```text
State Loader.state_payload
-> Build Intent Prompt.state_payload

MongoDB Domain Loader.domain_payload 또는 Domain JSON Loader.domain_payload
-> Build Intent Prompt.domain_payload

Table Catalog Loader.table_catalog_payload
-> Build Intent Prompt.table_catalog_payload

Main Flow Filters Loader.main_flow_filters_payload
-> Build Intent Prompt.main_flow_filters_payload

Build Intent Prompt.prompt_payload
-> LLM JSON Caller (Intent).prompt_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "state_payload": {
    "user_question": "오늘 DA공정 DDR5 생산 보여줘",
    "state": {
      "session_id": "abc",
      "current_data": null
    }
  },
  "domain_payload": {
    "domain": {
      "process_groups": {
        "DA": {
          "aliases": ["DA", "D/A", "DA공정"],
          "processes": ["D/A1", "D/A2", "D/A3"]
        }
      }
    }
  },
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {
          "keywords": ["생산", "실적", "production"],
          "tool_name": "get_production_data"
        }
      }
    }
  },
  "main_flow_filters_payload": {
    "main_flow_filters": {
      "required_params": {
        "date": {"normalized_format": "YYYYMMDD"}
      },
      "filters": {
        "process_name": {"operator": "in"},
        "mode": {"operator": "in"}
      }
    }
  },
  "reference_date": "2026-04-26"
}
```

### 출력 예시

```json
{
  "prompt_payload": {
    "prompt_type": "intent",
    "prompt": "You are the intent planner for a manufacturing data-analysis Langflow...",
    "state": {"session_id": "abc", "current_data": null},
    "domain": {"process_groups": {"DA": "..."}},
    "table_catalog": {"datasets": {"production": "..."}},
    "main_flow_filters": {"filters": {"process_name": "..."}},
    "user_question": "오늘 DA공정 DDR5 생산 보여줘",
    "reference_date": "2026-04-26"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"prompt": "..."})` | `{"prompt": "..."}` | Langflow 노드 출력은 `Data`로 감싸져 올 수 있으므로 실제 dict만 꺼냅니다. |
| `_unwrap_state` | `{"state_payload": {"state": {...}}}` | `{...}` | state wrapper를 벗기고 실제 state를 prompt에 넣기 위해 사용합니다. |
| `_unwrap_domain` | `{"domain_payload": {"domain": {...}}}` | `{...}` | domain wrapper를 벗기고 metric, process group 정보를 바로 쓰기 위해 사용합니다. |
| `_unwrap_catalog` | `{"table_catalog_payload": {"table_catalog": {...}}}` | `{...}` | dataset catalog만 꺼내 LLM에게 전달합니다. |
| `_unwrap_main_flow_filters` | `{"main_flow_filters_payload": {"main_flow_filters": {...}}}` | `{...}` | 표준 필터와 required parameter 정의를 꺼냅니다. |
| `_current_data_summary` | `{"data": [{"MODE": "DDR5"}]}` | `{"current_row_count": 1, "current_columns": ["MODE"]}` | 후속 질문 판단에 필요한 요약만 prompt에 넣습니다. |
| `build_intent_prompt` | state/domain/catalog/filter payload | `prompt_payload` | LLM에게 route, dataset, filter, pandas 필요 여부를 JSON으로 답하게 하는 prompt를 만듭니다. |
| `build_prompt` | Langflow 입력값 | `Data(data=prompt_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
각 입력 payload에서 실제 dict 추출
-> 현재 질문과 current_data 요약 생성
-> table catalog datasets 추출
-> main_flow_filters의 filters와 required_params 추출
-> LLM instruction과 예시 JSON schema 작성
-> prompt와 context를 함께 prompt_payload로 반환
```

## 함수 코드 단위 해석: `build_intent_prompt`

이 함수는 현재 질문과 주변 context를 합쳐 Intent LLM에게 줄 prompt를 만듭니다.

### 함수 input

```json
{
  "state_payload": {"user_question": "오늘 생산 보여줘", "state": {"session_id": "abc"}},
  "domain_payload": {"domain": {"metrics": {}}},
  "table_catalog_payload": {"table_catalog": {"datasets": {"production": {}}}},
  "main_flow_filters_payload": {"main_flow_filters": {"filters": {}, "required_params": {}}},
  "reference_date": "2026-04-26"
}
```

### 함수 output

```json
{
  "prompt_payload": {
    "prompt_type": "intent",
    "prompt": "You are the intent planner...",
    "state": {"session_id": "abc"},
    "domain": {"metrics": {}},
    "table_catalog": {"datasets": {"production": {}}},
    "main_flow_filters": {"filters": {}, "required_params": {}},
    "user_question": "오늘 생산 보여줘",
    "reference_date": "2026-04-26"
  }
}
```

### 핵심 코드 해석

```python
if isinstance(main_flow_filters_payload, str) and not reference_date:
    reference_date = main_flow_filters_payload
    main_flow_filters_payload = None
```

예전 호출 방식에서는 네 번째 인자로 `reference_date`가 들어올 수 있었습니다. 지금은 `main_flow_filters_payload`가 추가되었기 때문에, 문자열이 들어오면 예전 방식이라고 보고 기준일로 옮깁니다.

```python
state = _unwrap_state(state_payload)
domain = _unwrap_domain(domain_payload)
table_catalog = _unwrap_catalog(table_catalog_payload)
main_flow_filters = _unwrap_main_flow_filters(main_flow_filters_payload)
```

각 노드의 출력 wrapper를 벗기고 실제 dict만 꺼냅니다. 이 과정을 해두면 prompt 작성 코드가 단순해집니다.

```python
question = str(_payload_from_value(state_payload).get("user_question") or state.get("pending_user_question") or "")
```

현재 질문을 찾습니다. `user_question`이 없으면 state 안의 `pending_user_question`을 fallback으로 사용합니다.

```python
filter_defs = main_flow_filters.get("filters") if isinstance(main_flow_filters.get("filters"), dict) else {}
required_param_defs = main_flow_filters.get("required_params") if isinstance(main_flow_filters.get("required_params"), dict) else {}
```

표준 필터 정의와 required parameter 정의를 분리해서 prompt에 넣습니다. 여기서 `date.normalized_format = YYYYMMDD` 같은 정보가 LLM에게 전달됩니다.

```python
return {"prompt_payload": {...}}
```

prompt 문자열만 반환하지 않고 state/domain/catalog/filter context도 함께 반환합니다. 다음 `Normalize Intent Plan`이 LLM 결과를 보정할 때 이 context를 다시 사용하기 때문입니다.

## 추가 함수 코드 단위 해석: `_current_data_summary`

이 함수는 이전 턴의 `current_data`를 prompt에 넣기 좋은 요약 정보로 줄입니다.

```python
rows = current.get("data") if isinstance(current.get("data"), list) else []
data_ref = current.get("data_ref") if isinstance(current.get("data_ref"), dict) else {}
```

현재 데이터가 payload 안에 직접 들어 있는 경우와 MongoDB reference로 빠져 있는 경우를 모두 처리합니다.

```python
columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else data_ref.get("columns", [])
```

row가 있으면 첫 row의 key를 컬럼 목록으로 사용하고, row가 preview 없이 ref만 있으면 `data_ref.columns`를 사용합니다.

```python
"has_current_data": bool(rows) or bool(data_ref),
"current_row_count": current.get("row_count") or data_ref.get("row_count") or len(rows),
```

후속 질문 판단에 필요한 현재 데이터 존재 여부와 전체 row 수를 계산합니다.

```python
"current_source_required_params": current.get("source_required_params", current.get("retrieval_applied_params", {})),
"current_source_filters": current.get("source_filters", {}),
"current_source_column_filters": current.get("source_column_filters", {}),
```

이전 조회에 적용된 required param과 filter를 prompt에 전달합니다. 그래서 LLM이 "어제 WB공정은?" 같은 질문이 신규 조회인지 판단하는 근거를 갖습니다.

## 추가 함수 코드 단위 해석: `_unwrap_main_flow_filters`

이 함수는 Main Flow Filters Loader 출력에서 실제 설정 dict만 꺼냅니다.

```python
payload = _payload_from_value(value)
```

Langflow Data 객체나 dict 입력을 일반 payload로 바꿉니다.

```python
if isinstance(payload.get("main_flow_filters_payload"), dict):
    payload = payload["main_flow_filters_payload"]
```

Loader 출력처럼 `main_flow_filters_payload`로 감싸진 경우 내부로 한 단계 들어갑니다.

```python
return payload.get("main_flow_filters") if isinstance(payload.get("main_flow_filters"), dict) else payload
```

최종적으로 `main_flow_filters` dict를 반환합니다. 이미 dict 자체가 들어온 경우도 그대로 사용할 수 있게 합니다.
