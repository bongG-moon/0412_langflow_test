# Langflow Domain Item Flow Guide

이 문서는 현재 구현된 새 도메인 정리 flow인 `langflow/domain_item_authoring_flow`를 이해하기 위한 설명서이다.

기존 `domain_authoring_flow`는 큰 `domain_patch` fragment를 저장하는 방식이었다. 새 flow는 도메인 정보를 `gbn + key` 단위의 작은 item document로 MongoDB에 저장한다. 이렇게 하면 나중에 Web 화면에서 도메인 정보를 항목별로 조회, 수정, 삭제, 시각화하기 쉽다.

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
-> built-in LLM 호출
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
  06_parse_domain_item_json.py
  07_normalize_domain_item.py
  08_domain_item_conflict_checker.py
  09_mongodb_domain_item_saver.py
```

Main Flow에서 item collection을 읽는 노드는 다음 파일에 있다.

```text
langflow/data_answer_flow/10_mongodb_domain_item_payload_loader.py
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

Domain Item Prompt Template.prompt
-> built-in LLM prompt/chat input

built-in LLM output
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
prompt         -> Message 타입. built-in LLM에 연결
prompt_payload -> Data 타입. prompt 문자열 확인 또는 커스텀 LLM 연결용
```

보통 built-in LLM에는 아래 포트를 연결한다.

```text
Domain Item Prompt Template.prompt
```

`prompt_payload`는 built-in LLM 연결용이 아니라 디버깅/대체 LLM용 보조 출력이다.

### 6.7 Built-in LLM Node

새 flow에는 커스텀 LLM caller가 없다. Langflow 기본 LLM 노드를 사용한다.

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
06_parse_domain_item_json.py
```

역할:

built-in LLM 결과에서 JSON을 추출한다. Markdown code fence가 섞여 있어도 가능한 한 JSON object만 찾아 파싱한다.

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
07_normalize_domain_item.py
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
08_domain_item_conflict_checker.py
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
09_mongodb_domain_item_saver.py
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
langflow/data_answer_flow/10_mongodb_domain_item_payload_loader.py
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

`Normalize Intent With Domain` 이후에는 `main_context`가 payload 안에 같이 전달된다. 따라서 `Query Mode Decider`, `Retrieval Plan Builder`, `Dummy Data Retriever`, `OracleDB Data Retriever`, `Analysis Base Builder`, `Build Pandas Analysis Prompt`에는 `domain_payload`를 다시 직접 연결하지 않아도 된다.

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

## 10. 기존 flow와의 차이

| 항목 | Legacy `domain_authoring_flow` | New `domain_item_authoring_flow` |
| --- | --- | --- |
| 저장 단위 | 큰 domain patch fragment | 작은 item document |
| LLM 호출 | 커스텀 LLM caller 포함 | built-in LLM 사용 |
| 입력 방식 | 전체 domain patch 추출 | 여러 줄 note를 item 배열로 추출 |
| 저장 필드 | domain_id, patch_hash 등 포함 | gbn, key, payload 중심 |
| Web 관리 | fragment 안을 파싱해야 함 | item document를 바로 표시 가능 |
| Main Flow 연결 | fragment loader | item payload loader |

## 11. 자주 생기는 연결 문제

### Prompt Template과 built-in LLM이 연결되지 않음

`Domain Item Prompt Template.prompt` 포트를 사용해야 한다.

```text
Domain Item Prompt Template.prompt -> built-in LLM prompt/chat input
```

`prompt_payload`는 `Data` 타입이라 built-in LLM 입력과 맞지 않을 수 있다.

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

## 13. 16번 Custom Node 가이드와 연결해서 읽는 법

`16_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`는 Langflow custom node를 만드는 일반 문법을 설명한다. 이 문서는 그 문법이 실제 프로젝트 flow에서 어떻게 쓰였는지 보여주는 적용 예시다.

### 13.1 Input Node 패턴

적용 노드:

```text
00_raw_domain_text_input.py
```

16번 문서의 핵심 개념:

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

16번 문서의 핵심 개념:

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

16번 문서의 핵심 개념:

```text
여러 input payload를 직접 LLM에 넣지 않고, prompt builder에서 읽기 쉬운 하나의 prompt로 만든다.
built-in LLM에 연결할 때는 Data가 아니라 Message/string 계열 output이 필요할 수 있다.
```

현재 flow 적용 방식:

```text
Domain Item Prompt Template.prompt
  -> built-in LLM prompt/chat input
```

`prompt` output은 built-in LLM에 연결하기 위한 `Message` 타입이다. `prompt_payload` output은 디버깅이나 커스텀 LLM 노드 연결용 보조 `Data` 출력이다.

### 13.4 Built-in LLM 사용 패턴

현재 flow에서는 커스텀 LLM caller를 만들지 않는다. 이유는 API key, model, provider 설정은 Langflow 기본 LLM 노드가 이미 잘 제공하기 때문이다.

연결 위치:

```text
Domain Item Prompt Template.prompt
-> built-in LLM node
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
06_parse_domain_item_json.py
07_normalize_domain_item.py
```

16번 문서의 핵심 개념:

```text
LLM 결과는 그대로 믿지 않고 parser에서 JSON으로 꺼낸다.
그 다음 normalizer에서 key, status, aliases, source_text 같은 필드를 표준화한다.
```

현재 flow에서는 파싱과 정규화를 분리했다. 이렇게 하면 LLM 출력 형식 오류와 도메인 item schema 오류를 서로 다른 위치에서 확인할 수 있다.

### 13.6 Validator / Saver 패턴

적용 노드:

```text
08_domain_item_conflict_checker.py
09_mongodb_domain_item_saver.py
```

16번 문서의 핵심 개념:

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
langflow/data_answer_flow/10_mongodb_domain_item_payload_loader.py
```

16번 문서의 핵심 개념:

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

이후 노드들은 앞 노드 payload 안에 포함된 `main_context`를 계속 전달받으므로 domain 관련 선을 여러 번 그리지 않는다.

### 13.8 이 flow를 수정할 때의 기준

새 노드를 추가하거나 수정할 때는 다음 기준으로 판단한다.

- LLM prompt 문장이 바뀌는 일은 `Domain Item Prompt Template`에서 처리한다.
- LLM에 넣을 변수가 바뀌는 일은 `Domain Item Prompt Context Builder`에서 처리한다.
- 저장 schema가 바뀌는 일은 `Normalize Domain Item`과 `MongoDB Domain Item Saver`에서 처리한다.
- 충돌 판단 기준이 바뀌는 일은 `Domain Item Conflict Checker`에서 처리한다.
- Main Flow가 읽는 domain JSON 구조가 바뀌는 일은 `MongoDB Domain Item Payload Loader`에서 처리한다.

한 노드에 모든 로직을 몰아넣지 않는 이유는 Langflow 초보자가 canvas에서 문제 위치를 찾기 쉽게 하기 위해서다. 예를 들어 LLM 결과가 이상하면 parser 이전인지 이후인지, 저장이 안 되면 conflict checker인지 saver인지 분리해서 확인할 수 있다.
