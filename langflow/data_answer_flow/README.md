# Data Answer Flow

제조 데이터 질문에 답하기 위한 Langflow main flow custom node 모음이다.

현재 구조의 핵심은 세 가지다.

1. `MongoDB Domain Item Payload Loader`가 `manufacturing_domain_items` 컬렉션의 active item을 domain id 없이 전부 읽어온다.
2. `Main Flow Context Builder`가 사용자 질문, session state, domain payload를 한 번에 묶어 `main_context`로 전달한다.
3. `Table Catalog JSON Input -> Table Catalog Loader`가 table/SQL/required parameter 정보를 domain과 분리해서 전달한다.
4. LLM 호출은 Langflow built-in LLM이 아니라 custom `LLM API Caller` 노드를 사용한다. 각 LLM 노드마다 API key와 model을 입력한다.

## 권장 전체 순서

```text
00 Previous State JSON Input
-> 01 Session State Loader

02 MongoDB Domain Item Payload Loader
03 Table Catalog JSON Input
-> 04 Table Catalog Loader
-> 05 Main Flow Context Builder

05 Main Flow Context Builder
-> 06 Build Intent Prompt
-> 07 LLM API Caller
-> 08 Parse Intent JSON

05 Main Flow Context Builder
-> 09 Normalize Intent With Domain

08 Parse Intent JSON
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

Langflow canvas에서는 `07 LLM API Caller`를 세 개 배치하는 것을 권장한다.

```text
Intent LLM API Caller
Pandas Analysis LLM API Caller
Answer LLM API Caller
```

각 노드는 같은 component를 사용하지만 API key, model, temperature를 독립적으로 입력한다. 예를 들어 intent 추출은 빠른 모델, pandas 코드 생성은 더 강한 모델, 최종 답변은 비용이 낮은 모델을 넣을 수 있다.

## 핵심 연결 목록

### 1. State와 Domain을 Main Context로 묶기

```text
Previous State JSON Input.previous_state_payload
-> Session State Loader.previous_state_payload

사용자 질문 입력
-> Session State Loader.user_question

Session State Loader.agent_state
-> Main Flow Context Builder.agent_state

MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload

Table Catalog Loader.table_catalog_payload
-> Main Flow Context Builder.table_catalog_payload

사용자 질문 입력
-> Main Flow Context Builder.user_question
```

`Main Flow Context Builder.main_context`에는 아래 정보가 들어간다.

```json
{
  "main_context": {
    "user_question": "...",
    "reference_date": "",
    "agent_state": {},
    "domain_payload": {},
    "domain": {},
    "domain_index": {},
    "domain_prompt_context": {},
    "domain_errors": [],
    "mongo_domain_load_status": {},
    "table_catalog_payload": {},
    "table_catalog": {},
    "table_catalog_prompt_context": {},
    "table_catalog_errors": []
  }
}
```

`domain_prompt_context`는 LLM prompt용 경량 요약이다. 전체 domain의 모든 컬럼과 원본 payload를 LLM에 넣지 않고, 의도 분류에 필요한 dataset, metric, alias, term 요약만 전달해서 token 사용량을 줄인다.

`table_catalog_prompt_context`는 어떤 질문이 어떤 dataset 후보와 연결되는지 알려주는 LLM용 경량 요약이다. 실제 SQL, table name, db_key는 LLM prompt에 넣지 않고 `table_catalog` 실행 payload에만 둔다.

### 2. Intent 추출

```text
Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Build Intent Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Parse Intent JSON.llm_result
```

`LLM API Caller.response_mode`는 `auto`로 두면 된다. `Build Intent Prompt`가 `prompt_type="intent"`를 같이 보내므로 LLM caller가 JSON 응답 모드로 처리한다.

### 3. Intent 정규화와 분기

```text
Parse Intent JSON.intent_raw
-> Normalize Intent With Domain.intent_raw

Main Flow Context Builder.main_context
-> Normalize Intent With Domain.main_context

Normalize Intent With Domain.intent
-> Request Type Router.intent

Request Type Router.data_question
-> Query Mode Decider.intent

Query Mode Decider.query_mode_decision
-> Retrieval Plan Builder.query_mode_decision
```

`Request Type Router`는 output이 여러 개지만 Phase 1에서는 `data_question`만 다음 노드로 연결하면 된다. `process_execution`, `unknown`, `router_result`는 이후 process flow나 디버깅용이다.

### 4. 데이터 조회

조회 계획은 SQL 문자열을 넘기지 않는다. `Retrieval Plan Builder`는 아래처럼 dataset별 tool 실행 계획을 만든다.

```json
{
  "dataset_key": "production",
  "dataset_label": "생산 데이터",
  "tool_name": "get_production_data",
  "params": {
    "date": "2026-04-22"
  },
  "post_filters": {
    "product": "A"
  },
  "filter_expressions": []
}
```

Dummy 조회:

```text
Retrieval Plan Builder.retrieval_plan
-> Dummy Data Retriever.retrieval_plan

Dummy Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

Oracle 조회:

```text
Retrieval Plan Builder.retrieval_plan
-> OracleDB Data Retriever.retrieval_plan

OracleDB Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

두 조회 노드는 같은 `retrieval_result` 형태를 반환하므로 둘 중 하나만 다음 노드에 연결한다.

### 5. Pandas 분석

```text
Analysis Base Builder.analysis_context
-> Build Pandas Analysis Prompt.analysis_context

Build Pandas Analysis Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Parse Pandas Analysis JSON.llm_output

Analysis Base Builder.analysis_context
-> Execute Pandas Analysis.analysis_context

Parse Pandas Analysis JSON.analysis_plan
-> Execute Pandas Analysis.analysis_plan
```

`Build Pandas Analysis Prompt`는 현재 조회된 dataset과 metric hint에 필요한 domain slice만 prompt에 넣는다. 전체 domain을 반복해서 넣지 않는다.

### 6. 최종 답변과 다음 state

```text
Execute Pandas Analysis.analysis_result
-> Build Answer Prompt.analysis_result

Build Answer Prompt.prompt_payload
-> LLM API Caller.prompt

LLM API Caller.llm_result
-> Final Answer Builder.answer_llm_output

Execute Pandas Analysis.analysis_result
-> Final Answer Builder.analysis_result

Final Answer Builder.answer_message
-> Chat Output or Playground display output
```

`Final Answer Builder.final_result`는 전체 JSON/Data payload 확인용이다. Playground에서 짧게 보려면 `answer_message`를 출력에 연결한다.

`Final Answer Builder.next_state`를 다음 질문의 `Previous State JSON Input`에 넣으면 후속 질문에서 `current_data`를 재사용할 수 있다.

## MongoDB Domain 로딩 방식

Main Flow는 아래 컬렉션에서 `status="active"`인 item들을 모두 읽는다.

```text
Database Name: datagov
Collection Name: manufacturing_domain_items
```

domain id를 입력하지 않는다. `gbn + key + payload`만 사용해 아래 domain 구조로 합친다.

```json
{
  "products": {},
  "process_groups": {},
  "terms": {},
  "datasets": {},
  "metrics": {},
  "join_rules": []
}
```

`domain_document`는 최소 metadata만 담고, 실제 실행에는 `domain`, `domain_index`, `domain_prompt_context`를 사용한다.

수동 JSON 테스트를 해야 할 때만 아래 fallback을 사용한다.

```text
Domain JSON Input.domain_json_payload
-> Domain JSON Loader.domain_json_payload

Domain JSON Loader.domain_payload
-> Main Flow Context Builder.domain_payload
```

## Table Catalog 입력 방식

테이블/DB 조회 정보는 domain이 아니라 table catalog로 전달한다.

```text
Table Catalog JSON Input.table_catalog_json_payload
-> Table Catalog Loader.table_catalog_json_payload

Table Catalog Loader.table_catalog_payload
-> Main Flow Context Builder.table_catalog_payload
```

쿼리는 `sql_template`에 block 형태로 그대로 붙여넣는 방식을 권장한다. 표준 JSON은 raw multiline string을 지원하지 않지만, `Table Catalog Loader`는 SQL 전용 편의 문법으로 `"""..."""` 블록을 먼저 변환한 뒤 파싱한다.

```text
{
  "sql_template": """
SELECT
    WORK_DT,
    OPER_NAME,
    SUM(QTY) AS production
FROM PROD_TABLE
WHERE WORK_DT = :date
  AND NVL(DELETE_FLAG, 'N') = 'N'
  AND SITE_CODE = "K1"
GROUP BY WORK_DT, OPER_NAME
"""
}
```

이 방식이면 SQL 안에 작은따옴표(`'N'`)나 큰따옴표(`"K1"`)가 있어도 대부분 그대로 유지된다. Loader 출력의 `table_catalog.datasets[].sql_template`에는 실제 실행 가능한 멀티라인 SQL 문자열이 들어간다.

어떤 질문에 어떤 데이터가 필요한지는 아래 두 정보가 함께 결정한다.

- `table_catalog.datasets[].keywords`, `question_examples`: 질문 표현과 dataset 후보 연결
- domain `metrics[].required_datasets`: 계산 metric이 요구하는 dataset 연결

예를 들어 “생산 달성율”은 domain metric에서 `production`, `target`이 필요하다고 정의하고, table catalog에서 각 dataset의 `tool_name`, `required_params`, SQL을 가져온다.

예시 파일:

```text
reference_materials/table_catalog_examples/phase1_table_catalog_input_example.txt
```

## OracleDB TNS Connections JSON 예시

`OracleDB Data Retriever.db_connections_json` 입력 예시:

```json
{
  "MES": {
    "id": "MES_USER",
    "pw": "MES_PASSWORD",
    "tns": "MES_TNS_ALIAS"
  },
  "PLAN": {
    "id": "PLAN_USER",
    "pw": "PLAN_PASSWORD",
    "tns": "PLAN_TNS_ALIAS"
  },
  "QMS": {
    "id": "QMS_USER",
    "pw": "QMS_PASSWORD",
    "tns": "QMS_TNS_ALIAS"
  },
  "default": {
    "id": "DEFAULT_USER",
    "pw": "DEFAULT_PASSWORD",
    "tns": "DEFAULT_TNS_ALIAS"
  }
}
```

사용자 입력 설정명은 `tns`, `tns_name`, `tns_alias`, `tns_info` 중 하나를 쓴다. 내부적으로 `oracledb.connect(user=..., password=..., dsn=tns)` 형태로 연결한다.

Oracle SQL은 domain JSON이나 LLM 결과에서 받지 않는다. 우선 `Table Catalog Loader.table_catalog`의 dataset별 `sql_template`을 사용하고, table catalog가 비어 있을 때만 `14 OracleDB Data Retriever` 내부 fallback SQL을 사용한다.

```text
get_production_data
get_target_data
get_defect_rate
get_equipment_status
get_wip_status
get_yield_data
get_hold_lot_data
get_scrap_data
get_recipe_condition_data
get_lot_trace_data
```

실제 운영 테이블명과 컬럼명은 이 함수 안의 SQL만 환경에 맞게 수정하면 된다.

## Final Output과 MongoDB Table 저장

`Final Answer Builder`는 Playground 출력이 너무 길어지지 않도록 원본 table은 MongoDB에 저장하고, flow output에는 마지막 분석 결과 preview와 table reference id만 담는다.

기본 저장 위치:

```text
Database Name: datagov
Collection Name: manufacturing_flow_tables
```

추천 출력:

```text
Final Answer Builder.answer_message
-> Chat Output
```

`answer_message`는 답변 문장, row count, column 목록, table reference id, 제한된 markdown preview만 보여준다.
