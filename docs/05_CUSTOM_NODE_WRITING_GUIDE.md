# 커스텀 노드 작성 가이드

이 문서는 현재 프로젝트 스타일에 맞는 Langflow 커스텀 노드를 어떻게 작성하면 좋은지 정리한 가이드입니다.

## 기본 원칙

- 비즈니스 로직은 `manufacturing_agent/`에 둡니다.
- Langflow 노드는 얇은 wrapper로 유지합니다.
- 가능한 한 `state` 기반으로 연결합니다.
- 현재 프로젝트 기준 Langflow 노드는 분기 가시형 구조를 우선합니다.

## 현재 기준으로 주로 만드는 노드

- 세션 메모리 노드
  - `Manufacturing Session Memory`
- 상태 해석 노드
  - `Extract Manufacturing Params`
  - `Decide Manufacturing Query Mode`
- 계획/실행 노드
  - `Plan Manufacturing Datasets`
  - `Build Manufacturing Jobs`
  - `Execute Manufacturing Jobs`
- 분기 노드
  - `Route Manufacturing Query Mode`
  - `Route Manufacturing Retrieval Plan`
  - `Route Single Post Processing`
  - `Route Multi Post Processing`
- 결과 조립 노드
  - `Build Single Retrieval Response`
  - `Run Single Retrieval Post Analysis`
  - `Build Multi Retrieval Response`
  - `Run Multi Retrieval Analysis`
  - `Merge Final Manufacturing Result`

## 추천 구조

커스텀 노드는 보통 아래 흐름을 따릅니다.

1. repo root를 찾는 최소 helper
2. `Component` 상속 클래스 정의
3. `display_name`, `description`, `icon`, `name`
4. `inputs`, `outputs` 정의
5. 실제 실행 메서드 구현

## 입력과 출력 설계

### 가능한 한 `state` 하나로 받기

현재 프로젝트에서는 대부분 아래 패턴을 따릅니다.

- 입력
  - `state`
- 출력
  - `{"state": updated_state}`

이렇게 하면 캔버스 연결이 단순해지고, LangGraph state contract와도 맞추기 쉽습니다.

### 실제 텍스트 입력은 시작/저장 노드만

직접 문자열 입력을 받는 노드는 가능한 한 줄입니다.

- `Chat Input`
- `Manufacturing Session Memory`

나머지 노드는 대부분 앞 단계 state를 받아 처리합니다.

## 공통 helper 사용법

### `read_state_payload`

`langflow_version/component_base.py`의 `read_state_payload`를 사용하면
`Data` 객체와 dict를 모두 같은 방식으로 읽을 수 있습니다.

장점:

- `{"state": ...}` wrapper를 자동으로 벗깁니다.
- 노드마다 같은 unpack 로직을 반복하지 않아도 됩니다.

### `make_data`

일반 출력은 `make_data`로 감싸서 반환합니다.

### `make_branch_data`

router 노드는 `make_branch_data`를 사용합니다.

장점:

- 활성 branch만 payload를 보냅니다.
- 비활성 branch는 `None`으로 처리해 downstream 실행을 막습니다.

## router node 작성 규칙

분기 노드는 일반 노드보다 조금 더 엄격하게 맞추는 편이 좋습니다.

### 1. `group_outputs=True` 사용

분기 포트를 명확히 보이게 하려면 `Output(..., group_outputs=True)`를 사용합니다.

### 2. 분기 판단은 한 번만 계산

Langflow는 출력 메서드를 각각 호출할 수 있으므로, route 계산은 캐시해두는 편이 안전합니다.

예:

- `_cached` 필드 사용
- `_resolve()` 메서드에서 state와 route 계산

### 3. 비활성 branch는 값 전달 금지

비활성 branch에서 빈 dict를 반환하면 downstream이 실행될 수 있습니다.
현재 프로젝트에선 아래 규칙을 따릅니다.

- 활성 branch만 `make_branch_data(True, ...)`
- 비활성 branch는 `None`

## 노드 안에 넣을 로직과 빼둘 로직

노드 안에 둬도 되는 것:

- 입력 검증
- state unwrap
- 서비스 함수 호출
- status 문자열 설정
- 결과 state 조립

서비스 레이어에 둬야 하는 것:

- 복잡한 분기 규칙
- dataset 선택 규칙
- query mode 판단 근거
- retrieval planning 근거

## 좋은 패턴 예시

### 일반 실행 노드

```python
state = read_state_payload(getattr(self, "state", None))
if not state:
    self.status = "No input state; skipped"
    return None

updated = some_service_function(state)
return make_data({"state": updated})
```

### 분기 노드

```python
state, route = self._resolve()
return make_branch_data(route == "target_branch", {"state": state})
```

## status 문구 원칙

status는 아래 조건이면 충분합니다.

- 지금 무엇을 했는지 바로 보인다
- 분기 결과가 있으면 짧게 보인다
- 지나치게 길지 않다

예:

- `Session loaded: abc123`
- `Query mode decided: retrieval`
- `Retrieval route: single_retrieval`

## 새 노드 추가 체크리스트

- 입력 포트 이름이 직관적인가
- 출력 payload가 `{"state": ...}` 형태를 유지하는가
- `read_state_payload`를 사용하는가
- 코어 서비스 함수를 재사용하는가
- inactive branch가 값을 흘리지 않는가
- 캔버스에서 display name이 읽기 쉬운가
- 관련 문서를 함께 갱신했는가
