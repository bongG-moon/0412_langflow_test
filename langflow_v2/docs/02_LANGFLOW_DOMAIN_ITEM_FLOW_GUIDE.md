# Langflow Domain Item Flow Guide

이 문서는 이 프로젝트에서 도메인 지식을 `item document`로 저장하고, Langflow v2 flow에서 다시 읽어 쓰는 방식을 설명한다.

초기 Langflow authoring flow인 `langflow/domain_item_authoring_flow`의 노드별 구조와, 현재 v2에서 쓰는 MongoDB item document 방식 및 등록 웹의 구현 기준을 함께 다룬다.

이 flow는 도메인 정보를 `gbn + key` 단위의 작은 item document로 MongoDB에 저장한다. 이렇게 하면 나중에 Web 화면에서 도메인 정보를 항목별로 조회, 수정, 삭제, 시각화하기 쉽다.

## 1. 전체 목표

사용자는 하나의 입력창에 도메인 설명을 여러 줄로 입력한다.

```text
생산 달성률은 생산량 / 목표량으로 계산한다.
production 데이터와 target 데이터는 WORK_DT, OPER_NAME 기준으로 조인한다.
다이본딩 공정군은 D/A1, D/A2, D/A3를 포함한다.
```

flow는 이 입력을 다음 순서로 처리한다.

```text
원문 입력
-> 여러 줄 note 분리
-> 어떤 도메인 항목인지 route 판단
-> 해당 route의 기존 item만 MongoDB에서 조회
-> LLM prompt 변수 생성
-> prompt 생성
-> custom LLM API 호출
-> LLM JSON 파싱
-> item schema 정규화
-> 충돌 검증
-> MongoDB에 item 단위 저장
```

저장 결과는 예를 들어 다음처럼 여러 document가 된다.

```text
manufacturing_domain_items
  - {gbn: "metrics", key: "production_achievement_rate", ...}
  - {gbn: "join_rules", key: "production_target_join", ...}
  - {gbn: "process_groups", key: "da", ...}
```

## 2. 저장 단위

새 flow의 저장 collection 기본값은 다음과 같다.

```text
Database Name: datagov
Collection Name: manufacturing_domain_items
```

저장 document 기본 형태:

```json
{
  "gbn": "metrics",
  "key": "production_achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "생산 달성률",
    "aliases": ["달성률", "달성율"],
    "required_datasets": ["production", "target"],
    "formula": "production / target"
  },
  "normalized_aliases": ["production_achievement_rate", "생산달성률", "달성률", "달성율"],
  "normalized_keywords": [],
  "source_note_id": "note_1",
  "source_text": "생산 달성률은 생산량 / 목표량으로 계산한다.",
  "warnings": [],
  "created_at": "UTC ISO datetime",
  "updated_at": "UTC ISO datetime"
}
```

기능에 꼭 필요하지 않은 `domain_id`, `patch_hash`, `authoring_mode`는 새 item 저장 구조에서 사용하지 않는다.

## 3. 지원 GBN

`gbn`은 도메인 item의 항목 구분값이다.

| gbn | 의미 | Main Flow 변환 위치 |
| --- | --- | --- |
| `products` | 제품군, 제품 alias, 제품 필터 | `domain.products` |
| `process_groups` | 공정 그룹, 공정 alias, 실제 공정값 | `domain.process_groups` |
| `terms` | 특정 용어와 필터 의미 | `domain.terms` |
| `datasets` | 조회 가능한 데이터셋 정의 | `domain.datasets` |
| `metrics` | 계산식, KPI, 파생 지표 | `domain.metrics` |
| `join_rules` | 데이터셋 간 조인 규칙 | `domain.join_rules` |

## 4. 구현 파일 순서

현재 구현 파일은 다음 순서로 배치되어 있다.

```text
langflow/domain_item_authoring_flow/
  00_raw_domain_text_input.py
  01_domain_text_splitter.py
  02_domain_item_router.py
  03_mongodb_existing_domain_item_loader.py
  04_domain_item_prompt_context_builder.py
  05_domain_item_prompt_template.py
  06_domain_item_llm_api_caller.py
  07_parse_domain_item_json.py
  08_normalize_domain_item.py
  09_domain_item_conflict_checker.py
  10_mongodb_domain_item_saver.py
```

Main Flow에서 item collection을 읽는 노드는 다음 파일에 있다.

```text
langflow/data_answer_flow/02_mongodb_domain_item_payload_loader.py
```

## 5. Langflow 연결 순서

Canvas에서는 다음 순서로 연결한다.

```text
Raw Domain Text Input.raw_domain_payload
-> Domain Text Splitter.raw_domain_payload

Domain Text Splitter.split_domain_payload
-> Domain Item Router.raw_domain_payload

Domain Item Router.route_payload
-> MongoDB Existing Domain Item Loader.route_payload

Domain Item Router.route_payload
-> Domain Item Prompt Context Builder.route_payload

MongoDB Existing Domain Item Loader.existing_items
-> Domain Item Prompt Context Builder.existing_items

Domain Item Prompt Context Builder.prompt_context
-> Domain Item Prompt Template.prompt_context

Domain Item Prompt Template.prompt_payload
-> Domain Item LLM API Caller.prompt

Domain Item LLM API Caller.llm_result
-> Parse Domain Item JSON.llm_output

Parse Domain Item JSON.domain_items_raw
-> Normalize Domain Item.domain_items_raw

Domain Item Router.route_payload
-> Normalize Domain Item.route_payload

Normalize Domain Item.normalized_domain_items
-> Domain Item Conflict Checker.normalized_domain_items

MongoDB Existing Domain Item Loader.existing_items
-> Domain Item Conflict Checker.existing_items

Domain Item Conflict Checker.conflict_report
-> MongoDB Domain Item Saver.conflict_report
```

## 6. 노드별 역할

### 6.1 Raw Domain Text Input

파일:

```text
00_raw_domain_text_input.py
```

역할:

사용자가 도메인 원문을 직접 입력하는 노드다. 긴 텍스트와 여러 줄 입력이 편하도록 `MultilineInput`을 사용한다.

입력:

```text
raw_text
```

출력:

```json
{
  "raw_text": "사용자 입력 원문",
  "source": "domain_item_authoring_flow",
  "is_empty": false
}
```

### 6.2 Domain Text Splitter

파일:

```text
01_domain_text_splitter.py
```

역할:

여러 줄 raw text를 의미 단위 note 배열로 나눈다.

입력 예:

```text
1. 생산 달성률은 생산량 / 목표량으로 계산한다.
2. production 데이터와 target 데이터는 WORK_DT 기준으로 조인한다.
```

출력 예:

```json
{
  "raw_text": "전체 원문",
  "combined_raw_text": "생산 달성률은 생산량 / 목표량으로 계산한다.\nproduction 데이터와 target 데이터는 WORK_DT 기준으로 조인한다.",
  "raw_notes": [
    {
      "note_id": "note_1",
      "raw_text": "생산 달성률은 생산량 / 목표량으로 계산한다."
    },
    {
      "note_id": "note_2",
      "raw_text": "production 데이터와 target 데이터는 WORK_DT 기준으로 조인한다."
    }
  ],
  "note_count": 2
}
```

중요한 점:

Splitter가 저장 건수를 직접 결정하지 않는다. MongoDB 저장 건수는 LLM이 반환한 `items` 배열 개수로 결정된다.

### 6.3 Domain Item Router

파일:

```text
02_domain_item_router.py
```

역할:

원문과 `raw_notes`를 보고 어떤 `gbn`이 필요한지 1차 분류한다.

출력 예:

```json
{
  "raw_text": "정리된 전체 원문",
  "raw_notes": [
    {"note_id": "note_1", "raw_text": "생산 달성률은 생산량 / 목표량으로 계산한다."}
  ],
  "note_count": 1,
  "routes": ["metrics"],
  "primary_gbn": "metrics",
  "confidence": 0.75
}
```

현재 노드는 rule 기반 fallback이다. Langflow 기본 Smart Router를 쓰고 싶으면 이 위치를 대체할 수 있다. 단, 뒤 노드와 연결하려면 `raw_text`, `raw_notes`, `routes`, `primary_gbn`을 포함한 payload를 만들어야 한다.

### 6.4 MongoDB Existing Domain Item Loader

파일:

```text
03_mongodb_existing_domain_item_loader.py
```

역할:

route에 포함된 `gbn`의 기존 item만 MongoDB에서 조회한다.

조회 조건 예:

```json
{
  "gbn": {"$in": ["metrics", "join_rules"]},
  "status": {"$in": ["active", "review_required"]}
}
```

출력은 전체 document가 아니라 prompt와 충돌 검증에 필요한 요약이다.

```json
{
  "routes": ["metrics"],
  "existing_items": {
    "metrics": [
      {
        "gbn": "metrics",
        "key": "production_achievement_rate",
        "display_name": "생산 달성률",
        "normalized_aliases": ["달성률"]
      }
    ]
  }
}
```

### 6.5 Domain Item Prompt Context Builder

파일:

```text
04_domain_item_prompt_context_builder.py
```

역할:

Prompt Template에 넣을 변수를 만든다. LLM 호출은 하지 않는다.

출력 핵심:

```json
{
  "template_vars": {
    "routes": "metrics, join_rules",
    "item_schemas": "{...}",
    "existing_items": "{...}",
    "raw_notes": "[...]",
    "raw_text": "전체 원문",
    "output_schema": "{...}"
  }
}
```

### 6.6 Domain Item Prompt Template

파일:

```text
05_domain_item_prompt_template.py
```

역할:

`template_vars`를 실제 LLM prompt로 조합한다.

출력:

```text
prompt         -> Message 타입. prompt 미리보기 또는 호환용
prompt_payload -> Data 타입. Domain Item LLM API Caller에 연결
```

보통 custom LLM caller에는 아래 포트를 연결한다.

```text
Domain Item Prompt Template.prompt_payload
```

`prompt_payload`에는 `prompt` 문자열과 `prompt_type="domain_item_json"`이 들어간다.

### 6.7 Domain Item LLM API Caller

파일:

```text
06_domain_item_llm_api_caller.py
```

역할:

`Domain Item Prompt Template.prompt_payload`를 받아 LLM API를 호출한다. Langflow 기본 LLM node를 쓰지 않고 이 custom node에 `llm_api_key`, `model_name`, `temperature`를 직접 입력한다.

출력:

```json
{
  "llm_text": "{...}",
  "llm_debug": {
    "provider": "langchain_google_genai",
    "model_name": "...",
    "response_mode": "json",
    "ok": true,
    "error": null
  }
}
```

LLM은 반드시 JSON만 반환해야 한다.

```json
{
  "items": [
    {
      "source_note_id": "note_1",
      "gbn": "metrics",
      "key": "production_achievement_rate",
      "payload": {
        "display_name": "생산 달성률",
        "aliases": ["달성률", "달성율"],
        "required_datasets": ["production", "target"],
        "formula": "production / target"
      },
      "warnings": []
    }
  ],
  "unmapped_text": ""
}
```

### 6.8 Parse Domain Item JSON

파일:

```text
07_parse_domain_item_json.py
```

역할:

custom LLM caller 결과에서 JSON을 추출한다. Markdown code fence가 섞여 있어도 가능한 한 JSON object만 찾아 파싱한다.

출력:

```json
{
  "domain_items_raw": [],
  "unmapped_text": "",
  "parse_errors": [],
  "llm_text_chars": 0
}
```

### 6.9 Normalize Domain Item

파일:

```text
08_normalize_domain_item.py
```

역할:

LLM이 만든 raw item을 MongoDB 저장용 최소 schema로 정리한다.

정규화 결과:

```json
{
  "gbn": "metrics",
  "key": "production_achievement_rate",
  "status": "active",
  "payload": {},
  "normalized_aliases": [],
  "normalized_keywords": [],
  "source_note_id": "note_1",
  "source_text": "생산 달성률은 생산량 / 목표량으로 계산한다.",
  "warnings": []
}
```

`source_note_id`가 있으면 `raw_notes`에서 해당 note의 원문을 찾아 `source_text`로 저장한다. 없으면 전체 원문을 저장한다.

### 6.10 Domain Item Conflict Checker

파일:

```text
09_domain_item_conflict_checker.py
```

역할:

저장 전 중복/충돌을 검사한다.

검사 항목:

```text
같은 batch 안 key 중복
기존 item과 key 동일 여부
alias가 다른 item에 이미 등록되었는지
dataset keyword가 다른 dataset에 이미 등록되었는지
```

blocking conflict가 있으면 해당 item의 권장 상태가 `review_required`가 된다.

### 6.11 MongoDB Domain Item Saver

파일:

```text
10_mongodb_domain_item_saver.py
```

역할:

정규화된 item 배열을 순회하면서 MongoDB에 건바이건 저장한다.

저장 기준:

```text
unique key: gbn + key
status=active          -> Main Flow에서 사용
status=review_required -> 저장은 되지만 Main Flow에서는 제외
```

출력 예:

```json
{
  "saved_items": [
    {
      "gbn": "metrics",
      "key": "production_achievement_rate",
      "status": "active",
      "used_in_main_flow": true
    }
  ],
  "save_status": {
    "saved": true,
    "saved_count": 1,
    "errors": []
  }
}
```

## 7. 여러 줄 입력과 저장 건수

여러 줄 입력을 넣으면 splitter는 줄을 나눠 `raw_notes`를 만든다.

하지만 MongoDB 저장 건수는 `raw_notes` 개수가 아니라 LLM이 반환한 `items` 개수다.

예를 들어 3줄 입력:

```text
생산 달성률은 생산량 / 목표량으로 계산한다.
production 데이터와 target 데이터는 WORK_DT 기준으로 조인한다.
달성률과 달성율은 생산 달성률과 같은 의미다.
```

LLM이 metric 1개와 join rule 1개만 반환하면 MongoDB에는 2개 document가 저장된다.

```text
metrics:production_achievement_rate
join_rules:production_target_join
```

반대로 한 줄 안에 metric과 join rule이 함께 있으면 한 줄 입력이어도 2개 item이 저장될 수 있다.

## 8. Main Flow에서 사용하는 방법

새 item 저장소를 Main Data Answer Flow에서 사용하려면 아래 노드를 쓴다.

```text
langflow_v2/02_mongodb_domain_loader.py
```

현재 Main Flow 연결:

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

`Normalize Intent With Domain` 이후에는 `main_context`가 payload 안에 같이 전달된다. 따라서 `Query Mode Decider`, `Retrieval Plan Builder`, `Dummy Data Retriever`, `OracleDB Data Retriever`, `Analysis Base Builder`, `Build Pandas Analysis Prompt`에는 `domain_payload`를 다시 직접 연결하지 않아도 된다. 단, table catalog는 `main_context`에 싣지 않으므로 `Table Catalog Loader.table_catalog_payload`를 `Retrieval Plan Builder`와 `OracleDB Data Retriever`에 직접 연결한다.

이 loader는 MongoDB의 `status=active` item만 읽어서 기존 Main Flow가 기대하는 `domain_payload`로 변환한다.

출력 형태:

```json
{
  "domain_document": {
    "domain_id": "mongodb_domain_items",
    "status": "active",
    "domain": {}
  },
  "domain": {},
  "domain_index": {},
  "domain_errors": [],
  "mongo_domain_load_status": {
    "source": "mongodb_domain_items",
    "active_item_count": 0,
    "gbn_counts": {}
  }
}
```

## 9. 테스트 입력 예시

Raw Domain Text Input에 넣어볼 수 있는 예시:

```text
생산 달성률은 생산량 / 목표량으로 계산한다.
생산량 데이터와 목표량 데이터는 WORK_DT, OPER_NAME, MODE, DEN 기준으로 조인한다.
달성률, 달성율, 목표 대비 생산은 모두 생산 달성률을 의미한다.
```

LLM이 반환하면 좋은 예시:

```json
{
  "items": [
    {
      "source_note_id": "note_1",
      "gbn": "metrics",
      "key": "production_achievement_rate",
      "payload": {
        "display_name": "생산 달성률",
        "aliases": ["달성률", "달성율", "목표 대비 생산"],
        "required_datasets": ["production", "target"],
        "required_columns": ["production", "target"],
        "calculation_mode": "ratio",
        "formula": "production / target",
        "output_column": "achievement_rate"
      },
      "warnings": []
    },
    {
      "source_note_id": "note_2",
      "gbn": "join_rules",
      "key": "production_target_join",
      "payload": {
        "base_dataset": "production",
        "join_dataset": "target",
        "join_type": "left",
        "join_keys": ["WORK_DT", "OPER_NAME", "MODE", "DEN"]
      },
      "warnings": []
    }
  ],
  "unmapped_text": ""
}
```

## 10. 현재 flow의 특징

| 항목 | 현재 `domain_item_authoring_flow` 방식 |
| --- | --- |
| 저장 단위 | 작은 item document |
| LLM 호출 | custom `Domain Item LLM API Caller` 사용 |
| 입력 방식 | 여러 줄 note를 item 배열로 추출 |
| 저장 필드 | gbn, key, payload 중심 |
| Web 관리 | item document를 바로 표시 가능 |
| Main Flow 연결 | item payload loader |

## 11. 자주 생기는 연결 문제

### Prompt Template과 custom LLM caller가 연결되지 않음

`Domain Item Prompt Template.prompt_payload` 포트를 사용해야 한다.

```text
Domain Item Prompt Template.prompt_payload
-> Domain Item LLM API Caller.prompt
```

`prompt` output은 Message 타입 호환용이다. 현재 권장 연결은 Data 타입인 `prompt_payload`다.

### Raw Domain Text Input 입력창이 불편함

현재는 `MultilineInput`을 사용한다. 기존 canvas에 올라간 노드는 캐시되어 있을 수 있으므로 custom component reload 후 노드를 다시 추가한다.

### Splitter가 3개 note를 만들었는데 MongoDB에는 2건만 저장됨

정상일 수 있다. 실제 저장 건수는 LLM이 반환한 `items` 배열 개수로 결정된다.

### Main Flow에서 저장한 item이 안 보임

확인할 값:

```text
MongoDB Domain Item Saver.Collection Name
MongoDB Domain Item Payload Loader.Collection Name
status 값이 active인지
```

## 12. 검증 명령

문법 검증:

```bash
python -m py_compile langflow/domain_item_authoring_flow/*.py langflow/data_answer_flow/*.py
```

Git whitespace 검증:

```bash
git diff --check -- langflow docs
```

## 13. 03번 Custom Node 가이드와 연결해서 읽는 법

`03_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`는 Langflow custom node를 만드는 일반 문법과 멀티턴, ReAct, 분기 설계 같은 범용 패턴을 설명한다. 이 문서는 그 문법이 이 프로젝트 flow에서 어떻게 쓰였는지 보여주는 적용 예시다.

### 13.1 Input Node 패턴

적용 노드:

```text
00_raw_domain_text_input.py
```

03번 커스텀 노드 가이드의 핵심 개념:

```text
사용자가 직접 값을 넣는 노드는 TextInput, MultilineInput, DropdownInput 같은 입력 컴포넌트를 쓴다.
출력은 뒤 노드가 안정적으로 읽을 수 있도록 Data(data={...})로 만든다.
```

현재 flow 적용 방식:

```text
Raw Domain Text Input
  입력: raw_text
  출력: raw_domain_payload
```

여러 줄 도메인 설명을 넣어야 하므로 `MultilineInput`을 사용한다. 출력 payload에는 원문과 빈 값 여부만 담는다.

```json
{
  "raw_text": "생산 달성률은 생산량 / 목표량으로 계산한다.",
  "source": "domain_item_authoring_flow",
  "is_empty": false
}
```

### 13.2 Data Loader / Transformer 패턴

적용 노드:

```text
01_domain_text_splitter.py
02_domain_item_router.py
03_mongodb_existing_domain_item_loader.py
04_domain_item_prompt_context_builder.py
```

03번 커스텀 노드 가이드의 핵심 개념:

```text
앞 노드의 Data를 DataInput으로 받고, value.data를 안전하게 꺼낸 뒤, 다음 노드가 쓸 표준 payload로 다시 반환한다.
```

현재 flow 적용 방식:

| 노드 | 입력 | 출력 | 역할 |
| --- | --- | --- | --- |
| `Domain Text Splitter` | `raw_domain_payload` | `split_domain_payload` | 여러 줄 입력을 `raw_notes` 배열로 분리 |
| `Domain Item Router` | `split_domain_payload` | `route_payload` | 어떤 `gbn` 항목이 필요한지 판단 |
| `MongoDB Existing Domain Item Loader` | `route_payload` | `existing_items` | route에 필요한 기존 item만 조회 |
| `Domain Item Prompt Context Builder` | `route_payload`, `existing_items` | `prompt_context` | prompt template에 넣을 변수 생성 |

이 구간은 LLM을 호출하지 않는다. 목적은 LLM에 넣을 입력을 작게 만들고, 기존 도메인 정보와 충돌 여부를 판단할 수 있는 최소 context를 준비하는 것이다.

### 13.3 Prompt Builder 패턴

적용 노드:

```text
05_domain_item_prompt_template.py
```

03번 커스텀 노드 가이드의 핵심 개념:

```text
여러 input payload를 직접 LLM에 넣지 않고, prompt builder에서 읽기 쉬운 하나의 prompt로 만든다.
custom LLM caller에 연결할 수 있도록 Data payload에 prompt 문자열을 담는다.
```

현재 flow 적용 방식:

```text
Domain Item Prompt Template.prompt_payload
  -> Domain Item LLM API Caller.prompt
```

`prompt_payload` output은 custom LLM 노드 연결용 `Data` 출력이다. `prompt` output은 prompt 미리보기 또는 다른 Message 호환 노드 연결용으로 남겨둔다.

### 13.4 Custom LLM 사용 패턴

현재 flow에서는 custom `Domain Item LLM API Caller`를 사용한다. API key, model, temperature는 이 노드에 직접 입력한다.

연결 위치:

```text
Domain Item Prompt Template.prompt_payload
-> Domain Item LLM API Caller.prompt
-> Domain Item LLM API Caller.llm_result
-> Parse Domain Item JSON.llm_output
```

LLM이 반드시 반환해야 하는 최소 형태:

```json
{
  "items": [
    {
      "source_note_id": "note_1",
      "gbn": "metrics",
      "key": "production_achievement_rate",
      "payload": {
        "display_name": "생산 달성률"
      },
      "warnings": []
    }
  ],
  "unmapped_text": ""
}
```

### 13.5 Parser / Normalizer 패턴

적용 노드:

```text
07_parse_domain_item_json.py
08_normalize_domain_item.py
```

03번 커스텀 노드 가이드의 핵심 개념:

```text
LLM 결과는 그대로 믿지 않고 parser에서 JSON으로 꺼낸다.
그 다음 normalizer에서 key, status, aliases, source_text 같은 필드를 표준화한다.
```

현재 flow에서는 파싱과 정규화를 분리했다. 이렇게 하면 LLM 출력 형식 오류와 도메인 item schema 오류를 서로 다른 위치에서 확인할 수 있다.

### 13.6 Validator / Saver 패턴

적용 노드:

```text
09_domain_item_conflict_checker.py
10_mongodb_domain_item_saver.py
```

03번 커스텀 노드 가이드의 핵심 개념:

```text
저장 전 검증과 실제 저장을 분리한다.
검증 노드는 저장하지 않고 판단 결과만 만든다.
저장 노드는 검증 결과를 보고 active 또는 review_required 상태로 저장한다.
```

현재 flow에서 충돌 검증은 다음을 확인한다.

```text
같은 batch 안 key 중복
기존 item과 key 중복
alias가 다른 item에 이미 쓰였는지
dataset keyword가 다른 dataset에 이미 쓰였는지
```

저장은 `gbn + key` 기준으로 upsert한다. 즉 같은 `gbn`과 `key`가 다시 들어오면 새 document를 무한히 추가하지 않고 기존 document를 갱신한다.

### 13.7 Main Flow Loader 패턴

적용 노드:

```text
langflow_v2/02_mongodb_domain_loader.py
```

03번 커스텀 노드 가이드의 핵심 개념:

```text
다른 flow에서 만든 데이터를 main flow가 바로 쓰기 어렵다면, loader node에서 main flow 표준 payload로 변환한다.
```

현재 loader는 `manufacturing_domain_items`의 `status=active` item만 읽어서 main flow가 기대하는 다음 형태로 조립한다.

```json
{
  "domain_document": {},
  "domain": {
    "products": {},
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  },
  "domain_index": {},
  "domain_errors": []
}
```

Main Flow 연결:

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

이후 노드들은 앞 노드 payload 안에 포함된 `main_context`를 계속 전달받으므로 domain 관련 선을 여러 번 그리지 않는다. Table catalog는 token 절감을 위해 별도 payload로 유지하고, 조회 계획/실행 노드에 직접 연결한다.

### 13.8 이 flow를 수정할 때의 기준

새 노드를 추가하거나 수정할 때는 다음 기준으로 판단한다.

- LLM prompt 문장이 바뀌는 일은 `Domain Item Prompt Template`에서 처리한다.
- LLM에 넣을 변수가 바뀌는 일은 `Domain Item Prompt Context Builder`에서 처리한다.
- 저장 schema가 바뀌는 일은 `Normalize Domain Item`과 `MongoDB Domain Item Saver`에서 처리한다.
- 충돌 판단 기준이 바뀌는 일은 `Domain Item Conflict Checker`에서 처리한다.
- Main Flow가 읽는 domain JSON 구조가 바뀌는 일은 `MongoDB Domain Item Payload Loader`에서 처리한다.

한 노드에 모든 로직을 몰아넣지 않는 이유는 Langflow 초보자가 canvas에서 문제 위치를 찾기 쉽게 하기 위해서다. 예를 들어 LLM 결과가 이상하면 parser 이전인지 이후인지, 저장이 안 되면 conflict checker인지 saver인지 분리해서 확인할 수 있다.

## 14. Langflow v2 프로젝트 전용 구현 패턴

이 섹션은 기존 Custom Node 가이드에 섞여 있던 프로젝트 특화 구현 내용을 이 문서로 옮겨 정리한 것이다. 다른 프로젝트에서 그대로 공유하기보다는, 이 제조 데이터 분석 flow를 수정할 때 참고한다.

### 14.1 Standalone Custom Component 원칙

Langflow에 직접 등록하는 노드는 standalone 방식으로 작성한다.

즉, 다음처럼 형제 모듈을 import하는 방식은 피한다.

```python
from langflow_v2.common import normalize_payload
from manufacturing_agent.domain.registry import load_domain
```

Langflow canvas에 Custom Component 파일 하나를 올렸을 때도 동작해야 하기 때문이다. 공통 helper가 필요하면 각 노드 파일 안에 최소 helper만 포함한다.

이 원칙 때문에 코드가 조금 길어질 수 있다. 대신 Langflow 서버에 올릴 때 Python path 문제나 패키지 배포 문제를 줄일 수 있다.

### 14.2 현재 v2 Main Flow의 큰 순서

현재 `langflow_v2`의 노드는 다음 책임으로 나뉜다.

```text
00 State Memory Extractor
01 State Loader
02 MongoDB Domain Loader
03 Domain JSON Loader
04 Table Catalog Loader
05 Main Flow Filters Loader
06 Build Intent Prompt
07 LLM JSON Caller
08 Normalize Intent Plan
09 Intent Route Router
10 Dummy Data Retriever
11 Oracle Data Retriever
12 MongoDB Data Loader
13 Current Data Retriever
14 Early Result Adapter
15 Retrieval Payload Merger
16 Retrieval Postprocess Router
17 Direct Result Adapter
18 Build Pandas Prompt
19 Normalize Pandas Plan
20 Pandas Analysis Executor
21 Analysis Result Merger
22 MongoDB Data Store
23 Build Final Answer Prompt
24 Normalize Answer Text
25 Final Answer Builder
26 State Memory Message Builder
```

이 flow에서 LLM은 크게 세 번 쓰인다.

1. 사용자 의도와 조회 계획을 분류한다.
2. pandas 분석 계획을 만든다.
3. 최종 데이터와 분석 결과를 보고 사용자 답변 문장을 만든다.

중간 계산은 가능한 Python과 pandas 쪽에서 처리한다. LLM은 판단과 설명에 집중시키고, row 단위 계산은 코드가 담당하는 구조다.

### 14.3 Prompt, LLM, 후처리를 분리한 이유

v2에서는 다음 세 단계를 한 노드에 합치지 않는다.

```text
Build Intent Prompt
-> LLM JSON Caller
-> Normalize Intent Plan
```

이렇게 나누면 문제가 생겼을 때 원인을 더 빨리 찾을 수 있다.

| 문제 상황 | 먼저 볼 노드 |
| --- | --- |
| LLM에 들어가는 정보가 부족함 | `06 Build Intent Prompt` |
| LLM 호출 자체가 실패함 | `07 LLM JSON Caller` |
| LLM JSON은 맞는데 route가 이상함 | `08 Normalize Intent Plan` |
| canvas 분기가 이상함 | `09 Intent Route Router` |

최종 답변도 같은 원칙을 따른다.

```text
Build Final Answer Prompt
-> LLM Caller
-> Normalize Answer Text
-> Final Answer Builder
```

최종 화면에는 답변 문장만이 아니라, 그 답변을 만들 때 사용한 최종 가공 데이터도 함께 담는다.

### 14.4 Route 기준

현재 v2 flow는 route를 캔버스에서 보이게 나누는 것을 목표로 한다.

중요한 route는 다음과 같다.

| route | 의미 |
| --- | --- |
| `followup_transform` | 이전 `current_data`를 재사용해서 분석 |
| `retrieval` | 새 데이터 조회 필요 |
| `finish` | 조회 없이 바로 응답 가능 |
| `single_retrieval` | 하나의 dataset 조회 |
| `multi_retrieval` | 여러 dataset 조회 |
| `direct_response` | 조회 결과를 그대로 답변에 사용 |
| `post_analysis` | pandas 전처리나 집계 필요 |

특히 metric item에 `required_datasets`가 있으면 LLM이 dataset을 하나만 반환했더라도 normalizer가 필요한 dataset을 추가해야 한다. 예를 들어 생산달성률이 `production`과 `wip`을 요구하면, 질문이 생산 쪽 단어만 포함해도 multi retrieval로 확장되어야 한다.

### 14.5 Domain Item Document 사용 방식

MongoDB의 domain item은 대략 다음 구조를 가진다.

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "Achievement Rate",
    "aliases": ["달성률", "달성율"],
    "required_datasets": ["production", "wip"],
    "formula": "sum(production) / sum(wip_qty) * 100",
    "output_column": "achievement_rate",
    "source_columns": ["production", "wip_qty"],
    "grouping_hint": ["MODE", "OPER_NAME"]
  },
  "normalized_aliases": ["achievement_rate", "달성률", "달성율"],
  "normalized_keywords": []
}
```

Main Flow는 이 document를 그대로 LLM에 전부 넣지 않는다. `02 MongoDB Domain Loader`가 active item만 읽고, intent prompt와 pandas prompt가 쓰기 좋은 payload로 압축한다.

도메인 정보가 필요한 위치는 주로 두 곳이다.

- Intent 분류: 사용자가 어떤 dataset, metric, filter를 말하는지 판단
- Pandas 전처리: 컬럼 의미, formula, grouping hint를 참고해 계산 계획 작성

조회 실행 노드에는 도메인 설명 전체가 필요하지 않다. 조회 노드는 이미 정규화된 dataset, filter, query parameter만 받는 편이 단순하다.

### 14.6 Table Catalog 사용 방식

Table catalog는 LLM이 "어떤 dataset을 조회해야 하는지" 판단할 수 있게 해주는 설명이다.

초기에는 컬럼 전체를 너무 자세히 넣지 않아도 된다. 보통 다음 정보면 충분하다.

```json
{
  "dataset_key": "production",
  "display_name": "Production",
  "description": "Daily production rows by process, line, mode, density, package.",
  "keywords": ["생산", "생산량", "production"],
  "retriever": "oracle",
  "target_db": "PKG_RPT",
  "date_filter": "WORK_DT",
  "common_group_by": ["OPER_NAME", "MODE", "LINE"]
}
```

실제 컬럼 목록은 조회 결과나 DB metadata에서 확인할 수 있다. 다만 LLM이 dataset을 고르는 데 꼭 필요한 키워드, 용도, 날짜 필터 기준은 catalog에 넣어야 한다.

### 14.7 Data Retriever 패턴

데이터 조회 노드는 source가 달라도 output schema를 비슷하게 유지한다.

```json
{
  "success": true,
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "data": [],
  "summary": "total rows 12, production 33097",
  "errors": []
}
```

현재 v2에는 같은 구조를 가진 조회 노드를 둘 수 있다.

- `10 Dummy Data Retriever`: 테스트용 더미 데이터 생성
- `11 Oracle Data Retriever`: Oracle DB 조회
- `12 MongoDB Data Loader`: 저장된 큰 데이터 재조회
- `13 Current Data Retriever`: 후속 질문에서 현재 데이터 재사용

여러 dataset을 쓰는 경우에는 각 retriever 결과를 `15 Retrieval Payload Merger`에서 하나의 payload로 합친다.

### 14.8 큰 데이터 저장과 reference 방식

조회 결과 전체를 매번 LLM prompt와 memory에 넣으면 토큰이 너무 커진다. 그래서 v2는 다음 방식을 기준으로 한다.

```text
조회 결과 또는 최종 분석용 중간 데이터
-> MongoDB에 저장
-> flow payload에는 data_ref, row_count, columns, preview, summary만 유지
-> 실제 pandas 계산이 필요할 때 data_ref로 다시 로드
```

단, 최종 사용자에게 보여줄 "최종 데이터"는 답변과 함께 보여준다. 여기서 말하는 최종 데이터는 원본 전체가 아니라, 답변을 만들기 위해 전처리된 결과 데이터이다.

### 14.9 Memory와 후속 질문

후속 질문을 제대로 처리하려면 다음 값이 다음 턴까지 유지되어야 한다.

| 값 | 역할 |
| --- | --- |
| `chat_history` | 이전 질문과 답변 흐름 |
| `context` | 최근 intent, filter, dataset 판단 |
| `current_data` | 후속 분석에 쓸 현재 결과 데이터 또는 data_ref |

Langflow Playground에서는 화면의 대화 session id가 유지되어야 memory를 이어서 읽을 수 있다. v2에서는 `State Memory Extractor`, `State Loader`, `State Memory Message Builder`가 이 역할을 나누어 담당한다.

후속 질문이 새 조회로 잘못 가는 경우에는 먼저 다음을 확인한다.

- Memory Loader가 이전 state를 실제로 읽었는가
- `current_data` 또는 `current_data_ref`가 비어 있지 않은가
- intent prompt에 "이전 결과를 기준으로 분석할 수 있음"이 들어갔는가
- normalizer가 LLM의 follow-up 판단을 덮어쓰고 있지 않은가

### 14.10 Registration Web과의 관계

`langflow_v2/registration_web`은 도메인과 table catalog를 사람이 JSON으로 직접 작성하지 않아도 되게 만든 보조 웹이다.

사용자는 자연어로 다음처럼 적는다.

```text
생산달성률은 생산량 / 재공 * 100으로 계산한다.
WB는 W/B1, W/B2 공정 그룹을 의미한다.
mode별로 자주 확인한다.
```

등록 웹은 LLM을 사용해 이 문장을 v2 item document 형식으로 바꾼 뒤 MongoDB에 저장한다.

이 웹에서 저장한 item은 Langflow v2의 `02 MongoDB Domain Loader`가 읽고, main flow의 intent/pandas prompt에 반영한다.

### 14.11 수정할 때의 기준

v2 flow를 수정할 때는 다음처럼 책임을 나누어 판단한다.

| 바꾸고 싶은 것 | 수정 위치 |
| --- | --- |
| LLM에게 보여줄 의도 분류 정보 | `06 Build Intent Prompt` |
| LLM provider, model, api key 처리 | `07 LLM JSON Caller` |
| metric required_datasets 반영 | `08 Normalize Intent Plan` |
| 화면에서 보이는 route 가지 | `09 Intent Route Router` |
| dummy 조회 데이터 | `10 Dummy Data Retriever` |
| Oracle DB 연결과 SQL 실행 | `11 Oracle Data Retriever` |
| 후속 질문 current data 로딩 | `13 Current Data Retriever` |
| pandas 계산 prompt | `18 Build Pandas Prompt` |
| pandas 계획 정규화 | `19 Normalize Pandas Plan` |
| pandas 실행 | `20 Pandas Analysis Executor` |
| 최종 답변 prompt | `23 Build Final Answer Prompt` |
| 답변과 최종 데이터 출력 형태 | `25 Final Answer Builder` |
| 다음 턴 memory 저장 메시지 | `26 State Memory Message Builder` |

이 기준을 지키면 한 노드의 함수가 지나치게 커지는 것을 막고, Langflow canvas에서 문제가 난 위치를 눈으로 따라가기 쉽다.
