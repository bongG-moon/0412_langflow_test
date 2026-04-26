# 08. Intent Route Router

## 한 줄 역할

`intent_plan.route` 값을 보고 flow를 네 갈래로 나누는 분기 노드입니다.

## 네 가지 분기

| 출력 포트 | 의미 |
| --- | --- |
| `single_retrieval` | dataset 하나만 조회하면 되는 질문입니다. |
| `multi_retrieval` | 여러 dataset을 조회해야 하는 질문입니다. |
| `followup_transform` | 이전 결과를 다시 분석하는 후속 질문입니다. |
| `finish` | 조건 부족, 조회 불필요 등으로 바로 종료하거나 안내해야 하는 경우입니다. |

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Normalize Intent Plan`의 출력입니다. |

## 주요 함수 설명

- `_intent_payload`: 입력에서 실제 intent plan을 꺼냅니다.
- `_select_route`: route 값을 읽고 유효한 분기 이름으로 정리합니다.
- `route_intent`: 선택된 branch에는 실제 payload를, 나머지 branch에는 skipped payload를 보냅니다.

## skipped payload란?

선택되지 않은 출력도 Langflow 연결상 downstream 노드에 값이 들어갈 수 있습니다.
그래서 선택되지 않은 branch에는 다음처럼 표시합니다.

```json
{
  "skipped": true,
  "skip_reason": "route is multi_retrieval"
}
```

뒤 노드들은 `skipped: true`를 보면 아무 작업도 하지 않습니다.

## 초보자 포인트

이 노드가 있어야 Langflow 화면에서 분기가 눈에 보입니다.
즉, `single`, `multi`, `follow-up`, `finish`를 캔버스에서 명확히 확인하기 위한 노드입니다.

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
      {"dataset_key": "wip"}
    ]
  },
  "state": {
    "session_id": "abc"
  }
}
```

### 출력 예시

`multi_retrieval` output에는 실제 payload가 나갑니다.

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "retrieval_jobs": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
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

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_intent_payload` | `{"intent_plan": {...}}` 또는 plan 자체 | 표준 payload | 앞 노드가 어떤 감싸기 형태로 주든 `intent_plan` key가 있는 형태로 맞춥니다. |
| `_select_route` | `{"route": "multi_retrieval"}` | `"multi_retrieval"` | route, query_mode, retrieval_jobs 개수를 보고 실제 선택 branch를 정합니다. |
| `route_intent` | intent payload, `"single_retrieval"` | active 또는 skipped payload | 선택 branch만 실제 처리되고 나머지는 건너뛰게 만듭니다. |
| `_payload` | branch 이름 | routed payload | class method들이 공통으로 쓰는 내부 함수입니다. status도 여기서 갱신합니다. |
| `build_single_retrieval` 등 | 없음 | `Data(data=payload)` | Langflow canvas에 보이는 각 output port입니다. |

### 코드 흐름

```text
Normalize Intent Plan 결과 입력
-> route 결정
-> 각 output method가 자기 branch와 비교
-> 맞는 branch는 active payload
-> 아닌 branch는 skipped payload
```

### 초보자 포인트

이 노드는 실제 조회를 하지 않습니다. Langflow 화면에서 "어느 길로 갔는지"를 보이게 하기 위한 교차로 역할입니다.

## 함수 코드 단위 해석: `route_intent`

이 함수는 현재 branch가 선택된 branch인지 확인하고, 맞으면 payload를 통과시키고 아니면 `skipped` payload를 반환합니다.

### 함수 input

```json
{
  "intent_plan_value": {
    "intent_plan": {
      "route": "multi_retrieval",
      "retrieval_jobs": [{"dataset_key": "production"}, {"dataset_key": "wip"}]
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

현재 output port가 선택된 branch가 아니면 `skipped=True`로 반환합니다. 뒤 노드는 이 값을 보고 실제 처리를 하지 않습니다.

```python
routed = deepcopy(payload)
routed["selected_route"] = selected
routed["branch"] = branch
return routed
```

현재 output port가 선택된 branch라면 원래 payload를 복사해서 통과시킵니다. 원본을 직접 수정하지 않으려고 `deepcopy`를 사용합니다.
