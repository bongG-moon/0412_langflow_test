# Langflow Local Manufacturing Project

이 프로젝트는 기존 LangGraph 기반 제조 분석 에이전트를
Langflow와 Streamlit에서 모두 사용할 수 있도록 정리한 로컬 프로젝트입니다.

핵심 방향은 아래와 같습니다.

- 코어 비즈니스 로직은 `manufacturing_agent`에 유지
- Langflow용 노드는 `custom_components`에 분리
- Langflow adapter/helper는 `langflow_version`에 정리
- 설명/가이드/이론/참고 문서는 모두 `docs/` 아래에 통합

## 빠른 시작

1. 의존성을 설치합니다.

```powershell
pip install -r requirements.txt
```

2. Langflow를 쓸 경우 환경 변수를 설정합니다.

```powershell
setx LANGFLOW_COMPONENTS_PATH "C:\Users\qkekt\Desktop\langflow_local_manufacturing_project\custom_components"
```

3. Streamlit을 쓸 경우 프로젝트 루트에서 실행합니다.

```powershell
streamlit run app.py
```

## 문서 안내

이제 프로젝트 문서는 모두 `docs/` 아래에서 봅니다.

### 구현/사용 문서

1. [docs/README.md](docs/README.md)
2. [docs/00_START_HERE.md](docs/00_START_HERE.md)
3. [docs/01_LANGFLOW_CONCEPT.md](docs/01_LANGFLOW_CONCEPT.md)
4. [docs/02_PROJECT_STRUCTURE.md](docs/02_PROJECT_STRUCTURE.md)

Langflow 캔버스/멀티턴/Streamlit 사용 문서를 바로 보고 싶다면 아래를 보면 됩니다.

- [docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md](docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md)
- [docs/07_LANGFLOW_CANVAS_SETUP.md](docs/07_LANGFLOW_CANVAS_SETUP.md)
- [docs/08_MULTITURN_CHAT_FLOW.md](docs/08_MULTITURN_CHAT_FLOW.md)
- [docs/09_STREAMLIT_APP.md](docs/09_STREAMLIT_APP.md)
- [docs/10_ADDITIONAL_READING.md](docs/10_ADDITIONAL_READING.md)
- [docs/11_DOMAIN_AND_USAGE_GUIDE.md](docs/11_DOMAIN_AND_USAGE_GUIDE.md)
- [docs/12_LANGFLOW_MIGRATION_ISSUES.md](docs/12_LANGFLOW_MIGRATION_ISSUES.md)

## 디렉토리 개요

```text
langflow_local_manufacturing_project/
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

각 디렉토리의 역할은 아래와 같습니다.

- `custom_components`
  - Langflow가 직접 읽는 커스텀 노드
- `manufacturing_agent`
  - 실제 제조 분석 코어 로직
- `langflow_version`
  - Langflow 전용 state/workflow adapter
- `docs`
  - 구현 설명, 사용 가이드, 이론, 참고 문서를 통합한 문서 루트
- `reference_materials`
  - 런타임에서 참조하는 자산 폴더
  - 현재는 주로 `domain_registry/entries` 같은 실행 자산이 들어 있음

## 현재 추천 사용 방식

### Langflow에서 빠르게 전체 실행

- `Manufacturing Agent`

### LangGraph와 유사한 압축 실행 플로우

- `Manufacturing State Input`
- `Resolve Manufacturing Request`
- `Run Manufacturing Branch`
- `Finish Manufacturing Result`

### 분기까지 드러내는 Langflow 플로우

- query mode 분기
- retrieval plan 분기
- single/multi post-processing 분기

### Streamlit UI

- [app.py](app.py)

## 참고

- 현재 retrieval 계층은 실제 제조 DB 연결이 아니라 mock/synthetic 데이터 기반입니다.
- Langflow 멀티턴 플로우는 세션 메모리 노드를 통해 이전 `chat_history/context/current_data`를 이어갑니다.
- 더 자세한 구조 설명은 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)와 [docs/README.md](docs/README.md)를 보면 됩니다.
