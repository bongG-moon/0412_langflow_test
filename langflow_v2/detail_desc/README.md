# detail_desc 문서 안내

이 폴더는 `langflow_v2` 노드별 상세 설명 문서입니다. 각 문서는 현재 구현 순서인 `00`부터 `26`까지의 Langflow 노드 번호와 맞춰져 있습니다.

## 읽는 순서

1. `00_state_memory_extractor.md` ~ `01_state_loader.md`: 이전 대화 상태와 현재 질문 준비
2. `02_mongodb_domain_loader.md` ~ `05_main_flow_filters_loader.md`: 도메인, 테이블 카탈로그, 표준 필터 정의 로드
3. `06_build_intent_prompt.md` ~ `09_intent_route_router.md`: intent prompt, LLM 호출, 계획 정규화, route 분기
4. `10_dummy_data_retriever.md` ~ `17_direct_result_adapter.md`: 데이터 조회와 조회 결과 branch 정리
5. `18_build_pandas_prompt.md` ~ `21_analysis_result_merger.md`: pandas 분석 계획, 실행, 결과 합치기
6. `22_mongodb_data_store.md` ~ `25_final_answer_builder.md`: 결과 저장, 최종 답변, next_state 생성
7. `26_state_memory_message_builder.md`: 다음 턴을 위한 state 저장 메시지 생성

## 현재 설계 기준

- `table_catalog`는 dataset/tool 메타데이터만 관리합니다. SQL과 DB별 파라미터 변환은 retriever 함수 책임입니다.
- `main_flow_filters`는 공통 의미 필터와 required param 정의를 관리합니다.
- `date` required param의 normalized format은 `YYYYMMDD`입니다.
- 실제 테이블 컬럼명이 다를 때는 `table_catalog.filter_mappings`로 표준 key를 컬럼에 매핑합니다.
- `domain.process_groups`는 `DA공정`, `WB공정` 같은 공정 그룹 확장을 담당합니다.

## 관련 문서

- 상위 README: `../README.md`
- 현재 flow 가이드: `../docs/02_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md`
- 예시 JSON: `../examples/main_flow_filters_example.json`, `../examples/table_catalog_example.json`, `../examples/mongodb_domain_items_example.json`
