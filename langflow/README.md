# Standalone Langflow Components

이 폴더는 제조 데이터 분석 agent를 Langflow custom component로 나누어 구현한 공간이다.

현재 구현 범위는 두 가지다.

| Folder | Purpose |
| --- | --- |
| `data_answer_flow` | 사용자 질문에 대해 domain 로딩, intent 추출, query mode 판단, 데이터 조회, pandas 전처리, 최종 답변과 다음 state 생성을 수행하는 main flow |
| `domain_item_authoring_flow` | 자연어 domain 설명을 `products`, `process_groups`, `terms`, `datasets`, `metrics`, `join_rules` item으로 나누어 MongoDB에 저장하는 domain 작성 flow |
| `registration_web` | 도메인 지식과 테이블 카탈로그를 Streamlit 화면에서 작성, 검증, 저장하는 등록 웹 |

기본 코드 작성 이론은 아래 문서에 정리되어 있다.

```text
docs/09_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md
```

## 권장 사용 흐름

먼저 domain 작성 flow로 domain item을 저장한다.

```text
domain_item_authoring_flow
-> MongoDB Domain Item Saver.saved_items
```

기본 저장 위치:

```text
Database: datagov
Collection: manufacturing_domain_items
```

그 다음 main flow에서 저장된 active item 전체를 읽어온다.

```text
data_answer_flow / MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload
```

Streamlit 화면으로 등록하려면 아래 앱을 실행한다.

```powershell
streamlit run C:\Users\qkekt\Desktop\langflow_local_manufacturing_project\langflow\registration_web\app.py
```

Main Flow는 domain id를 입력하지 않는다. `manufacturing_domain_items` 컬렉션의 active item을 모두 읽어 `domain`, `domain_index`, `domain_prompt_context`로 합친다.

테이블/SQL/필수 parameter 정보는 domain과 분리해서 table catalog로 넣는다.

```text
data_answer_flow / Table Catalog JSON Input.table_catalog_json_payload
-> Table Catalog Loader.table_catalog_json_payload
-> Main Flow Context Builder.table_catalog_payload
```

SQL은 사람이 읽기 쉽게 `sql_template: """..."""` 블록으로 그대로 붙여넣을 수 있다. 예시는 아래 파일에 있다.

```text
langflow/data_answer_flow/examples/phase1_table_catalog_input_example.txt
```

## Data Answer Flow 순서

```text
00 Previous State JSON Input
-> 01 Session State Loader
02 MongoDB Domain Item Payload Loader
03 Table Catalog JSON Input
-> 04 Table Catalog Loader
-> 05 Main Flow Context Builder
-> 06 Build Intent Prompt
-> 07 LLM API Caller
-> 08 Parse Intent JSON
-> 09 Normalize Intent With Domain
-> 10 Request Type Router
-> 11 Query Mode Decider
-> 12 Retrieval Plan Builder
-> 13 Dummy Data Retriever or 14 OracleDB Data Retriever
-> 15 Analysis Base Builder
-> 16 Build Pandas Analysis Prompt
-> 07 LLM API Caller
-> 17 Parse Pandas Analysis JSON
-> 18 Execute Pandas Analysis
-> 19 Build Answer Prompt
-> 07 LLM API Caller
-> 20 Final Answer Builder
```

`07 LLM API Caller`는 canvas에 세 번 배치한다.

```text
Build Intent Prompt.prompt_payload
-> LLM API Caller.prompt
-> Parse Intent JSON.llm_result

Build Pandas Analysis Prompt.prompt_payload
-> LLM API Caller.prompt
-> Parse Pandas Analysis JSON.llm_output

Build Answer Prompt.prompt_payload
-> LLM API Caller.prompt
-> Final Answer Builder.answer_llm_output
```

각 LLM caller는 자체 `LLM API Key`, `Model Name`, `Temperature`를 가진다. 내부 구현은 현재 `langchain_google_genai.ChatGoogleGenerativeAI` 기반이며, 함수명과 노드명은 범용 LLM API 호출 의미로 유지한다.

## Retrieval 구조

`Retrieval Plan Builder`는 SQL을 만들지 않고 dataset별 tool 실행 계획만 만든다.

```json
{
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "params": {
    "date": "2026-04-22"
  },
  "post_filters": {
    "product": "A"
  }
}
```

`Dummy Data Retriever`와 `OracleDB Data Retriever`는 같은 tool 이름을 사용한다. Oracle 버전은 table catalog의 dataset별 `sql_template`, `db_key`, `bind_params`를 우선 사용하고, table catalog가 없을 때만 `14_oracledb_data_retriever.py` 내부 fallback SQL을 사용한다.

## Playground 출력

긴 JSON 대신 아래 output을 Chat Output에 연결한다.

```text
Final Answer Builder.answer_message
-> Chat Output
```

원본 table은 `manufacturing_flow_tables` 컬렉션에 저장되고, 최종 payload에는 table reference id와 preview만 들어간다.

## 세부 문서

Main Flow 연결 순서:

```text
langflow/data_answer_flow/README.md
```

노드별 상세 설명:

```text
langflow/data_answer_flow/detail_desc/
```

Domain item 작성 flow:

```text
docs/10_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md
```

수동 JSON fallback 예시:

```text
reference_materials/domain_json_examples/phase1_domain_input_example.json
```
