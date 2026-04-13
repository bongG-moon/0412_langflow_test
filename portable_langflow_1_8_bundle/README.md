# Langflow 1.8.0 Add Custom Node 전용 번들

이 폴더는 기존 repo 코드를 import 하지 못하고, Langflow UI의 `Add Custom Node`만 사용할 수 있는 환경을 위한 독립형 구현입니다.

## 목적

- `custom_components` 경로 마운트 없이 사용
- repo 내부 모듈 import 없이 사용
- Langflow `1.8.0` 기준으로 `Data`, `Message`, `tool_mode` 패턴에 맞게 작성
- 기본 노드와 조합해서 제조 분석용 멀티턴 플로우 구성
- 선택적으로 Agent/tool-calling 방식에서도 같은 기능 사용

## 전제 조건

- 런타임에서 파일 저장이 가능해야 합니다.
- Kubernetes 기준으로는 `securityContext.readOnlyRootFilesystem: false`가 필요합니다.
- 외부 패키지를 추가 설치하려면 네트워크 접근이 필요합니다.
- 사내 패키지 인덱스를 쓴다면 `UV_INDEX_URL` 환경변수를 사용합니다.

## 폴더 구성

- [FLOW_STANDALONE.md](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/FLOW_STANDALONE.md)
  - 기본 노드 + 커스텀 노드를 섞어 만드는 권장 플로우
- [FLOW_AGENT_TOOL_MODE.md](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/FLOW_AGENT_TOOL_MODE.md)
  - Agent/tool-calling 방식 권장 플로우
- [nodes/portable_dependency_bootstrap.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_dependency_bootstrap.py)
  - `uv pip install` 또는 `python -m pip install` 실행용 노드
- [nodes/portable_manufacturing_session_state.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_session_state.py)
  - 멀티턴 세션 로드
- [nodes/portable_manufacturing_request_router.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_request_router.py)
  - 파라미터 추출 + follow-up / retrieval 분기
- [nodes/portable_manufacturing_retrieval_planner.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_retrieval_planner.py)
  - dataset 계획 + early finish / jobs 분기
- [nodes/portable_manufacturing_tool_executor.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_tool_executor.py)
  - synthetic 제조 dataset 조회 실행
- [nodes/portable_manufacturing_result_composer.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_result_composer.py)
  - follow-up / retrieval 결과 생성
- [nodes/portable_manufacturing_merge_result.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_merge_result.py)
  - branch 결과를 하나로 합치기
- [nodes/portable_manufacturing_session_save.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_session_save.py)
  - 멀티턴 세션 저장 + Chat Output용 Message 생성
- [nodes/portable_manufacturing_toolbox.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_toolbox.py)
  - Agent에서 tool처럼 바로 붙일 수 있는 엔드투엔드 노드
- [nodes/portable_manufacturing_domain_rules_text.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_domain_rules_text.py)
  - 도메인 규칙을 Message 텍스트로 내보내는 노드
- [nodes/portable_manufacturing_domain_registry_json.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_domain_registry_json.py)
  - 추가 도메인 등록과 dataset/tool 규칙을 JSON(Data)로 내보내는 노드
- [nodes/portable_manufacturing_full_pipeline.py](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_manufacturing_full_pipeline.py)
  - 도메인 규칙 / registry / 분석 rule을 더 강하게 반영한 full-fidelity 파이프라인
- [FULL_FIDELITY_FLOW.md](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/FULL_FIDELITY_FLOW.md)
  - 도메인 강화형 portable flow 설명

## 추천 사용 방식

### 1. 기본 권장

- `Chat Input`
- `Message History`
- `Portable Manufacturing Session State`
- `Portable Manufacturing Request Router`
- `Portable Manufacturing Retrieval Planner`
- `Portable Manufacturing Tool Executor`
- `Portable Manufacturing Result Composer`
- `Portable Manufacturing Merge Result`
- `Portable Manufacturing Session Save`
- `Chat Output`

이 방식은 Langflow 기본 노드와 섞어 쓰기 좋고, 분기도 충분히 보입니다.

### 1-1. 도메인 강화형 권장

- `Chat Input`
- `Message History`
- `Portable Manufacturing Session State`
- `Portable Manufacturing Full Pipeline`
- `Portable Manufacturing Session Save`
- `Chat Output`

이 방식은 branch-visible 구조는 줄어들지만, registry와 분석 규칙 반영 수준은 더 높습니다.

### 2. Agent / Tool Calling 권장

- `Portable Manufacturing Domain Rules Text`
- `Portable Manufacturing Domain Registry JSON`
- built-in Agent
- `Portable Manufacturing Toolbox`

### 3. LLM High-Fidelity 권장

- [FLOW_LLM_HIGH_FIDELITY.md](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/FLOW_LLM_HIGH_FIDELITY.md)
- 핵심 노드
  - `Portable Manufacturing Domain Rules Text`
  - `Portable Manufacturing Domain Registry JSON`
  - `Portable Manufacturing Session State`
  - `Portable Manufacturing LLM Param Prompt`
  - `Portable Manufacturing LLM Param Parser`
  - `Portable Manufacturing LLM Retrieval Plan Prompt`
  - `Portable Manufacturing LLM Retrieval Plan Parser`
  - `Portable Manufacturing Tool Executor`
  - `Portable Manufacturing Sufficiency Prompt`
  - `Portable Manufacturing Sufficiency Parser`
  - `Portable Manufacturing Retry Replan`
  - `Portable Manufacturing Pandas Analysis Prompt`
  - `Portable Manufacturing Pandas Analysis Executor`
  - `Portable Manufacturing Merge Result`
  - `Portable Manufacturing Session Save`

이 경로는 기존 제조 LangGraph 코어의 핵심 구조를 portable 환경에서 가장 가깝게 재현하는 흐름입니다.

이 방식은 아래 역할을 분리해서 씁니다.

- `Portable Manufacturing Domain Rules Text`
  - system prompt 또는 Prompt Template 쪽으로 전달
- `Portable Manufacturing Domain Registry JSON`
  - toolbox의 `domain_registry` 입력으로 전달
- `Portable Manufacturing Toolbox`
  - 실제 tool call, dataset 선택, synthetic retrieval, analysis rule 적용 수행

## 중요한 구현 원칙

- 모든 커스텀 노드는 self-contained 입니다.
- 각 `.py` 파일은 다른 로컬 파일을 import 하지 않습니다.
- Langflow `Add Custom Node` 창에 파일 내용을 그대로 붙여넣는 것을 기준으로 작성했습니다.
- 제공 노드들은 기본적으로 Python 표준 라이브러리만 사용합니다.
- 따라서 설치 노드가 없어도 바로 테스트할 수 있습니다.
- 간편형과 도메인 강화형을 같이 제공하므로, 환경 제약과 정확도 요구사항에 따라 선택할 수 있습니다.

## 설치 노드가 필요한 경우

현재 제공 노드는 stdlib-only라서 설치 없이도 됩니다. 다만 아래 상황이면 [Portable Dependency Bootstrap](C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/portable_langflow_1_8_bundle/nodes/portable_dependency_bootstrap.py) 노드를 먼저 실행할 수 있습니다.

- pandas 같은 외부 패키지를 추가로 쓰고 싶을 때
- 사내 인덱스에서 패키지를 받아야 할 때
- `UV_INDEX_URL`을 이용해 `uv pip install`을 해야 할 때

## 세션 저장 위치

기본값은 현재 작업 디렉터리 아래 `.portable_langflow_sessions` 입니다.

필요하면 각 세션 관련 노드에서 `Storage Subdir` 값을 바꿔 분리할 수 있습니다.
