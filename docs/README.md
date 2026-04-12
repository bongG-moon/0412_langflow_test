# 문서 안내

이 폴더는 이 프로젝트의 유일한 문서 루트입니다.

- 구현 설명
- Langflow 구성 방법
- 멀티턴/Streamlit 사용 방법
- 이론/설계/체크리스트/참고 자료

를 모두 `docs/` 한 폴더 안에 모아 두었습니다.

## 추천 읽기 순서

처음 보는 경우에는 아래 순서를 추천합니다.

1. [00_START_HERE.md](00_START_HERE.md)
2. [01_LANGFLOW_CONCEPT.md](01_LANGFLOW_CONCEPT.md)
3. [02_PROJECT_STRUCTURE.md](02_PROJECT_STRUCTURE.md)
4. [03_BUILD_FLOW.md](03_BUILD_FLOW.md)
5. [04_FUNCTION_GUIDE.md](04_FUNCTION_GUIDE.md)
6. [05_CUSTOM_NODE_WRITING_GUIDE.md](05_CUSTOM_NODE_WRITING_GUIDE.md)
7. [06_BRANCH_VISIBLE_LANGFLOW_FLOW.md](06_BRANCH_VISIBLE_LANGFLOW_FLOW.md)
8. [07_LANGFLOW_CANVAS_SETUP.md](07_LANGFLOW_CANVAS_SETUP.md)
9. [08_MULTITURN_CHAT_FLOW.md](08_MULTITURN_CHAT_FLOW.md)
10. [09_STREAMLIT_APP.md](09_STREAMLIT_APP.md)
11. [10_ADDITIONAL_READING.md](10_ADDITIONAL_READING.md)
12. [11_DOMAIN_AND_USAGE_GUIDE.md](11_DOMAIN_AND_USAGE_GUIDE.md)
13. [12_LANGFLOW_MIGRATION_ISSUES.md](12_LANGFLOW_MIGRATION_ISSUES.md)
14. [13_AGENT_HARNESS.md](13_AGENT_HARNESS.md)
15. [14_LOCAL_SKILLS.md](14_LOCAL_SKILLS.md)

## 구현/사용 문서

- `00_START_HERE`
  - 프로젝트 전체를 빠르게 이해하기 위한 입문 문서
- `01_LANGFLOW_CONCEPT`
  - LangGraph와 Langflow의 관계 설명
- `02_PROJECT_STRUCTURE`
  - 디렉토리와 파일 역할 설명
- `03_BUILD_FLOW`
  - 어떤 흐름으로 구현을 쌓아가는지 설명
- `04_FUNCTION_GUIDE`
  - 주요 함수와 진입점 정리
- `05_CUSTOM_NODE_WRITING_GUIDE`
  - Langflow 커스텀 노드 작성 기준
- `06_BRANCH_VISIBLE_LANGFLOW_FLOW`
  - 분기 가시형 Langflow 구조 설명
- `07_LANGFLOW_CANVAS_SETUP`
  - 실제 Langflow 캔버스 배치/연결 가이드
- `08_MULTITURN_CHAT_FLOW`
  - 세션 메모리 기반 멀티턴 챗봇 플로우
- `09_STREAMLIT_APP`
  - Streamlit 실행 가이드
- `10_ADDITIONAL_READING`
  - 핵심 문서를 읽은 뒤 이어서 볼 추가 읽기 안내
- `11_DOMAIN_AND_USAGE_GUIDE`
  - 도메인 등록, 질문 작성, 초보자용 확장 가이드 통합 문서
- `12_LANGFLOW_MIGRATION_ISSUES`
  - Langflow 전환 과정에서 겪은 오류와 수정 사례 정리
- `13_AGENT_HARNESS`
  - 다른 도구에서도 같은 결과를 재현하기 위한 하네스 기준 문서
- `14_LOCAL_SKILLS`
  - 프로젝트 로컬 `.codex/skills` 스킬 안내

## 문서 정리 기준

- 핵심 구현/사용 문서는 `00~09`
- 추가 읽기 안내는 `10`
- 도메인 등록과 질문 사용 가이드는 `11`
- 전환 이슈와 트러블슈팅 기록은 `12`
- 하네스 기준 문서는 `13`
- 로컬 스킬 안내는 `14`

## 참고

- 실행 중 사용하는 실제 자산은 여전히 `reference_materials/` 아래에 있습니다.
- 문서만 `docs/`로 통합했고, 런타임 데이터인 `reference_materials/domain_registry/entries`는 그대로 유지합니다.
