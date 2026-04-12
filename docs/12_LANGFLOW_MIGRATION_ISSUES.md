# Langflow 전환 이슈와 수정 기록

이 문서는 기존 LangGraph 기반 프로젝트를 Langflow에서도 동작하도록 바꾸는 과정에서 실제로 겪었던 문제와 해결 방법을 정리한 기록입니다.
나중에 비슷한 문제를 다시 만나거나, 다른 프로젝트를 Langflow로 옮길 때 참고할 수 있도록 사례 중심으로 정리했습니다.

## 1. 정리 목적

이번 전환 작업에서 중요한 점은 단순히 Langflow 노드를 추가하는 것이 아니라,
기존 LangGraph 코어 로직을 최대한 유지한 채 Langflow가 읽을 수 있는 형태로 감싸는 것이었습니다.

이 과정에서 주로 아래 종류의 문제가 발생했습니다.

- 커스텀 노드 검색/로딩 실패
- 프로젝트 루트 import 실패
- 출력 타입 메타데이터 누락
- Langflow 저장 코드와 실제 파일 코드의 불일치
- 분기형 플로우의 최종 결과 병합 문제
- 멀티턴 세션 상태 유지 문제
- Playground에 과거 에러가 남아 보이는 문제

## 2. 이슈 1: 커스텀 노드는 보이는데 import가 실패함

### 변경하려던 것

- 기존 코어 패키지 `manufacturing_agent`를 유지한 채
- Langflow 커스텀 노드를 `custom_components` 아래에 두고 싶었음

### 증상

- Langflow에서 노드를 빌드하려고 할 때 import 오류 발생
- 대표적으로 `No module named 'langflow_version'` 같은 에러가 발생

### 원인

- Langflow는 커스텀 컴포넌트를 별도 로딩 방식으로 읽기 때문에,
  프로젝트 루트가 `sys.path`에 자동으로 들어오지 않음
- 게다가 커스텀 노드 폴더 이름이 코어 패키지 이름과 충돌하면 import 경로 해석이 더 불안정해짐

### 수정

- 커스텀 노드 폴더를 `custom_components/manufacturing_agent`에서
  `custom_components/manufacturing_nodes`로 분리
- 각 노드 파일 안에서 프로젝트 루트를 직접 찾는 `_ensure_repo_root()` 패턴 추가
- `LANGFLOW_COMPONENTS_PATH`, `MANUFACTURING_AGENT_PROJECT_ROOT` 환경 변수도 지원하도록 정리

### 결과

- Langflow가 커스텀 노드를 안정적으로 인식
- `langflow_version`, `manufacturing_agent` import가 정상 동작

### 교훈

- Langflow용 커스텀 노드 폴더 이름은 코어 패키지 이름과 겹치지 않는 것이 안전합니다.
- 프로젝트 루트를 자동으로 찾는 bootstrap 로직이 필요합니다.

## 3. 이슈 2: 노드가 아예 검색되지 않거나 load error로 스킵됨

### 증상

- Langflow 좌측 패널에서 노드가 안 보이거나
- 로그에서는 스캔했지만 `Skipping component ... (load error)`로 빠짐

### 확인 위치

- Langflow Desktop 로그:
  - `C:\\Users\\qkekt\\AppData\\Local\\com.LangflowDesktop\\logs\\langflow.log`

### 원인

- 일부 커스텀 노드 파일에 UTF-8 BOM이 들어 있었음
- Langflow가 내부적으로 텍스트 `exec` 기반으로 커스텀 코드를 읽는 경로에서 BOM이 문제를 일으킴
- top-level fallback import 구조도 Langflow 로더와 궁합이 좋지 않았음

### 수정

- `custom_components/manufacturing_nodes` 아래 파일들의 BOM 제거
- top-level 복잡한 fallback import 제거
- 각 노드 내부에서 필요한 시점에 `_ensure_repo_root()`를 호출하는 방식으로 단순화

### 결과

- 노드 검색이 정상화됨
- `manufacturing_nodes` 카테고리가 Langflow에서 안정적으로 표시됨

### 교훈

- Langflow 커스텀 노드는 일반 Python import만 생각하면 안 되고,
  Langflow의 동적 evaluator/exec 방식까지 고려해야 합니다.

## 4. 이슈 3: 첫 노드 출력이 `NoneType`으로 잡혀 연결이 안 됨

### 증상

- `Manufacturing State Input`의 출력이 `Output type: NoneType`으로 표시됨
- 다음 노드의 `Data` 입력 포트와 연결되지 않음

### 원인

- 노드가 실제로는 `Data` payload를 반환하지만,
  `Output(...)` 선언에서 타입 메타데이터가 빠져 있었음
- Langflow는 반환값만이 아니라 출력 포트 선언의 타입 메타를 보고 연결 가능 여부를 판단함

### 수정

- 출력 포트에 `types=["Data"], selected="Data"` 명시
- 동일한 패턴을 다른 커스텀 노드에도 적용

예:

```python
Output(
    name="initial_state",
    display_name="Initial State",
    method="build_state",
    types=["Data"],
    selected="Data",
)
```

### 결과

- `Initial State -> State` 연결이 정상화됨
- 분기형 노드들도 모두 `Data` 타입 기준으로 연결 가능

### 교훈

- Langflow에서는 실제 반환 타입과 출력 포트 메타데이터가 모두 중요합니다.

## 5. 이슈 4: `name 'ensure_project_root' is not defined`

### 증상

- 노드를 실행하면 아래와 같은 에러가 발생

```text
name 'ensure_project_root' is not defined
```

### 원인

두 가지가 겹쳤습니다.

1. Langflow가 저장된 노드 코드를 다시 실행할 때,
   top-level `try/except import` 구조가 기대대로 재구성되지 않음
2. 캔버스에 이미 올린 노드는 예전 코드 스냅샷을 계속 들고 있음

즉, 파일은 수정됐어도 캔버스 노드는 예전 코드 상태를 들고 실행하고 있었습니다.

### 수정

- 각 노드 파일 안에 `_ensure_repo_root()`를 직접 정의
- top-level 외부 bootstrap 의존도를 줄임
- `__file__`에 의존하지 않도록 변경
- 기존 캔버스 노드는 삭제 후 다시 추가해서 최신 코드 메타를 반영

### 결과

- `Manufacturing State Input` 등 첫 노드 실행이 정상화됨

### 교훈

- Langflow에서는 파일을 고친 뒤에도 캔버스에 있는 기존 노드가 자동 갱신되지 않을 수 있습니다.
- “코드 수정 + 노드 재추가”를 같이 생각해야 합니다.

## 6. 이슈 5: 분기 구조는 있는데 캔버스에는 직선 흐름처럼만 보임

### 증상

- 실제 코어 로직에는 follow-up / retrieval / single / multi / post-analysis 분기가 있는데
- Langflow 캔버스에서는 몇 개 노드가 내부에서 다 처리해 버려서 분기가 눈에 잘 안 보임

### 원인

- 초기 Langflow 어댑터는 “실행 결과 동일성”에 초점을 두었기 때문에
  분기 판단을 출력 포트가 아니라 노드 내부에서 처리하고 있었음

### 수정

분기형 라우터와 세분화 노드를 추가했습니다.

- `Route Manufacturing Query Mode`
- `Route Manufacturing Retrieval Plan`
- `Route Single Post Processing`
- `Route Multi Post Processing`
- `Build Single Retrieval Response`
- `Run Single Retrieval Post Analysis`
- `Build Multi Retrieval Response`
- `Run Multi Retrieval Analysis`

### 결과

- 캔버스에서 분기점이 눈에 보이는 구조로 전환
- 실행과 설명, 디버깅이 쉬워짐

### 교훈

- “기존 로직을 그대로 재현”하는 것과
  “분기를 시각적으로 드러내는 것”은 다른 요구사항입니다.
- 후자가 필요하면 router node를 별도로 설계해야 합니다.

## 7. 이슈 6: 분기형 플로우는 되는데 자동 멀티턴 챗봇처럼 이어지지 않음

### 증상

- 분해형 flow는 잘 동작하지만
- 다음 질문에서 이전 `chat_history`, `context`, `current_data`가 자동으로 이어지지 않음

### 원인

- 기존 분기형 flow는 디버그용으로는 충분했지만,
  세션 상태를 로드/저장하는 노드와 branch 결과를 다시 합치는 노드가 없었음

### 수정

아래 노드를 추가했습니다.

- `Manufacturing Session Memory`
  - 같은 노드를 두 번 사용
  - 앞쪽은 load, 뒤쪽은 save
- `Merge Final Manufacturing Result`
  - 여러 branch 끝의 `result` 중 실제 값이 있는 하나를 선택

### 결과

- 분기형 Langflow 플로우도 Playground에서 멀티턴 챗봇처럼 동작 가능
- 세션 상태는 `.langflow_session_store/` 아래 JSON으로 저장

### 교훈

- 디버그형 플로우를 운영형 멀티턴 플로우로 바꾸려면
  “세션 저장”과 “branch merge”가 별도 개념으로 필요합니다.

## 8. 이슈 7: Playground 상단에 예전 에러가 계속 보임

### 증상

- 현재는 정상 실행되는데도 Playground 상단에 과거 `Manufacturing State Input` 에러 카드가 계속 보임

### 원인

- 현재 실행 에러가 아니라, 이전 세션에서 남은 메시지 히스토리가 Playground에 그대로 표시된 것

### 수정

- 새 세션으로 테스트
- 또는 `Chat Input`의 `session_id`를 바꿔 새 세션처럼 분리

### 결과

- 현재 플로우 기준의 깨끗한 테스트 가능

### 교훈

- Playground 화면의 에러 카드가 항상 “현재 코드의 실패”를 의미하는 것은 아닙니다.
- 세션 히스토리와 실제 런타임 로그를 분리해서 봐야 합니다.

## 9. 이슈 8: 문서와 실제 구조가 자꾸 어긋남

### 증상

- 문서는 여러 폴더에 흩어져 있고
- 일부 문서는 예전 `core/...`, `reference_materials/docs/...` 같은 옛 구조를 가리킴

### 원인

- 구현이 빠르게 바뀌는 동안 설명 문서가 함께 정리되지 않았음

### 수정

- 문서 루트를 `docs/` 하나로 통합
- 번호 문서 체계 `00~12`로 정리
- 옛 경로 표기를 현재 구조 기준으로 갱신

### 결과

- 구현, 사용법, 추가 읽기, 문제 기록이 모두 한 곳에서 연결됨

### 교훈

- 마이그레이션 프로젝트에서는 코드 변경만큼 문서 구조 정리도 중요합니다.

## 10. 이번 전환에서 특히 중요했던 실제 수정 포인트

핵심만 다시 요약하면 아래와 같습니다.

1. 커스텀 노드 폴더 이름을 코어 패키지와 분리했다.
2. 각 노드 안에 `_ensure_repo_root()`를 넣어 프로젝트 루트를 찾게 했다.
3. Langflow 출력 포트에 `Data` 타입 메타를 명시했다.
4. 분기형 router node와 결과 노드를 추가해 캔버스 분기를 드러냈다.
5. `Manufacturing Session Memory`, `Merge Final Manufacturing Result`를 추가해 멀티턴을 가능하게 했다.
6. 문서를 `docs/` 한 곳으로 모으고 현재 구조 기준으로 다시 정리했다.

## 11. 다음 프로젝트에서도 바로 쓸 수 있는 체크포인트

LangGraph 기반 프로젝트를 Langflow로 옮길 때는 아래를 먼저 확인하면 좋습니다.

- 커스텀 노드 폴더 이름이 코어 패키지와 충돌하지 않는가
- 프로젝트 루트를 찾는 bootstrap 로직이 있는가
- 출력 포트 타입 메타가 명시돼 있는가
- 분기 로직을 포트로 노출할지 내부에서 감출지 결정했는가
- 멀티턴이 필요하다면 세션 저장/복원과 branch merge를 설계했는가
- Langflow 로그와 Playground 세션 히스토리를 구분해서 보고 있는가

## 12. 한 줄 요약

이번 Langflow 전환의 핵심은 “코어 LangGraph 로직은 유지하고, Langflow가 요구하는 로딩 방식, 타입 메타, 세션 구조, 분기 표현 방식에 맞게 어댑터와 노드를 다시 설계하는 것”이었습니다.
