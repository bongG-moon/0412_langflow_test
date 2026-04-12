# Langflow Local Manufacturing Project

이 프로젝트는 기존 LangGraph 기반 제조 분석 에이전트를 Langflow에서도
동일한 흐름으로 사용할 수 있도록 정리한 로컬 실험용 프로젝트입니다.

핵심 방향은 아래와 같습니다.

- 비즈니스 로직은 `manufacturing_agent`에 유지
- Langflow에서 보이는 노드는 `custom_components`에 배치
- Langflow 전용 state/workflow 어댑터는 `langflow_version`에 정리
- 필요하면 LangGraph의 분기 구조까지 Langflow 캔버스에서 드러나게 구성

## 빠르게 시작하기

1. `LANGFLOW_COMPONENTS_PATH`를 설정합니다.

```powershell
setx LANGFLOW_COMPONENTS_PATH "C:\Users\qkekt\Desktop\langflow_local_manufacturing_project\custom_components"
```

2. Langflow가 사용하는 Python 환경에 의존성을 설치합니다.

```powershell
pip install -r requirements.txt
```

3. Langflow Desktop을 완전히 종료한 뒤 다시 실행합니다.

4. 새 `Blank Flow`를 만들고 `manufacturing`으로 노드를 검색합니다.

## 문서 읽는 순서

전체 흐름을 이해하려면 아래 순서를 추천합니다.

1. [docs/README.md](docs/README.md)
2. [docs/00_START_HERE.md](docs/00_START_HERE.md)
3. [docs/01_LANGFLOW_CONCEPT.md](docs/01_LANGFLOW_CONCEPT.md)
4. [docs/02_PROJECT_STRUCTURE.md](docs/02_PROJECT_STRUCTURE.md)

바로 Langflow 캔버스에 올리고 싶다면 아래 문서부터 보는 편이 빠릅니다.

- [docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md](docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md)
- [docs/07_LANGFLOW_CANVAS_SETUP.md](docs/07_LANGFLOW_CANVAS_SETUP.md)

## 디렉터리 개요

```text
langflow_local_manufacturing_project/
├─ custom_components/
├─ manufacturing_agent/
├─ langflow_version/
├─ reference_materials/
├─ docs/
├─ .env.example
├─ requirements.txt
├─ PROJECT_STRUCTURE.md
└─ README.md
```

각 디렉터리의 역할은 아래와 같습니다.

- `custom_components`
  - Langflow가 직접 읽는 커스텀 노드
- `manufacturing_agent`
  - 실제 제조 분석 코어 로직
- `langflow_version`
  - Langflow 전용 state/workflow 헬퍼
- `reference_materials`
  - 도메인 규칙과 참고 자산
- `docs`
  - 프로젝트 설명 문서 모음

## 현재 추천 사용 방식

### 1. 가장 빠른 전체 실행 확인

- `Manufacturing Agent`

### 2. LangGraph와 유사한 압축형 실행 흐름

- `Manufacturing State Input`
- `Resolve Manufacturing Request`
- `Run Manufacturing Branch`
- `Finish Manufacturing Result`

### 3. 분기까지 드러내는 Langflow 흐름

- query mode 분기
- retrieval plan 분기
- single/multi 후처리 분기

이 구조는 아래 문서에 정리돼 있습니다.

- [docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md](docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md)
- [docs/07_LANGFLOW_CANVAS_SETUP.md](docs/07_LANGFLOW_CANVAS_SETUP.md)

## 참고 사항

- 현재 retrieval 계층은 실제 제조 DB 연결이 아니라 mock/synthetic 데이터 기반입니다.
- 멀티턴 follow-up을 Langflow에서 완전히 재현하려면 `result.current_data`를
  다음 입력의 `Current Data JSON`으로 다시 넘겨야 합니다.
- Langflow 런타임에 필요한 패키지가 없으면 노드는 보여도 로딩에 실패할 수 있습니다.

## 추가 구조 설명

보다 자세한 구조 설명은 아래 문서를 참고하면 됩니다.

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
