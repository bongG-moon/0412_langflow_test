# 에이전트 하네스 기준 문서

이 문서는 이 프로젝트의 제조 에이전트를 다른 실행 환경에서도 같은 결과로 재현하기 위한 기준 하네스를 설명합니다.
여기서 말하는 하네스는 단순 프롬프트가 아니라, 상태 계약, 분기 순서, 세션 유지, 검증 방식까지 포함한 실행 구조 전체를 뜻합니다.

## 1. 왜 하네스가 필요한가

이 프로젝트는 이미 아래 여러 실행 방식이 공존합니다.

- LangGraph 코어 실행
- Langflow 분기 가시형 플로우
- Streamlit UI

여기에 Codex CLI나 다른 도구를 붙이더라도 결과가 같으려면,
각 도구가 제각각 판단하는 것이 아니라 같은 기준 하네스를 따라야 합니다.

## 2. 하네스의 핵심 원칙

1. 코어 비즈니스 로직은 가능하면 재사용한다.
2. 상태 구조를 바꾸지 않는다.
3. 분기 순서를 바꾸지 않는다.
4. 멀티턴에서는 `chat_history`, `context`, `current_data`를 반드시 유지한다.
5. 최종 payload 형식은 최대한 동일하게 유지한다.
6. 오류를 고치거나 개발 방향이 바뀌어 기준이 달라지면, 하네스 문서도 같은 턴에 함께 갱신한다.

## 3. 실제 하네스 파일 위치

프로젝트 로컬 하네스는 아래에 있습니다.

- [`.codex/harness/manufacturing-agent/HARNESS.md`](../.codex/harness/manufacturing-agent/HARNESS.md)
- [`.codex/harness/manufacturing-agent/references/state-contract.md`](../.codex/harness/manufacturing-agent/references/state-contract.md)
- [`.codex/harness/manufacturing-agent/references/routing-contract.md`](../.codex/harness/manufacturing-agent/references/routing-contract.md)
- [`.codex/harness/manufacturing-agent/references/validation-checklist.md`](../.codex/harness/manufacturing-agent/references/validation-checklist.md)

## 4. 어떤 순서로 따라야 하나

도구가 무엇이든 기본 순서는 같습니다.

1. 질문과 세션 상태를 읽는다.
2. 상태 계약에 맞는 입력 state를 만든다.
3. query mode를 판단한다.
4. retrieval 경로라면 dataset/job planning을 수행한다.
5. finish / single / multi 분기를 탄다.
6. direct response / post-analysis 분기를 탄다.
7. 최종 result payload를 만든다.
8. 멀티턴이면 세션 상태를 저장한다.

## 5. Codex CLI와 다른 도구에서의 사용 원칙

### Codex CLI

가장 좋은 방식은 하네스 파일과 스킬 파일을 프로젝트 로컬 `.codex/`에 두고,
Codex CLI가 이 저장소 맥락에서 그대로 읽게 하는 것입니다.

### 다른 도구

다른 도구는 `.codex/skills`를 자동으로 인식하지 않을 수 있습니다.
그 경우에도 아래 방식으로 같은 기준을 쓸 수 있습니다.

- 하네스 문서를 사람이 직접 참조
- `SKILL.md`를 system/developer instruction이나 task template처럼 재사용
- 필요하면 하네스 문서를 별도 프롬프트 자산으로 등록

즉, 파일 포맷은 Codex 친화적이지만 내용은 도구 중립적으로 유지하는 것이 목표입니다.

## 6. 언제 직접 로직을 재구현하면 안 되나

아래 상황에서는 새 도구 안에서 로직을 다시 짜지 말고 기존 엔트리포인트를 호출하는 편이 좋습니다.

- 코어 결과를 그대로 재현해야 할 때
- 후속 질문 동작까지 동일해야 할 때
- routing 차이가 생기면 안 될 때

권장 엔트리포인트:

- [manufacturing_agent/agent.py](../manufacturing_agent/agent.py)

Langflow 쪽은 단일 순차 wrapper를 다시 만드는 대신, 현재 문서화된 분기 가시형 노드 구조를 그대로 따르는 것을 기본 원칙으로 둡니다.

## 7. 관련 문서

- [03_BUILD_FLOW.md](03_BUILD_FLOW.md)
- [04_FUNCTION_GUIDE.md](04_FUNCTION_GUIDE.md)
- [08_MULTITURN_CHAT_FLOW.md](08_MULTITURN_CHAT_FLOW.md)
- [12_LANGFLOW_MIGRATION_ISSUES.md](12_LANGFLOW_MIGRATION_ISSUES.md)

## 8. 유지보수 원칙

하네스는 한 번 써놓고 끝나는 문서가 아닙니다.
작업 중 아래 변화가 생기면 함께 갱신해야 합니다.

- 반복 오류에서 공통 원인이 드러난 경우
- branch 판단 기준이 달라진 경우
- 세션 저장 방식이 달라진 경우
- 특정 도구 대응 방식이 표준으로 굳어진 경우

보통은 아래 순서로 갱신합니다.

1. 코드 수정
2. 필요하면 `docs/12_LANGFLOW_MIGRATION_ISSUES.md` 기록 추가
3. `.codex/harness/...` 기준 업데이트
4. `.codex/skills/...` 실행 지침 업데이트

## 9. 한 줄 요약

이 프로젝트의 하네스는 "같은 state, 같은 routing, 같은 세션 규칙, 같은 결과 payload"를 유지하게 만드는 기준 문서와 참조 파일 집합입니다.
