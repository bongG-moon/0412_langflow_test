# 프로젝트 구조 설명

이 문서는 디렉토리 단위로 프로젝트 구조를 설명합니다.

## 최상위 디렉토리

```text
langflow_local_manufacturing_project/
├─ .codex/
├─ custom_components/
├─ manufacturing_agent/
├─ langflow_version/
├─ docs/
├─ reference_materials/
├─ app.py
├─ requirements.txt
├─ PROJECT_STRUCTURE.md
└─ README.md
```

## `custom_components`

Langflow 캔버스에 보이는 커스텀 노드가 있습니다.

현재 제조 노드는 모두 아래에 모여 있습니다.

- `custom_components/manufacturing_nodes`

여기에는 아래 종류의 노드가 있습니다.

- 세션 메모리/초기화 노드
- 요청 해석 노드
- retrieval 준비 노드
- 실행 노드
- branch router 노드
- 결과 생성/merge 노드

## `.codex`

프로젝트 로컬 하네스와 스킬 파일이 있습니다.

### `harness/`

다른 도구에서도 같은 결과를 재현하기 위한 기준 하네스가 들어 있습니다.

### `skills/`

Codex CLI 등에서 재사용할 수 있는 프로젝트 로컬 스킬이 들어 있습니다.

## `manufacturing_agent`

실제 제조 분석 비즈니스 로직이 있는 코어 패키지입니다.

### `graph/`

LangGraph의 상태와 분기 구조를 가집니다.

### `services/`

실제 판단과 실행 로직이 모여 있습니다.

- 파라미터 추출
- query mode 판단
- retrieval planning
- single/multi retrieval 실행
- follow-up 분석
- 응답 생성

### `data/`

dataset registry와 retrieval 관련 구현이 있습니다.

### `analysis/`

LLM이 만든 pandas 코드를 안전하게 실행하는 분석 계층이 있습니다.

### `domain/`

도메인 지식, registry, value group, analysis rule 처리가 있습니다.

### `app/`

Streamlit UI helper가 있습니다.

## `langflow_version`

Langflow가 쓰기 쉬운 형태로 감싼 최소 helper 계층입니다.

주요 파일:

- `workflow.py`
- `component_base.py`

## `docs`

프로젝트 문서를 한 폴더로 통합한 문서 루트입니다.

### 번호 문서 체계

- `docs/00~09`
  - 구현과 사용 가이드
- `docs/10_ADDITIONAL_READING.md`
  - 추가 읽기 안내
- `docs/11_DOMAIN_AND_USAGE_GUIDE.md`
  - 도메인 등록, 질문 작성, 초보자용 확장 가이드 통합 문서
- `docs/12_LANGFLOW_MIGRATION_ISSUES.md`
  - Langflow 전환 과정의 오류와 수정 기록
- `docs/13_AGENT_HARNESS.md`
  - 다른 도구에서도 같은 결과를 재현하기 위한 하네스 기준 문서
- `docs/14_LOCAL_SKILLS.md`
  - 프로젝트 로컬 스킬 안내

즉, 지금은 설명 문서를 번호 체계 안으로 모으고, 별도 보조 문서는 최소화한 상태입니다.

## `reference_materials`

문서 폴더가 아니라 런타임 자산 폴더입니다.

- `domain_registry/entries/`
  - 사용자 정의 도메인 규칙 JSON

즉, 지금 기준으로:

- 설명/이론/참고 자료 = `docs/`
- 실제 실행 자산 = `reference_materials/`

로 구분하면 됩니다.
