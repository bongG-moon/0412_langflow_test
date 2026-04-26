# Langflow v2 Docs

이 폴더는 `langflow_v2` 구현을 이해하고 운영할 때 참고하는 보조 문서입니다.

## 문서 목록

1. `01_LANGFLOW_STANDALONE_IMPLEMENTATION_PLAN.md`
   - 초기 standalone Langflow custom component 구현 계획 문서입니다.
   - 일부 내용은 현재 구현과 다를 수 있으므로, 최종 연결 기준은 `../README.md`를 우선합니다.

2. `02_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md`
   - MongoDB item document 기반 domain 관리 방식과 현재 v2 main flow의 구현 패턴을 설명합니다.
   - 현재 노드 번호 00-26 기준으로 정리되어 있습니다.

3. `03_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`
   - Langflow Custom Component 작성 방식, 입력/출력 payload 패턴, 분기 설계에 대한 일반 가이드입니다.

4. `04_REQUIREMENTS_RISKS_WORKFLOW.md`
   - 요구사항, risk, 기능 단위 workflow를 정리한 참고 문서입니다.
   - 세부 노드 번호보다 기능 의도와 검증 관점 위주로 읽는 문서입니다.

## 최신 기준 문서

현재 flow를 실제로 연결하거나 수정할 때는 다음 순서로 보는 것을 권장합니다.

1. `../README.md`
2. `../detail_desc/README.md`
3. `02_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md`
4. `../registration_web/README.md`

## Canonical Example Files

- Domain item: `../examples/mongodb_domain_items_example.json`
- Table catalog: `../examples/table_catalog_example.json`
- Main flow filters: `../examples/main_flow_filters_example.json`
- Oracle DB config: `../examples/db_config_jsonish_example.txt`
