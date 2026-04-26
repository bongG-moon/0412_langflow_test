# 09. Intent Route Router

## 이 노드 역할

`intent_plan.route` 값을 보고 flow를 네 갈래로 나누는 분기 노드입니다.

## 왜 필요한가

`Normalize Intent Plan`은 하나의 `intent_plan` 안에 최종 route를 적어 줍니다. 하지만 Langflow 화면에서는 route별로 다른 노드에 연결해야 합니다.

이 노드는 하나의 plan을 받아서 다음 네 갈래 output 중 하나만 active payload로 통과시키고, 나머지는 `skipped` payload로 표시합니다.

## 네 가지 분기

| 출력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | dataset 하나만 조회하면 되는 질문입니다. |
| `multi_retrieval` | 여러 dataset을 조회해야 하는 질문입니다. 예: 생산과 목표를 함께 써야 하는 달성률. |
| `followup_transform` | 이전 결과를 다시 분석하는 후속 질문입니다. |
| `finish` | 조회 없이 바로 끝내야 하는 경우입니다. 예: 필수 조건 부족, 안내 메시지. |

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Normalize Intent Plan`의 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | 선택 route가 `single_retrieval`이면 active payload를, 아니면 skipped payload를 반환합니다. |
| `multi_retrieval` | 선택 route가 `multi_retrieval`이면 active payload를, 아니면 skipped payload를 반환합니다. |
| `followup_transform` | 선택 route가 `followup_transform`이면 active payload를, 아니면 skipped payload를 반환합니다. |
| `finish` | 선택 route가 `finish`이면 active payload를, 아니면 skipped payload를 반환합니다. |

## 주요 함수 설명

- `_payload_from_value`: Langflow 입력을 dict로 꺼냅니다.
- `_intent_payload`: 입력이 wrapper 형태이든 plan 자체이든 표준 payload 형태로 맞춥니다.
- `_select_route`: plan의 `route`, `query_mode`, `retrieval_jobs` 개수를 보고 실제 route를 결정합니다.
- `route_intent`: 현재 output branch가 선택된 branch인지 확인하고 active 또는 skipped payload를 반환합니다.

## skipped payload란?

선택되지 않은 output에도 Langflow 연결상 값이 전달될 수 있습니다. 그래서 선택되지 않은 branch에는 다음처럼 `skipped: true`를 넣어 downstream 노드가 아무 작업도 하지 않게 합니다.

```json
{
  "skipped": true,
  "skip_reason": "selected route is multi_retrieval",
  "selected_route": "multi_retrieval",
  "branch": "single_retrieval"
}
```

## 초보자 확인용

이 노드는 실제 조회를 하지 않습니다. Langflow 화면에서 "어느 길로 갈지"를 보이게 만드는 교차로 역할입니다.

## 연결

```text
Normalize Intent Plan.intent_plan
-> Intent Route Router.intent_plan

Intent Route Router.single_retrieval
-> Dummy/Oracle Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Dummy/Oracle Retriever (Multi).intent_plan

Intent Route Router.followup_transform
-> Current Data Retriever.intent_plan

Intent Route Router.finish
-> Early Result Adapter.intent_plan
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "query_mode": "retrieval",
    "retrieval_jobs": [
      {"dataset_key": "production"},
      {"dataset_key": "target"}
    ]
  },
  "state": {
    "session_id": "abc"
  }
}
```

### 출력 예시

선택된 `multi_retrieval` output에는 실제 payload가 나갑니다.

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "retrieval_jobs": [
      {"dataset_key": "production"},
      {"dataset_key": "target"}
    ]
  },
  "selected_route": "multi_retrieval",
  "branch": "multi_retrieval"
}
```

선택되지 않은 `single_retrieval` output에는 skipped payload가 나갑니다.

```json
{
  "skipped": true,
  "skip_reason": "selected route is multi_retrieval",
  "selected_route": "multi_retrieval",
  "branch": "single_retrieval"
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"intent_plan": {...}})` | `{"intent_plan": {...}}` | Langflow 입력 wrapper를 벗깁니다. |
| `_intent_payload` | plan 자체 또는 `{"intent_plan": {...}}` | `{"intent_plan": {...}}` | 입력 형태가 달라도 route 판단 코드는 같은 구조를 보게 합니다. |
| `_select_route` | `{"route": "multi_retrieval"}` | `"multi_retrieval"` | route, query_mode, job 개수로 실제 branch를 결정합니다. |
| `route_intent` | intent payload, `"single_retrieval"` | active 또는 skipped payload | 현재 output port가 선택된 branch인지 판단합니다. |
| `_payload` | branch 이름 | routed payload | class output method들이 공통으로 쓰는 내부 함수입니다. |
| `build_single_retrieval` 등 | 없음 | `Data(data=payload)` | Langflow output port별 method입니다. |

### 코드 흐름

```text
Normalize Intent Plan 결과 입력
-> 실제 intent_plan 추출
-> route 결정
-> 각 output method가 자기 branch와 비교
-> 맞는 branch는 active payload 반환
-> 아닌 branch는 skipped payload 반환
```

## 함수 코드 단위 해석: `route_intent`

이 함수는 현재 branch가 선택된 branch인지 확인하고, 맞으면 payload를 통과시키고 아니면 skipped payload를 반환합니다.

### 함수 input

```json
{
  "intent_plan_value": {
    "intent_plan": {
      "route": "multi_retrieval",
      "retrieval_jobs": [
        {"dataset_key": "production"},
        {"dataset_key": "target"}
      ]
    }
  },
  "branch": "single_retrieval"
}
```

### 함수 output

선택 branch와 다르면:

```json
{
  "skipped": true,
  "skip_reason": "selected route is multi_retrieval",
  "selected_route": "multi_retrieval",
  "branch": "single_retrieval"
}
```

선택 branch와 같으면:

```json
{
  "intent_plan": {"route": "multi_retrieval"},
  "selected_route": "multi_retrieval",
  "branch": "multi_retrieval"
}
```

### 핵심 코드 해석

```python
payload = _intent_payload(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else {}
```

입력값에서 실제 intent plan을 꺼냅니다.

```python
selected = _select_route(plan)
```

plan의 route, query_mode, retrieval_jobs 개수를 보고 실제 선택 route를 계산합니다.

```python
if selected != branch:
    return {
        "skipped": True,
        "skip_reason": f"selected route is {selected}",
        ...
    }
```

현재 output port가 선택 route가 아니면 `skipped=True`로 반환합니다. 다음 노드는 이 값을 보고 실제 처리를 건너뜁니다.

```python
routed = deepcopy(payload)
routed["selected_route"] = selected
routed["branch"] = branch
return routed
```

현재 output port가 선택 route라면 원래 payload를 복사해서 넘깁니다. 원본을 직접 수정하지 않으려고 `deepcopy`를 사용합니다.
