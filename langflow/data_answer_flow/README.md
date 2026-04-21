# Data Answer Flow

제조 데이터 질문에 답하기 위한 Langflow main flow custom node 모음이다.

이번 구조에서는 `MongoDB Domain Item Payload Loader`의 `domain_payload`를 여러 노드에 직접 연결하지 않는다. 대신 `Main Flow Context Builder`가 사용자 질문, session state, domain payload를 한 번에 묶어서 `main_context`로 만들고, 이후 노드들은 이 값을 우선 사용한다.

## 핵심 변경

기존 방식:

```text
MongoDB Domain Item Payload Loader.domain_payload
-> Build Intent Prompt.domain_payload
-> Normalize Intent With Domain.domain_payload
-> Query Mode Decider.domain_payload
-> Retrieval Plan Builder.domain_payload
-> Dummy/Oracle Retriever.domain_payload
-> Analysis Base Builder.domain_payload
-> Build Pandas Analysis Prompt.domain_payload
```

새 방식:

```text
MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload

Session State Loader.agent_state
-> Main Flow Context Builder.agent_state

User Question
-> Main Flow Context Builder.user_question

Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Main Flow Context Builder.main_context
-> Normalize Intent With Domain.main_context
```

`Normalize Intent With Domain` 이후에는 `main_context`가 payload 안에 같이 전달된다. 그래서 `Request Type Router`, `Query Mode Decider`, `Retrieval Plan Builder`, `Dummy Data Retriever`, `OracleDB Data Retriever`, `Analysis Base Builder`, `Build Pandas Analysis Prompt`는 별도 domain 연결 없이 앞 노드의 output에서 필요한 context를 읽는다.

직접 연결용 `domain_payload`, `agent_state`, `user_question` input은 남겨두었지만 legacy/보조용이며 대부분 `advanced=True`로 숨겨두었다.

## 권장 전체 순서

```text
00 Previous State JSON Input
-> 01 Session State Loader

10 MongoDB Domain Item Payload Loader
-> 02 Main Flow Context Builder

02 Main Flow Context Builder
-> 03 Build Intent Prompt
-> built-in LLM
-> 05 Parse Intent JSON

02 Main Flow Context Builder
-> 06 Normalize Intent With Domain

05 Parse Intent JSON
-> 06 Normalize Intent With Domain
-> 07 Request Type Router
-> 08 Query Mode Decider
-> 11 Retrieval Plan Builder
-> 12 Dummy Data Retriever or 13 OracleDB Data Retriever
-> 14 Analysis Base Builder
-> 15 Build Pandas Analysis Prompt
-> built-in LLM
-> 16 Parse Pandas Analysis JSON
-> 17 Execute Pandas Analysis
-> 18 Build Answer Prompt
-> built-in LLM
-> 19 Final Answer Builder
```

## 권장 연결 목록

### 1. State와 Domain을 Main Context로 묶기

```text
Previous State JSON Input.previous_state_payload
-> Session State Loader.previous_state_payload

Session State Loader.agent_state
-> Main Flow Context Builder.agent_state

MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload

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
    "domain_errors": [],
    "mongo_domain_load_status": {}
  }
}
```

### 2. Intent 추출

```text
Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Build Intent Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Parse Intent JSON.llm_result
```

직접 API key/model을 custom node에서 넣고 싶을 때만 legacy 경로를 사용한다.

```text
Build Intent Prompt.intent_prompt
-> LLM JSON Caller.prompt

LLM JSON Caller.llm_result
-> Parse Intent JSON.llm_result
```

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

`Normalize Intent With Domain.intent` output 안에 `main_context`가 같이 들어간다. 따라서 `Request Type Router.agent_state`, `Query Mode Decider.domain_payload`, `Retrieval Plan Builder.domain_payload`는 새 구조에서는 연결하지 않아도 된다.

### 4. 데이터 조회

더미 데이터로 테스트할 때:

```text
Retrieval Plan Builder.retrieval_plan
-> Dummy Data Retriever.retrieval_plan

Dummy Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

OracleDB로 조회할 때:

```text
Retrieval Plan Builder.retrieval_plan
-> OracleDB Data Retriever.retrieval_plan

OracleDB Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

두 조회 노드는 같은 `retrieval_result` 형태를 반환한다. 그래서 둘 중 하나만 다음 노드에 연결하면 된다.

### 5. Pandas 분석과 답변

```text
Analysis Base Builder.analysis_context
-> Build Pandas Analysis Prompt.analysis_context

Build Pandas Analysis Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Parse Pandas Analysis JSON.llm_output

Analysis Base Builder.analysis_context
-> Execute Pandas Analysis.analysis_context

Parse Pandas Analysis JSON.analysis_plan
-> Execute Pandas Analysis.analysis_plan

Execute Pandas Analysis.analysis_result
-> Build Answer Prompt.analysis_result

Build Answer Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Final Answer Builder.answer_llm_output

Execute Pandas Analysis.analysis_result
-> Final Answer Builder.analysis_result
```

`Final Answer Builder.next_state`를 다음 질문의 `Previous State JSON Input`에 넣으면 연속 질문에서 `current_data`를 재사용할 수 있다.

## OracleDB Connections JSON 예시

`OracleDB Data Retriever.db_connections_json` 입력 예시:

```json
{
  "MES": {
    "id": "MES_USER",
    "pw": "MES_PASSWORD",
    "tns": "MES_TNS_ALIAS"
  },
  "DW": {
    "id": "DW_USER",
    "pw": "DW_PASSWORD",
    "tns": "DW_TNS_ALIAS"
  },
  "default": {
    "id": "DEFAULT_USER",
    "pw": "DEFAULT_PASSWORD",
    "tns": "DEFAULT_TNS_ALIAS"
  }
}
```

Oracle 연결 설정은 `tns` 기준이다. `oracledb.connect()` 내부 인자명은 `dsn`이지만, 사용자가 입력하는 설정명은 `tns`, `tns_name`, `tns_alias`, `tns_info` 중 하나만 사용한다.

각 dataset domain item에는 아래 중 하나가 있으면 된다.

```json
{
  "db_key": "MES",
  "query_template": "SELECT * FROM PROD_TABLE WHERE WORK_DT = :date"
}
```

또는:

```json
{
  "oracle": {
    "db_key": "MES",
    "sql": "SELECT * FROM PROD_TABLE WHERE WORK_DT = :date"
  }
}
```

## Built-in LLM 사용 위치

현재 main flow에서 built-in LLM 사용을 권장하는 위치는 세 곳이다.

```text
Build Intent Prompt.prompt
-> built-in LLM
-> Parse Intent JSON

Build Pandas Analysis Prompt.prompt
-> built-in LLM
-> Parse Pandas Analysis JSON

Build Answer Prompt.prompt
-> built-in LLM
-> Final Answer Builder
```

이 방식이면 provider, API key, model은 Langflow 기본 LLM 노드에서 관리하고 custom node는 prompt 구성, JSON 파싱, 검증, 데이터 처리만 담당한다.

## Final Output과 MongoDB Table 저장

`Final Answer Builder`는 Playground 출력이 너무 커지지 않도록 원본 table 데이터를 MongoDB에 저장하고, flow output에는 참조 id와 마지막 분석 결과 preview만 남긴다.

기본 저장 위치:

```text
Database Name: datagov
Collection Name: manufacturing_flow_tables
```

저장되는 table 종류:

```text
source_result    원본 조회 결과
source_snapshot  후속 질문 재사용용 원본 snapshot
current_dataset  current_datasets 내부 원본 table
analysis_result  pandas 전처리 후 마지막 결과 table
```

최종 output 예시:

```json
{
  "table_ref_id": "analysis_result_...",
  "row_count": 1200,
  "columns": ["WORK_DT", "OPER_NAME", "production"],
  "data": [
    {"WORK_DT": "2026-04-21", "OPER_NAME": "D/A1", "production": 100}
  ],
  "data_is_preview": true,
  "preview_row_limit": 200
}
```

원본 table 전체가 필요하면 `table_storage_status.table_refs[].table_ref_id` 값으로 `manufacturing_flow_tables`에서 조회한다.

## Knowledge Base / Smart Router 사용 여부

현재 구현에서 필수 노드로 넣지는 않았다.

- Knowledge Base는 도메인 작성 규칙, SQL 작성 규칙, 분석 예시 문서를 보강 context로 넣을 때 유용하다.
- Smart Router는 추후 process 실행 flow가 추가되면 `data_question`과 `process_execution` 분기를 UI에서 더 명시적으로 나눌 때 유용하다.
- Prompt Template 역할은 현재 `03 Build Intent Prompt`, `15 Build Pandas Analysis Prompt`, `18 Build Answer Prompt`가 custom node 형태로 수행한다.
