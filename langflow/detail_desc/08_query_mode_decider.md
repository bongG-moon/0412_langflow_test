# 08. Query Mode Decider 상세 설명

대상 코드: `langflow/data_answer_flow/08_query_mode_decider.py`

이 노드는 정규화된 데이터 질문이 “새 원본 데이터를 조회해야 하는 질문인지” 또는 “기존 데이터를 재사용해서 pandas 전처리만 다시 하면 되는 질문인지” 판단한다.

사용자가 말한 예시와 직접 연결되는 핵심 노드다.

예를 들어:

- 첫 질문: “오늘 A제품 생산량 알려줘” → 원본 데이터가 없으므로 `retrieval`
- 후속 질문: “이때 생산량이 제일 많은 공정 TOP5 알려줘” → 필수 조회 조건이 바뀌지 않았으므로 `followup_transform`
- 후속 질문: “어제 생산량은 얼마야?” → 필수 조회 parameter인 date가 바뀌므로 `retrieval`
- 후속 질문: “오늘 B제품 생산량 알려줘” → date는 같고 제품은 후처리 filter라면 `followup_transform`

## 전체 역할

입력으로 intent, agent_state, domain_payload를 받는다.

그리고 다음을 판단한다.

- 필요한 dataset이 무엇인가
- 현재 state에 재사용 가능한 source snapshot이 있는가
- 필요한 dataset이 현재 snapshot에 있는가
- dataset의 required_params가 기존 조회와 비교해 바뀌었는가
- 후처리 조건만 바뀐 것인가
- 새 조회가 필요한가, 기존 데이터 변환만 하면 되는가

출력 query_mode는 주로 세 가지다.

- `retrieval`: 새 원본 데이터 조회 필요
- `followup_transform`: 기존 데이터 재사용 후 pandas 전처리만 필요
- `clarification`: 정보 부족 또는 Phase 1 미지원

## 출력 구조

```json
{
  "query_mode_decision": {
    "query_mode": "retrieval",
    "reason": "No source snapshot or current data is available.",
    "needed_datasets": ["production"],
    "reuse_candidates": [],
    "required_param_changes": [],
    "missing_required_params": [],
    "effective_required_params": {}
  },
  "intent": {},
  "agent_state": {},
  "query_mode": "retrieval",
  "reason": "..."
}
```

`query_mode_decision` 안에도 decision이 있고, 바깥에도 decision key를 펼쳐 넣는다. 뒤 노드가 어느 방식으로 접근해도 편하게 하기 위한 구조다.

## import와 공통부

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 Data text 출력과 payload parsing에 사용한다. 나머지는 Langflow 호환과 타입 힌트용이다.

이 노드는 `DataInput`, `Output`, `Data`를 사용한다.

## payload 추출

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

입력값에서 dict payload를 꺼낸다.

`None`이면 `{}`.

dict면 그대로.

Langflow `Data`면 `.data`.

`.text`가 JSON 문자열이면 파싱한다.

실패하면 `{}`.

## list 변환과 중복 제거

```python
def _as_list(value: Any) -> list[Any]:
```

값을 list로 통일한다.

```python
def _unique(values: list[str]) -> list[str]:
```

문자열 list에서 빈 값과 중복을 제거한다.

```python
for value in values:
    value = str(value or "").strip()
    if not value or value in seen:
        continue
    seen.add(value)
    result.append(value)
```

각 값을 문자열로 바꾸고, 비어 있거나 이미 본 값이면 건너뛴다. 순서는 유지한다.

## intent, state, domain 추출

```python
def _get_intent(value: Any) -> Dict[str, Any]:
```

payload 안에 `intent`가 있으면 그것을 반환하고, 없으면 payload 자체를 반환한다.

`Request Type Router.data_question` branch payload는 다음처럼 `intent`를 내부에 가지고 있기 때문에 이 처리가 필요하다.

```json
{
  "route": "data_question",
  "intent": {},
  "agent_state": {}
}
```

```python
def _get_state(value: Any) -> Dict[str, Any]:
```

payload 안에서 `agent_state` 또는 `state`를 꺼낸다.

```python
def _get_domain(value: Any) -> Dict[str, Any]:
```

domain_payload에서 `domain`을 꺼낸다. 없으면 payload 자체를 domain으로 본다.

## 현재 source dataset 확인

```python
def _source_dataset_keys(agent_state: Dict[str, Any]) -> list[str]:
```

현재 state에서 재사용 가능한 source dataset key 목록을 찾는다.

```python
snapshots = agent_state.get("source_snapshots")
if isinstance(snapshots, dict) and snapshots:
    return list(snapshots.keys())
```

source_snapshots가 있으면 그 key들을 반환한다.

```python
current_data = agent_state.get("current_data")
if isinstance(current_data, dict):
    return [str(item) for item in _as_list(current_data.get("source_dataset_keys"))]
```

snapshot이 없으면 current_data 안의 source_dataset_keys를 fallback으로 본다.

```python
return []
```

둘 다 없으면 재사용 가능한 dataset이 없는 상태다.

## 이전 required parameter 조회

```python
def _snapshot_required_params(agent_state: Dict[str, Any], dataset_key: str) -> Dict[str, Any]:
```

특정 dataset을 이전에 어떤 required parameter로 조회했는지 찾는다.

```python
snapshots = agent_state.get("source_snapshots")
if isinstance(snapshots, dict):
    snapshot = snapshots.get(dataset_key)
    if isinstance(snapshot, dict) and isinstance(snapshot.get("required_params"), dict):
        return snapshot["required_params"]
```

source snapshot에 저장된 required_params를 우선 사용한다.

```python
context = agent_state.get("context")
if isinstance(context, dict):
    last_required = context.get("last_required_params")
    if isinstance(last_required, dict) and isinstance(last_required.get(dataset_key), dict):
        return last_required[dataset_key]
```

snapshot에 없으면 context의 last_required_params를 fallback으로 사용한다.

```python
return {}
```

없으면 빈 dict다.

## metric에 필요한 dataset 계산

```python
def _metric_required_datasets(intent: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
```

intent의 metric_hints를 보고 해당 metric이 필요로 하는 dataset 목록을 가져온다.

```python
for metric_key in _as_list(intent.get("metric_hints")):
    metric = domain.get("metrics", {}).get(str(metric_key), {})
    if isinstance(metric, dict):
        datasets.extend([str(item) for item in _as_list(metric.get("required_datasets"))])
```

예를 들어 생산 달성율 metric이 `production`, `target`을 요구하면 두 dataset을 반환한다.

## 필요한 dataset 계산

```python
def _needed_datasets(intent: Dict[str, Any], domain: Dict[str, Any], agent_state: Dict[str, Any]) -> list[str]:
```

이번 질문 처리에 필요한 dataset 목록을 결정한다.

```python
datasets = []
datasets.extend([str(item) for item in _as_list(intent.get("required_datasets"))])
datasets.extend([str(item) for item in _as_list(intent.get("dataset_hints"))])
datasets.extend(_metric_required_datasets(intent, domain))
```

intent에 이미 들어 있는 required_datasets, dataset_hints, metric 기반 required_datasets를 모두 합친다.

```python
datasets = _unique([item for item in datasets if item in domain.get("datasets", {})])
```

domain에 실제 정의된 dataset만 남기고 중복 제거한다.

```python
if not datasets and intent.get("followup_cues"):
    datasets = _source_dataset_keys(agent_state)
```

명시 dataset은 없지만 후속 질문 cue가 있으면 기존 source dataset을 이어받는다.

```python
return datasets
```

최종 필요한 dataset 목록을 반환한다.

## 후처리 변경 여부

```python
def _has_post_processing_change(intent: Dict[str, Any]) -> bool:
```

새 원본 조회 없이 pandas 전처리 단계에서 처리할 수 있는 조건이 있는지 본다.

```python
return bool(
    intent.get("filters")
    or intent.get("filter_expressions")
    or intent.get("group_by")
    or intent.get("sort")
    or intent.get("top_n")
    or intent.get("calculation_hints")
    or intent.get("followup_cues")
)
```

필터, 그룹화, 정렬, top N, 계산 힌트, 후속 질문 cue가 있으면 후처리 의도가 있다고 본다.

## 명시적 새 조회 요청

```python
def _explicit_fresh_request(intent: Dict[str, Any]) -> bool:
```

사용자가 명시적으로 새로 조회하라고 했는지 확인한다.

```python
summary = " ".join(
    [
        str(intent.get("query_summary") or ""),
        " ".join([str(item) for item in _as_list(intent.get("raw_terms"))]),
    ]
)
```

query_summary와 raw_terms를 합쳐 검색 대상 문자열을 만든다.

```python
fresh_tokens = ("새로 조회", "다시 조회", "fresh retrieval", "reload")
return any(token in summary.lower() for token in fresh_tokens)
```

현재 코드에서는 일부 한글 token이 깨져 보일 수 있다. 의도는 “새로 조회”, “다시 조회” 같은 표현을 잡는 것이다.

## 핵심 함수: decide_query_mode

```python
def decide_query_mode(intent_value: Any, state_value: Any, domain_value: Any) -> Dict[str, Any]:
```

query mode 판단의 핵심 함수다.

```python
intent_payload = _payload_from_value(intent_value)
intent = _get_intent(intent_value)
agent_state = _get_state(state_value)
```

입력에서 intent와 state를 꺼낸다.

```python
if not agent_state and isinstance(intent_payload.get("agent_state"), dict):
    agent_state = intent_payload["agent_state"]
elif not agent_state and isinstance(intent_payload.get("state"), dict):
    agent_state = intent_payload["state"]
```

agent_state 입력이 따로 없더라도 router branch payload 안에 agent_state가 있으면 그것을 사용한다.

```python
domain = _get_domain(domain_value)
snapshots = agent_state.get("source_snapshots") if isinstance(agent_state.get("source_snapshots"), dict) else {}
current_data = agent_state.get("current_data")
available_sources = _source_dataset_keys(agent_state)
needed = _needed_datasets(intent, domain, agent_state)
requested_params = intent.get("required_params") if isinstance(intent.get("required_params"), dict) else {}
context = agent_state.get("context") if isinstance(agent_state.get("context"), dict) else {}
```

판단에 필요한 기본 값들을 정리한다.

`available_sources`는 현재 재사용 가능한 dataset이다.

`needed`는 이번 질문에 필요한 dataset이다.

`requested_params`는 이번 질문에서 추출된 필수 조회 parameter다.

```python
reasons = []
changes = []
missing = []
effective_required_params = {}
reuse_candidates = []
```

판단 결과 설명, 변경된 parameter, 누락 parameter, 실제 사용할 parameter, 재사용 후보를 담을 리스트와 dict다.

## process_execution 처리

```python
if intent.get("request_type") == "process_execution":
    return {
        "query_mode": "clarification",
        "reason": "Request was classified as process_execution; data query mode is not applicable in Phase 1.",
        ...
    }
```

프로세스 실행 요청은 Phase 1의 데이터 조회 mode 판단 대상이 아니므로 clarification으로 보낸다.

## 명시적 새 조회 처리

```python
if _explicit_fresh_request(intent):
    reasons.append("User explicitly requested a fresh retrieval.")
    return {
        "query_mode": "retrieval",
        ...
    }
```

사용자가 “새로 조회”를 요청하면 기존 데이터가 있어도 retrieval로 보낸다.

## 기존 데이터가 없는 경우

```python
if not snapshots and not current_data:
    reasons.append("No source snapshot or current data is available.")
    if not needed:
        reasons.append("No dataset has been identified yet; retrieval planning should decide the dataset.")
    return {
        "query_mode": "retrieval",
        ...
    }
```

처음 질문처럼 현재 재사용 가능한 데이터가 없으면 무조건 retrieval이다.

needed dataset도 아직 없다면, 이후 retrieval planning 단계가 dataset을 결정해야 한다는 이유를 추가한다.

## 필요한 dataset이 현재 없는 경우

```python
unavailable = [dataset for dataset in needed if dataset not in available_sources]
if unavailable:
    reasons.append(...)
    return {
        "query_mode": "retrieval",
        "reuse_candidates": [dataset for dataset in needed if dataset in available_sources],
        ...
    }
```

이번 질문에 필요한 dataset 중 현재 snapshot에 없는 것이 있으면 새 조회가 필요하다.

일부 dataset은 재사용 가능할 수 있으므로 reuse_candidates에 담는다.

## required parameter 비교

```python
for dataset_key in needed or available_sources:
```

필요한 dataset이 있으면 그것을 기준으로 보고, 없으면 현재 available source를 기준으로 본다.

```python
dataset = domain.get("datasets", {}).get(dataset_key, {})
required_names = [str(item) for item in _as_list(dataset.get("required_params"))] if isinstance(dataset, dict) else []
previous_params = _snapshot_required_params(agent_state, dataset_key)
effective_required_params[dataset_key] = {}
```

dataset 정의에서 required_params 이름을 가져오고, 이전 조회 parameter도 가져온다.

```python
requested_has_param = param_name in requested_params and requested_params.get(param_name) not in (None, "")
if requested_has_param:
    desired_value = requested_params.get(param_name)
elif previous_params.get(param_name) not in (None, ""):
    desired_value = previous_params.get(param_name)
else:
    ...
```

이번 질문에 parameter가 명시되어 있으면 그 값을 사용한다.

없으면 이전 snapshot parameter를 상속한다.

그것도 없으면 context의 last_required_params를 fallback으로 사용한다.

```python
if desired_value in (None, ""):
    missing.append({"dataset_key": dataset_key, "param": param_name})
    continue
```

필수 parameter 값을 끝내 찾지 못하면 missing에 기록한다.

```python
effective_required_params[dataset_key][param_name] = desired_value
```

이번 판단에서 실제로 사용할 parameter를 기록한다.

```python
previous_value = previous_params.get(param_name)
if requested_has_param and previous_value not in (None, "") and str(previous_value) != str(desired_value):
    changes.append(...)
```

이번 질문에서 명시한 parameter가 있고, 이전 값과 다르면 required parameter 변경으로 기록한다.

이 부분이 “어제 생산량은?” 같은 질문을 retrieval로 보내는 핵심이다. date가 required param이고 이전 date와 달라지면 새 조회가 필요하다.

```python
if dataset_key in available_sources and not changes:
    reuse_candidates.append(dataset_key)
```

dataset이 현재 사용 가능하고 parameter 변경이 없으면 재사용 후보로 넣는다.

## 변경이 있으면 retrieval

```python
if changes:
    reasons.append("At least one required retrieval parameter changed.")
    return {
        "query_mode": "retrieval",
        ...
    }
```

필수 조회 parameter가 하나라도 바뀌면 새 원본 조회가 필요하다.

## 필수 parameter가 누락된 경우

```python
if missing and not reuse_candidates:
    reasons.append("Required retrieval parameter(s) are missing and no reusable source exists.")
    return {
        "query_mode": "clarification",
        ...
    }
```

필수 parameter가 없고 재사용 가능한 데이터도 없으면 사용자에게 추가 정보를 물어야 한다.

## 후처리 변경이면 followup_transform

```python
if _has_post_processing_change(intent):
    reasons.append("Required retrieval parameters are unchanged; only post-processing intent changed.")
    return {
        "query_mode": "followup_transform",
        ...
    }
```

필수 조회 조건은 그대로이고 filter, group_by, sort, top_n 같은 후처리 조건만 바뀌었다면 기존 데이터를 재사용한다.

## fallback도 followup_transform

```python
reasons.append("Reusable source data exists and no required retrieval parameter changed.")
return {
    "query_mode": "followup_transform",
    ...
}
```

재사용 가능한 source data가 있고 required parameter 변경도 없으면 기본적으로 followup_transform이다.

## Component 입력

```python
DataInput(name="intent", display_name="Intent or Data Question Branch", ...)
```

`Normalize Intent With Domain.intent` 또는 `Request Type Router.data_question` branch를 받을 수 있다.

```python
DataInput(name="agent_state", ...)
```

`Session State Loader.agent_state`를 받을 수 있다. router branch payload에 agent_state가 이미 있으면 생략 가능하도록 코드가 방어되어 있다.

```python
DataInput(name="domain_payload", ...)
```

`Domain JSON Loader.domain_payload`를 연결한다.

## Component 출력

```python
Output(name="query_mode_decision", display_name="Query Mode Decision", method="build_decision", types=["Data"])
```

query mode 판단 결과를 출력한다.

## 실행 메서드

```python
def build_decision(self) -> Data:
```

Langflow output 요청 시 실행된다.

```python
decision = decide_query_mode(
    getattr(self, "intent", None),
    getattr(self, "agent_state", None),
    getattr(self, "domain_payload", None) or getattr(self, "domain", None),
)
```

Component input 값을 읽어 핵심 판단 함수에 전달한다.

```python
intent_payload = _payload_from_value(getattr(self, "intent", None))
agent_state = _get_state(getattr(self, "agent_state", None))
```

출력 payload에 넣기 위해 intent payload와 agent_state를 다시 정리한다.

```python
if not agent_state and isinstance(intent_payload.get("agent_state"), dict):
    agent_state = intent_payload["agent_state"]
```

agent_state 입력이 비어 있으면 router branch 안의 agent_state를 사용한다.

```python
output = {
    "query_mode_decision": decision,
    "intent": _get_intent(getattr(self, "intent", None)),
    "agent_state": agent_state,
    **decision,
}
```

최종 출력 payload를 만든다. `**decision`으로 decision key를 바깥에도 펼친다.

```python
return _make_data(output, text=json.dumps(decision, ensure_ascii=False))
```

payload를 Data로 반환한다. `.text`에는 decision만 JSON 문자열로 넣는다.

## 다음 노드 연결

현재 Phase 1은 여기까지 구현되어 있다. 이후 확장 시 예상 연결은 다음과 같다.

```text
Query Mode Decider.query_mode_decision -> Retrieval Planner
Query Mode Decider.query_mode_decision -> Pandas Transform Planner
```

`query_mode`가 `retrieval`이면 원본 데이터 조회 계획으로 가고, `followup_transform`이면 기존 데이터 기반 pandas 전처리로 가는 구조가 된다.

## 학습 포인트

이 노드는 멀티턴 데이터 분석의 핵심 판단 지점이다.

중요한 구분은 “필수 조회 parameter”와 “후처리 filter”다.

date처럼 dataset 조회 전에 반드시 필요한 값이 바뀌면 새 조회가 필요하다. 반면 product, process, top_n, group_by처럼 조회된 원본 데이터 안에서 처리 가능한 조건만 바뀌면 기존 데이터를 재사용한다.
