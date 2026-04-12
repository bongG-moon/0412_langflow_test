# 프로젝트 구조 가이드

이 문서는 루트 기준으로 어떤 디렉토리가 어떤 책임을 가지는지 빠르게 설명합니다.

## 최상위 구조

```text
langflow_local_manufacturing_project/
├─ .codex/
├─ custom_components/
├─ manufacturing_agent/
├─ langflow_version/
├─ docs/
├─ reference_materials/
├─ .env.example
├─ requirements.txt
├─ app.py
├─ PROJECT_STRUCTURE.md
└─ README.md
```

## 디렉토리 역할

### `custom_components`

Langflow가 직접 읽는 커스텀 노드가 있습니다.

- 실제 노드 구현 위치:
  - `custom_components/manufacturing_nodes/`
- 역할:
  - 입력/출력 포트 정의
  - Langflow 캔버스용 branch 노드
  - core 로직을 호출하는 thin wrapper

### `.codex`

프로젝트 로컬 하네스와 스킬 파일이 있습니다.

- `harness/`
  - 다른 도구에서도 같은 결과를 재현하기 위한 기준 계약
- `skills/`
  - 반복 작업용 실행 지침

### `manufacturing_agent`

제조 에이전트의 실제 코어 로직이 있습니다.

- `graph/`
  - LangGraph state와 branch 연결
- `services/`
  - 파라미터 해석, query mode 판단, retrieval planning, 응답 생성
- `data/`
  - dataset registry와 retrieval
- `analysis/`
  - pandas 기반 후처리/분석
- `domain/`
  - 도메인 규칙과 registry
- `app/`
  - Streamlit UI helper
- `shared/`
  - 공통 유틸

### `langflow_version`

Langflow에서 재사용하기 쉽게 만든 workflow/state adapter가 있습니다.

- `workflow.py`
  - LangGraph와 유사한 순서로 단계 실행
- `component_base.py`
  - Langflow `Data` payload helper
- `components.py`
  - 통합 helper 모음

### `docs`

프로젝트 관련 문서를 한 곳에 모아 둔 문서 루트입니다.

- 번호 문서 체계:
  - `docs/00~09`
  - `docs/10_ADDITIONAL_READING.md`
  - `docs/11_DOMAIN_AND_USAGE_GUIDE.md`
  - `docs/12_LANGFLOW_MIGRATION_ISSUES.md`
  - `docs/13_AGENT_HARNESS.md`
  - `docs/14_LOCAL_SKILLS.md`

즉, 구현 설명부터 추가 읽기, 도메인/질문 가이드, 전환 이슈 기록, 하네스와 스킬 안내까지 모두 `docs/` 루트 아래의 번호 문서로 정리합니다.

### `reference_materials`

문서 폴더가 아니라, 런타임에서 참조하는 자산 폴더입니다.

- `domain_registry/entries/`
  - 사용자 정의 도메인 규칙 JSON

현재는 문서를 `docs/`로 통합했기 때문에, `reference_materials`는 주로 실행 자산 저장소 역할을 합니다.

## 어디에 수정해야 하는가

### Langflow 노드 UI/포트/분기 연결을 바꿀 때

- `custom_components/manufacturing_nodes`

### 실제 제조 분석 로직을 바꿀 때

- `manufacturing_agent`

### Langflow용 adapter/helper를 바꿀 때

- `langflow_version`

### 설명 문서/이론 문서/가이드를 바꿀 때

- `docs`

## 참고

보다 자세한 설명은 아래 문서를 보면 됩니다.

- [README.md](README.md)
- [docs/README.md](docs/README.md)
- [docs/02_PROJECT_STRUCTURE.md](docs/02_PROJECT_STRUCTURE.md)
