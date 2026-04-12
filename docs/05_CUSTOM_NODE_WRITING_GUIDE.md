# 커스텀 노드 작성 가이드

이 문서는 이 프로젝트 스타일에 맞는 Langflow 커스텀 노드를 어떻게 작성하면
좋은지 정리한 가이드입니다.

## 기본 원칙

이 프로젝트에서 좋은 커스텀 노드는 아래 특징을 가집니다.

- 노드 안에 비즈니스 로직을 길게 쓰지 않는다
- 코어 서비스 함수를 호출하는 얇은 래퍼에 가깝다
- 입력과 출력이 state 기반으로 일관된다
- LangGraph와 다른 분기 기준을 새로 만들지 않는다

## 추천 구조

커스텀 노드 파일은 보통 아래 구조를 따릅니다.

1. repo root를 `sys.path`에 넣는 helper
2. `Component` 상속 클래스 정의
3. `display_name`, `description`, `icon`, `name`
4. `inputs`, `outputs` 정의
5. 실제 실행 메서드 구현

## 입력과 출력 설계

### 입력은 가능하면 `state` 하나로 받는다

이 프로젝트에서는 대부분 아래 형식을 유지합니다.

- 입력
  - `state`
- 출력
  - `{"state": updated_state}`

이렇게 하면 노드 간 연결이 단순해지고, 디버깅도 쉬워집니다.

### 문자열 입력이 필요한 경우

초기 진입 노드처럼 실제 사용자 입력을 받는 경우에만 아래를 사용합니다.

- `MessageTextInput`
- `MultilineInput`

대표 예:

- `Manufacturing State Input`
- `Manufacturing Agent`

## 공통 helper 사용법

### `read_state_payload`

state 입력을 읽을 때는 가능하면 `langflow_version/component_base.py`의
`read_state_payload`를 사용합니다.

장점:

- `Data` 객체와 dict를 모두 받을 수 있습니다.
- `{"state": ...}` 래핑을 자동으로 벗깁니다.
- 노드마다 같은 unwrap 코드를 반복하지 않아도 됩니다.

### `make_data`

출력은 가능하면 `make_data`를 통해 반환합니다.

장점:

- Langflow 런타임이 있든 없든 최소한의 호환을 맞출 수 있습니다.

### `make_branch_data`

분기형 router node에서는 `make_branch_data`를 사용하는 편이 좋습니다.

장점:

- 선택된 branch만 payload를 내보낼 수 있습니다.
- 비선택 branch는 `None`으로 처리해 downstream 실행을 막을 수 있습니다.

## router node를 만들 때 규칙

분기 노드는 일반 노드보다 주의할 점이 있습니다.

### 1. `group_outputs=True` 사용

출력 포트를 실제 분기처럼 보여주려면 `Output(..., group_outputs=True)`가 필요합니다.

### 2. 분기 판단은 한 번만 계산

Langflow는 연결된 출력 메서드를 각각 호출할 수 있으므로,
분기 판단 로직은 캐시해 두는 편이 안전합니다.

예:

- `_cached` 필드 사용
- `_resolve()` 메서드에서 state와 route 계산

### 3. 비선택 branch는 값을 내보내지 않기

비선택 branch에서도 빈 dict를 반환하면 downstream이 실행될 수 있습니다.

따라서:

- 선택 branch만 `make_branch_data(True, ...)`
- 비선택 branch는 `None`

으로 처리하는 것이 좋습니다.

## 노드 안에 어떤 로직까지 넣어도 되는가

넣어도 되는 것:

- 입력 검증
- state unwrap
- 서비스 함수 호출
- status 문자열 설정
- 결과 state 조립

넣지 않는 것이 좋은 것:

- 복잡한 비즈니스 분기
- dataset 선택 규칙
- query mode 판단 기준의 재구현
- retrieval planning 기준의 재구현

## 좋은 예시 패턴

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

## status 문자열 작성 팁

좋은 status는 아래 조건을 만족하면 충분합니다.

- 지금 무엇을 했는지 짧게 보여준다
- 분기 결과가 있으면 함께 보여준다
- 지나치게 길지 않다

예:

- `Initial state built`
- `Query mode decided: retrieval`
- `Retrieval route: single_retrieval`

## 새 노드를 추가할 때 체크리스트

- 입력 포트 이름이 일관적인가
- 출력 payload가 `{"state": ...}` 형태를 지키는가
- `read_state_payload`를 사용할 수 있는가
- LangGraph 기준 함수를 재사용할 수 있는가
- inactive branch가 값을 내보내지 않는가
- 캔버스에서 display name이 이해하기 쉬운가
- 문서도 함께 갱신했는가
