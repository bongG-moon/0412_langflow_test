# 03. Build Intent Prompt 상세 설명

대상 코드: `langflow/data_answer_flow/03_build_intent_prompt.py`

이 노드는 사용자 질문, 이전 state, domain payload, domain index를 모아 LLM에게 보낼 intent 추출 prompt를 만든다. 실제 LLM 호출은 하지 않고, “LLM에게 무엇을 요청할지”만 문자열로 구성한다.

## 전체 역할

이 노드의 목적은 사용자 질문을 다음 형태의 JSON intent로 바꾸도록 LLM에게 지시하는 prompt를 만드는 것이다.

```json
{
  "request_type": "data_question | process_execution | unknown",
  "query_summary": "",
  "dataset_hints": [],
  "metric_hints": [],
  "required_params": {},
  "filters": {},
  "group_by": [],
  "sort": {
    "column_or_metric": "",
    "direction": "desc"
  },
  "top_n": null,
  "calculation_hints": [],
  "followup_cues": [],
  "confidence": 0.0
}
```

이 노드는 LLM 호출과 분리되어 있다. 그래서 prompt를 눈으로 확인하거나 수정하기 쉽고, LLM 모델을 바꿔도 prompt 생성 로직은 독립적으로 유지된다.

## import와 공통부

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 prompt 안에 schema와 domain summary를 JSON 문자열로 삽입하기 위해 사용한다.

Langflow 호환 공통부는 다른 노드와 동일하다.

이 노드는 다음 Langflow input 클래스를 사용한다.

```python
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
```

`MessageTextInput`은 사용자 질문처럼 짧은 텍스트를 받는 데 사용한다.

`DataInput`은 앞 노드의 `agent_state`, `domain_payload`, `domain_index`를 연결받는 데 사용한다.

## payload 추출

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

Langflow `Data`, dict, JSON text에서 dict payload를 꺼내는 함수다.

```python
if value is None:
    return {}
```

입력이 없으면 빈 dict를 반환한다.

```python
if isinstance(value, dict):
    return value
```

이미 dict면 그대로 반환한다.

```python
data = getattr(value, "data", None)
if isinstance(data, dict):
    return data
```

Langflow `Data` 객체면 `.data`를 반환한다.

```python
text = getattr(value, "text", None)
if isinstance(text, str):
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
```

`.text`가 JSON 문자열이면 파싱해서 dict로 반환한다. 실패하면 빈 dict다.

## unwrap 함수

```python
def _unwrap(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else payload
```

payload 안에 특정 key가 dict로 있으면 그 안쪽을 사용하고, 없으면 payload 자체를 사용한다.

예를 들어 다음 payload가 들어오면:

```json
{
  "state": {
    "turn_id": 1
  }
}
```

`_unwrap(payload, "state")`는 `{"turn_id": 1}`을 반환한다.

하지만 payload가 이미 state 본문이면 payload 자체를 반환한다.

## dict 압축 함수

```python
def _compact_dict(value: Any, limit: int = 4000) -> str:
```

dict나 list를 prompt에 넣기 좋은 JSON 문자열로 바꾸되, 너무 길면 자른다.

```python
text = json.dumps(value, ensure_ascii=False, indent=2)
```

한글을 유지하면서 보기 좋은 JSON 문자열로 변환한다.

```python
if len(text) <= limit:
    return text
```

제한 길이보다 짧으면 그대로 반환한다.

```python
return text[:limit] + "\n... truncated ..."
```

너무 길면 앞부분만 사용하고 잘렸다는 표시를 붙인다.

주의할 점은 domain JSON이 커지면 prompt에 전체가 들어가지 않을 수 있다는 것이다. 현재 domain summary는 `limit=12000`으로 호출된다.

## domain summary 생성

```python
def _domain_summary(domain: Dict[str, Any], domain_index: Dict[str, Any]) -> Dict[str, Any]:
```

LLM prompt에 넣을 domain 요약본을 만든다.

```python
datasets = {}
for key, dataset in domain.get("datasets", {}).items():
```

domain의 datasets를 순회한다.

```python
if not isinstance(dataset, dict):
    continue
```

dataset 정의가 dict가 아니면 건너뛴다.

```python
datasets[key] = {
    "display_name": dataset.get("display_name", key),
    "description": dataset.get("description", ""),
    "keywords": dataset.get("keywords", []),
    "required_params": dataset.get("required_params", []),
    "columns": dataset.get("columns", []),
}
```

LLM이 dataset을 판단하는 데 필요한 최소 정보를 넣는다.

`display_name`, `description`, `keywords`는 질문과 dataset을 매칭하는 데 중요하다.

`required_params`는 원본 데이터 조회 전에 필요한 필수 parameter를 판단하는 데 중요하다.

`columns`는 이후 pandas 전처리 의도를 잡는 데 도움이 된다.

```python
metrics = {}
for key, metric in domain.get("metrics", {}).items():
```

metric 정의를 순회한다.

```python
metrics[key] = {
    "display_name": metric.get("display_name", key),
    "aliases": metric.get("aliases", []),
    "required_datasets": metric.get("required_datasets", []),
    "formula": metric.get("formula", ""),
}
```

LLM이 계산 지표를 이해할 수 있도록 metric 이름, alias, 필요한 dataset, 계산식을 넣는다.

```python
return {
    "datasets": datasets,
    "metrics": metrics,
    "products": domain.get("products", {}),
    "process_groups": domain.get("process_groups", {}),
    "terms": domain.get("terms", {}),
    "alias_index": domain_index,
}
```

LLM에게 제공할 domain summary를 반환한다. 제품, 공정 그룹, 용어, alias index도 함께 제공한다.

## 핵심 함수: build_intent_prompt

```python
def build_intent_prompt(
    user_question: str,
    agent_state_payload: Any,
    domain_payload: Any,
    domain_index_payload: Any,
) -> str:
```

사용자 질문과 관련 payload들을 받아 최종 prompt 문자열을 만든다.

```python
state_payload = _payload_from_value(agent_state_payload)
agent_state = state_payload.get("agent_state")
if not isinstance(agent_state, dict):
    agent_state = _unwrap(state_payload, "state")
```

agent_state payload에서 실제 state dict를 꺼낸다. `agent_state` key가 없으면 `state` key 또는 payload 자체를 사용한다.

```python
domain_full_payload = _payload_from_value(domain_payload)
domain = domain_full_payload.get("domain")
if not isinstance(domain, dict):
    domain = domain_full_payload
```

domain payload에서 실제 `domain` dict를 꺼낸다. 없으면 payload 자체를 domain으로 본다.

```python
index_payload = _payload_from_value(domain_index_payload)
domain_index = index_payload.get("domain_index")
if not isinstance(domain_index, dict):
    domain_index = {}
```

domain index payload에서 `domain_index`를 꺼낸다. 없으면 빈 dict로 둔다.

```python
context = agent_state.get("context", {}) if isinstance(agent_state, dict) else {}
chat_history = agent_state.get("chat_history", []) if isinstance(agent_state, dict) else []
recent_history = chat_history[-6:] if isinstance(chat_history, list) else []
current_data = agent_state.get("current_data") if isinstance(agent_state, dict) else None
```

이전 대화 상태에서 prompt에 넣을 정보를 꺼낸다.

`recent_history`는 최근 6개만 넣는다. 너무 오래된 대화를 전부 넣으면 prompt가 길어지고 판단이 흐려질 수 있기 때문이다.

```python
schema = {
    ...
}
```

LLM이 반환해야 하는 JSON 구조를 명시한다.

```python
prompt = f"""You are a manufacturing data-analysis intent extractor.
...
"""
```

실제 prompt 문자열을 만든다.

prompt에는 다음 정보가 들어간다.

- LLM의 역할
- JSON만 반환하라는 지시
- request_type 분류 기준
- dataset, metric, required parameter, filter, group_by, sort, top_n 추출 지시
- 출력 JSON schema
- 현재 사용자 질문
- 최근 대화 이력
- 이전 context
- 현재 데이터 요약
- 제조 domain summary

```python
return prompt
```

최종 prompt 문자열을 반환한다.

## Component 입력

```python
MessageTextInput(name="user_question", ...)
```

현재 사용자 질문이다.

```python
DataInput(name="agent_state", ...)
```

`Session State Loader`의 출력이다.

```python
DataInput(name="domain_payload", ...)
```

`Domain JSON Loader.domain_payload`를 연결한다.

```python
DataInput(name="domain_index", ...)
```

`Domain JSON Loader.domain_index`를 연결한다.

## Component 출력

```python
Output(name="intent_prompt", display_name="Intent Prompt", method="build_prompt", types=["Data"])
```

출력은 `intent_prompt` 하나다. 이 output은 `build_prompt()`를 호출한다.

## 실행 메서드

```python
def build_prompt(self) -> Data:
```

Langflow에서 output 요청 시 실행된다.

```python
prompt = build_intent_prompt(
    getattr(self, "user_question", ""),
    getattr(self, "agent_state", None),
    getattr(self, "domain_payload", None) or getattr(self, "domain", None),
    getattr(self, "domain_index", None),
)
```

Component input 값을 읽어 핵심 함수에 전달한다.

`domain_payload`가 없을 때 `domain`을 fallback으로 보는 이유는 이전 구조와의 호환을 위한 방어 코드다.

```python
return _make_data({"intent_prompt": prompt, "prompt": prompt}, text=prompt)
```

prompt를 `intent_prompt`와 `prompt` 두 key로 넣어 반환한다.

`LLM JSON Caller`는 `prompt`, `intent_prompt`, `text` 등의 key에서 prompt를 찾을 수 있으므로 이 구조가 연결 안정성을 높인다.

## 다음 노드 연결

```text
Build Intent Prompt.intent_prompt -> LLM JSON Caller.prompt
```

## 학습 포인트

이 노드는 LLM을 직접 호출하지 않는다. Prompt Builder와 LLM Caller를 분리하면 prompt만 따로 검증할 수 있고, 같은 LLM Caller를 다른 prompt에도 재사용할 수 있다.

또한 domain payload와 domain index를 모두 prompt에 넣는다. payload는 LLM이 의미를 이해하는 데 좋고, index는 alias 후보를 명시적으로 보여주는 데 좋다.
