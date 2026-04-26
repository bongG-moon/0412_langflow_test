# Langflow v2 Docs

이 폴더는 Langflow v2 구현과 직접 관련된 설계, 구현, 학습 문서를 모아 둔 곳이다.

루트 `docs/`는 LangGraph 기반 제조 Agent와 공통 실행 계약을 중심으로 정리하고, Langflow v2 전용 문서는 이 폴더에서 관리한다.

## 문서 목록

1. `01_LANGFLOW_STANDALONE_IMPLEMENTATION_PLAN.md`
   - standalone 방식으로 Langflow custom component flow를 구현하기 위한 계획 문서이다.
2. `02_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md`
   - MongoDB item document 기반 domain 등록/관리 방식과 이 프로젝트 전용 v2 구현 패턴을 설명한다.
3. `03_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`
   - 특정 프로젝트에 묶이지 않는 Langflow Custom Component, 멀티턴, ReAct, 분기 설계 범용 가이드이다.
4. `04_REQUIREMENTS_RISKS_WORKFLOW.md`
   - 현재 v2 구현의 개발 요건, 예상 risk/대응 방안, 기능 단위 workflow를 정리한 문서이다.

## 함께 읽을 문서

- `../README.md`
  - v2 flow 전체 연결 지도와 노드 순서
- `../detail_desc/README.md`
  - v2 노드별 상세 설명 시작점
- `../registration_web/README.md`
  - PKG Domain Registry 웹 사용법
