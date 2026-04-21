# Domain Item Authoring Flow

이 폴더는 새 도메인 정리 방식이다. 사용자는 하나의 입력창에 도메인 설명을 넣고, flow는 입력을 `gbn` 단위 item으로 분류한 뒤 MongoDB에 건바이건 저장한다.

기존 `domain_authoring_flow`는 큰 `domain_patch` fragment를 저장하는 legacy 방식이다. 새 권장 방식은 이 폴더의 item 기반 저장 방식이다.

## 저장 Collection

기본 MongoDB 저장 위치:

```text
Database Name: datagov
Collection Name: manufacturing_domain_items
```

저장 document는 기능에 필요한 최소 정보만 가진다.

```json
{
  "gbn": "metrics",
  "key": "production_achievement_rate",
  "status": "active",
  "payload": {},
  "normalized_aliases": [],
  "normalized_keywords": [],
  "source_text": "",
  "created_at": "UTC ISO datetime",
  "updated_at": "UTC ISO datetime"
}
```

`domain_id`, `patch_hash`, `authoring_mode`는 저장하지 않는다.

## Flow Order

```text
00_raw_domain_text_input.py
01_domain_text_splitter.py
02_domain_item_router.py
03_mongodb_existing_domain_item_loader.py
04_domain_item_prompt_context_builder.py
05_domain_item_prompt_template.py
built-in LLM node
06_parse_domain_item_json.py
07_normalize_domain_item.py
08_domain_item_conflict_checker.py
09_mongodb_domain_item_saver.py
```

## Wiring

| From | To | Required |
| --- | --- | --- |
| `Raw Domain Text Input.raw_domain_payload` | `Domain Text Splitter.raw_domain_payload` | Yes |
| `Domain Text Splitter.split_domain_payload` | `Domain Item Router.raw_domain_payload` | Yes |
| `Domain Item Router.route_payload` | `MongoDB Existing Domain Item Loader.route_payload` | Yes |
| `Domain Item Router.route_payload` | `Domain Item Prompt Context Builder.route_payload` | Yes |
| `MongoDB Existing Domain Item Loader.existing_items` | `Domain Item Prompt Context Builder.existing_items` | Yes |
| `Domain Item Prompt Context Builder.prompt_context` | `Domain Item Prompt Template.prompt_context` | Yes |
| `Domain Item Prompt Template.prompt` | built-in LLM prompt/chat input | Yes |
| built-in LLM output | `Parse Domain Item JSON.llm_output` | Yes |
| `Parse Domain Item JSON.domain_items_raw` | `Normalize Domain Item.domain_items_raw` | Yes |
| `Domain Item Router.route_payload` | `Normalize Domain Item.route_payload` | Yes |
| `Normalize Domain Item.normalized_domain_items` | `Domain Item Conflict Checker.normalized_domain_items` | Yes |
| `MongoDB Existing Domain Item Loader.existing_items` | `Domain Item Conflict Checker.existing_items` | Yes |
| `Domain Item Conflict Checker.conflict_report` | `MongoDB Domain Item Saver.conflict_report` | Yes |

## Smart Router 사용 방식

`02_domain_item_router.py`는 rule 기반 fallback router다. Langflow 기본 Smart Router를 쓰고 싶으면 이 위치에 Smart Router를 넣고, 결과를 다음 형태의 `route_payload`로 맞춰주면 뒤 노드를 그대로 쓸 수 있다.

```json
{
  "raw_text": "생산 달성률은 생산량 / 목표량이다.",
  "raw_notes": [
    {"note_id": "note_1", "raw_text": "생산 달성률은 생산량 / 목표량이다."}
  ],
  "routes": ["metrics"],
  "primary_gbn": "metrics",
  "confidence": 0.9
}
```

한 입력에 계산식과 조인 규칙이 함께 있으면 multi-route를 사용한다.

```json
{
  "routes": ["metrics", "join_rules"],
  "primary_gbn": "mixed"
}
```

## Built-in LLM Node

새 flow에는 커스텀 LLM caller가 없다. `Domain Item Prompt Template.prompt`는 `Message` 타입 출력이므로 Langflow 기본 LLM 노드의 prompt/chat message 입력에 연결한다. LLM 결과는 `Parse Domain Item JSON.llm_output`으로 연결한다.

`Domain Item Prompt Template.prompt_payload`는 `Data` 타입 보조 출력이다. built-in LLM 연결에는 보통 사용하지 않고, prompt 문자열 확인이나 커스텀 LLM 노드 연결이 필요할 때만 쓴다.

LLM은 JSON만 반환해야 한다.

```json
{
  "items": [
    {
      "gbn": "metrics",
      "source_note_id": "note_1",
      "key": "production_achievement_rate",
      "payload": {},
      "warnings": []
    }
  ],
  "unmapped_text": ""
}
```

## Knowledge Base 선택 사용

Knowledge Base는 기본 flow에는 넣지 않았다. 저장/충돌 검증은 MongoDB item collection이 정확한 기준이어야 하기 때문이다.

필요하면 아래 위치에 참고 문서 검색 결과를 추가할 수 있다.

```text
Knowledge Base Retriever.context
  -> Domain Item Prompt Template 또는 Langflow 기본 Prompt Template의 추가 context 변수
```

추천 용도는 "metric 작성 예시", "dataset column 설명", "도메인 작성 가이드" 같은 참고 자료 보강이다. 기존 item 조회, alias 충돌 검증, Main Flow domain payload 생성은 MongoDB 노드가 담당한다.

## Main Flow 연결

새 저장 구조를 Main Data Answer Flow에서 쓰려면 다음 loader를 사용한다.

```text
data_answer_flow / MongoDB Domain Item Payload Loader.domain_payload
  -> Build Intent Prompt.domain_payload
  -> Normalize Intent With Domain.domain_payload
  -> Query Mode Decider.domain_payload
```

legacy fragment loader인 `MongoDB Domain Payload Loader` 대신 item loader를 쓰는 것이 새 권장 방식이다.
