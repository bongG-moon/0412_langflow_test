# 05. Build Intent Prompt

## 한 줄 역할

사용자 질문, 이전 상태, domain, table catalog를 모아 intent 분류용 LLM prompt를 만드는 노드입니다.

## intent란?

intent는 "사용자가 지금 무엇을 원하는가"를 구조화한 정보입니다.

예를 들면 다음을 판단합니다.

- 새 데이터 조회가 필요한가?
- 이전 결과를 이어서 분석하는 질문인가?
- 어떤 dataset이 필요한가?
- 날짜 같은 필수 조건이 있는가?
- pandas 후처리가 필요한가?

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `state_payload` | `State Loader` 출력입니다. 현재 질문과 이전 상태가 들어 있습니다. |
| `domain_payload` | 도메인 규칙입니다. MongoDB 또는 JSON Loader 중 하나를 연결합니다. |
| `table_catalog_payload` | dataset/tool catalog입니다. |
| `reference_date` | 테스트용 기준 날짜입니다. 비우면 현재 날짜 기준으로 해석합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | LLM JSON Caller에 넘길 prompt와 관련 context입니다. |

## 주요 함수 설명

- `_unwrap_state`: `state_payload`에서 실제 state를 꺼냅니다.
- `_unwrap_domain`: `domain_payload`에서 domain만 꺼냅니다.
- `_unwrap_catalog`: table catalog를 꺼냅니다.
- `_current_data_summary`: 이전 결과가 있을 때 row 수, 컬럼 등을 요약합니다.
- `build_intent_prompt`: LLM에게 보낼 instruction과 JSON schema를 만듭니다.

## 초보자 포인트

이 노드는 LLM을 호출하지 않습니다.
LLM이 읽을 prompt 문자열만 만듭니다.

즉, 역할은 "질문지를 잘 작성하는 노드"입니다.
실제 답안 작성은 다음 노드인 `LLM JSON Caller`가 합니다.

## 연결

```text
State Loader.state_payload
-> Build Intent Prompt.state_payload

Domain Loader.domain_payload
-> Build Intent Prompt.domain_payload

Table Catalog Loader.table_catalog_payload
-> Build Intent Prompt.table_catalog_payload

Build Intent Prompt.prompt_payload
-> LLM JSON Caller (Intent).prompt_payload
```

## Python 코드 상세 해석

### 입력 예시

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
          "aliases": ["달성률"],
          "required_datasets": ["production", "wip"]
        }
      }
    }
  },
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {"keywords": ["생산"]},
        "wip": {"keywords": ["재공"]}
      }
    }
  }
}
```

### 출력 예시

```json
{
  "prompt_payload": {
    "prompt": "You are an intent planner...\nReturn JSON only...",
    "state": {"session_id": "abc"},
    "domain": {"metrics": {"achievement_rate": "..."}},
    "table_catalog": {"datasets": {"production": "..."}},
    "reference_date": "2026-04-26"
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_unwrap_state` | `{"state_payload": {"state": {...}}}` | `{"state": {...}, "user_question": "..."}` | 앞 노드 출력이 한 겹 감싸져 있어도 실제 state를 꺼냅니다. |
| `_unwrap_domain` | `{"domain_payload": {"domain": {...}}}` | `{"metrics": {...}}` | prompt에 넣을 domain dict만 추출합니다. |
| `_unwrap_catalog` | `{"table_catalog_payload": {"table_catalog": {...}}}` | `{"datasets": {...}}` | prompt에 넣을 dataset 설명만 추출합니다. |
| `_current_data_summary` | `{"rows": [{"A": 1}]}` | `{"row_count": 1, "columns": ["A"]}` | 후속 질문 판단에 필요한 현재 데이터 요약만 만듭니다. 전체 row를 prompt에 많이 넣지 않기 위함입니다. |
| `build_intent_prompt` | state/domain/catalog | `prompt_payload` | LLM이 route, dataset, filter, pandas 필요 여부를 JSON으로 답하게 하는 지시문을 만듭니다. |
| `build_prompt` | Langflow 입력값 | `Data(data=prompt_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
State에서 질문과 이전 current_data 요약 추출
-> Domain에서 metric/alias/required_datasets 추출
-> Table catalog에서 dataset 설명 추출
-> LLM에게 반환해야 할 JSON schema와 판단 기준을 prompt로 작성
```

### 초보자 포인트

이 노드는 LLM을 호출하지 않습니다. LLM에게 줄 "시험지"를 만드는 노드입니다. 결과가 이상하면 먼저 이 노드의 `prompt` 안에 필요한 정보가 들어갔는지 보면 됩니다.

## 함수 코드 단위 해석: `build_intent_prompt`

이 함수는 현재 질문, 이전 state, domain, table catalog를 모아 Intent LLM에게 줄 prompt를 만듭니다.

### 함수 input

```json
{
  "state_payload": {
    "user_question": "오늘 DA공정 생산량 알려줘",
    "state": {
      "session_id": "abc",
      "current_data": null
    }
  },
  "domain_payload": {
    "domain": {
      "process_groups": {
        "da": {"aliases": ["DA공정"], "processes": ["D/A1", "D/A2"]}
      }
    }
  },
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {"keywords": ["생산량"], "tool_name": "get_production_data"}
      }
    }
  }
}
```

### 함수 output

```json
{
  "prompt_payload": {
    "prompt": "You are a manufacturing data intent planner...",
    "state": {"session_id": "abc", "current_data": null},
    "domain": {"process_groups": "..."},
    "table_catalog": {"datasets": "..."}
  }
}
```

### 핵심 코드 해석

```python
state_payload = _unwrap_state(state_payload)
domain = _unwrap_domain(domain_payload)
table_catalog = _unwrap_catalog(table_catalog_payload)
```

앞 노드 출력들은 `Data(data={...})`로 한 번 감싸져 있습니다. 이 세 줄은 그 안에서 실제 state, domain, catalog만 꺼냅니다.

```python
question = str(state_payload.get("user_question") or state.get("pending_user_question") or "").strip()
```

현재 사용자 질문을 찾습니다. `user_question`이 없으면 state에 저장된 `pending_user_question`을 사용합니다.

```python
current_data_summary = _current_data_summary(state.get("current_data") if isinstance(state.get("current_data"), dict) else {})
```

후속 질문 판단에 필요한 현재 데이터 요약을 만듭니다. 전체 row를 다 넣기보다 row 수, 컬럼, data_ref 같은 작은 정보만 prompt에 넣기 위한 준비입니다.

```python
prompt = f"""..."""
```

LLM에게 줄 instruction을 만듭니다. 이 prompt 안에는 다음 내용이 포함됩니다.

- 가능한 route 종류
- dataset 선택 기준
- filter를 JSON으로 반환하라는 지시
- pandas가 필요한 경우
- domain metric의 required_datasets를 반영하라는 지시
- 반드시 JSON만 반환하라는 지시

```python
return {
    "prompt_payload": {
        "prompt": prompt,
        "state": state,
        "domain": domain,
        "table_catalog": table_catalog,
        ...
    }
}
```

LLM 호출 노드는 prompt 문자열만 쓰지만, 뒤 normalizer는 state/domain/catalog도 다시 필요합니다. 그래서 prompt와 context를 같이 담아 보냅니다.
