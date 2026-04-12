# 로컬 스킬 가이드

이 문서는 프로젝트 로컬 `.codex/skills` 아래에 둔 스킬 파일이 무엇을 위한 것인지 설명합니다.
목표는 Codex CLI뿐 아니라 다른 도구에서도 같은 작업 절차를 재사용할 수 있게 만드는 것입니다.

## 1. 왜 로컬 스킬을 두는가

지금 이 프로젝트는 단순 코드 저장소가 아니라,
제조 에이전트를 어떻게 다뤄야 일관된 결과가 나오는지에 대한 작업 규칙도 중요합니다.

그 규칙을 코드 밖에서 재사용할 수 있도록 스킬 파일로 분리했습니다.

## 2. 실제 스킬 위치

- [`.codex/skills/manufacturing-agent-harness/SKILL.md`](../.codex/skills/manufacturing-agent-harness/SKILL.md)
- [`.codex/skills/manufacturing-domain-authoring/SKILL.md`](../.codex/skills/manufacturing-domain-authoring/SKILL.md)
- [`.codex/skills/langflow-migration-debug/SKILL.md`](../.codex/skills/langflow-migration-debug/SKILL.md)
- [`.codex/skills/manufacturing-regression-check/SKILL.md`](../.codex/skills/manufacturing-regression-check/SKILL.md)

## 3. 각 스킬의 역할

### `manufacturing-agent-harness`

- 다른 도구로 포팅하거나 래핑할 때
- 동일한 상태 계약과 분기 순서를 유지할 때
- Codex CLI에서 이 저장소 기준으로 제조 에이전트를 다룰 때

### `manufacturing-domain-authoring`

- 도메인 규칙, 별칭, 계산 규칙을 추가하거나 검토할 때
- 코드 수정 없이 해결 가능한지 먼저 판단할 때

### `langflow-migration-debug`

- Langflow 커스텀 노드가 로드되지 않거나
- 타입 메타, stale code, import 문제가 생겼을 때

### `manufacturing-regression-check`

- 어떤 도구에서든 변경 후 결과가 동일한지 확인할 때
- branch 선택, response, session 유지가 같은지 검증할 때

## 4. 다른 도구에서 어떻게 재사용할까

다른 도구가 `.codex/skills`를 자동 인식하지 않아도 괜찮습니다.
이 파일들은 전부 Markdown 기반이기 때문에 아래처럼 재사용할 수 있습니다.

- system/developer prompt에 내용 반영
- task template로 복사
- 내부 agent guideline 문서로 등록
- CI 검증용 체크리스트로 재사용

즉, 파일 위치는 Codex 친화적이지만 내용은 도구 중립적으로 유지했습니다.

## 5. 하네스와 스킬의 관계

- 하네스
  - 시스템 전체의 기준 계약
- 스킬
  - 반복 작업을 수행하는 실행 지침

즉, 하네스가 "무엇을 반드시 지켜야 하는가"라면,
스킬은 "어떤 작업을 어떤 순서로 처리할 것인가"에 가깝습니다.

## 6. 스킬도 같이 갱신해야 하는 경우

아래 상황에서는 코드만 바꾸고 끝내지 말고 스킬도 같이 점검해야 합니다.

- 새 오류 패턴 때문에 작업 절차가 달라진 경우
- Langflow 디버깅 체크 순서가 바뀐 경우
- 회귀 검증 질문 세트가 바뀐 경우
- 도메인 규칙 작성 방식이 달라진 경우

즉, 스킬은 단순 참고 메모가 아니라 현재 구현 기준의 실행 절차를 담는 파일입니다.

## 7. 관련 문서

- [13_AGENT_HARNESS.md](13_AGENT_HARNESS.md)
- [12_LANGFLOW_MIGRATION_ISSUES.md](12_LANGFLOW_MIGRATION_ISSUES.md)

## 8. 한 줄 요약

`.codex/skills`의 스킬 파일은 Codex CLI에 바로 쓰기 좋게 두되, 다른 도구에서도 같은 작업 절차를 재사용할 수 있도록 만든 프로젝트 로컬 실행 가이드입니다.
