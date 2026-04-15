# Langflow Import Guide

Domain node input examples are documented in `docs/16_LANGFLOW_DOMAIN_INPUTS.md`.
LLM / data-tool 교체 포인트는 `docs/18_LANGFLOW_LLM_DATA_SWAP_GUIDE.md` 에 정리했습니다.

이 문서는 두 가지 사용 방식을 같이 안내합니다.

- `langflow_custom_component/manufacturing_langflow_import.json` 을 Langflow에 바로 import하는 방식
- Langflow Desktop에서 custom component 코드 편집기에 직접 붙여넣는 방식

이번 import 파일은 아래 기준으로 만들었습니다.

- LangGraph의 분기 순서를 그대로 보이게 유지
- `chat_history`, `context`, `current_data` 를 세션에 유지
- 각 노드 코드 안에 standalone bootstrap을 넣어서, 현재 저장소의 `.py` 파일을 Langflow가 직접 import하지 않아도 동작할 수 있게 구성
- `manufacturing_agent` 기준에서 이미 맞춰둔 query mode, retrieval planning, follow-up, raw snapshot 재사용 로직을 빠뜨리지 않음

## 준비 파일

- import flow JSON:
  `langflow_custom_component/manufacturing_langflow_import.json`
- JSON 재생성 스크립트:
  `scripts/generate_langflow_import.py`
- standalone 정본 노드:
  `langflow_custom_component/*.py`
- optional 미러 폴더:
  `langflow_custom_component/paste_ready/*.py`
- standalone 미러 스크립트:
  `scripts/export_standalone_langflow_nodes.py`

## 어떤 파일을 써야 하는지

- Langflow가 현재 저장소의 `.py` 파일을 직접 읽을 수 있거나, import JSON을 받아들이는 경우:
  `manufacturing_langflow_import.json`
- Langflow Desktop에서 custom component 코드 창에 직접 붙여넣는 경우:
  `langflow_custom_component/*.py` 파일을 그대로 사용
  필요하면 같은 내용의 미러인 `paste_ready` 폴더를 사용해도 됨

중요:
- 현재 `langflow_custom_component/*.py` 노드 파일 자체가 standalone 정본입니다.
- 각 노드 파일 안에는 runtime bootstrap과 필요한 내부 로직이 같이 들어 있습니다.
- 즉, Desktop의 코드 직접 붙여넣기 모드에서도 루트 노드 파일을 그대로 쓸 수 있어야 합니다.
- `paste_ready` 폴더는 같은 내용을 다시 모아둔 mirror 용도입니다.

## Import 순서

1. Langflow에서 새 Flow를 엽니다.
2. Import 메뉴에서 `langflow_custom_component/manufacturing_langflow_import.json` 파일을 선택합니다.
3. import 뒤에 각 노드 코드가 길게 들어가 있으므로 첫 로딩이 약간 느릴 수 있습니다.
4. 예전에 같은 이름의 테스트 노드를 직접 만들어 둔 적이 있으면, stale code를 피하려고 기존 노드는 지우고 새로 import한 flow만 남기는 편이 안전합니다.

## 캔버스 배치

이 flow는 7열 구조로 잡혀 있습니다.

- 1열
  `Domain Rules`, `Domain Registry`, `Chat Input`
- 2열
  `Session Memory`(load), `Extract Params`
- 3열
  `Decide Mode`, `Route Mode`
- 4열
  상단 `Run Followup`
  중앙 `Plan Datasets`
  하단 `Build Jobs`
  맨 아래 `Route Plan`
- 5열
  단일 조회 lane `Execute Jobs` -> `Route Single`
  다중 조회 lane `Execute Jobs` -> `Route Multi`
- 6열
  단일 direct lane `Build Single`
  단일 analysis lane `Analyze Single`
  다중 overview lane `Build Multi`
  다중 analysis lane `Analyze Multi`
- 7열
  `Merge Result`, `Session Memory`(save), `Chat Output`

## 정확한 연결 순서

아래 순서대로 선이 연결되어 있습니다.

1. `Domain Rules.rules` -> `Session Memory(load).domain_rules`
2. `Domain Registry.registry` -> `Session Memory(load).domain_registry`
3. `Chat Input.message` -> `Session Memory(load).message`
4. `Session Memory(load).state_out` -> `Extract Params.state`
5. `Extract Params.state_out` -> `Decide Mode.state`
6. `Decide Mode.state_out` -> `Route Mode.state`
7. `Route Mode.followup_out` -> `Run Followup.state`
8. `Run Followup.state_out` -> `Merge Result.followup_result`
9. `Route Mode.retrieval_out` -> `Plan Datasets.state`
10. `Plan Datasets.state_out` -> `Build Jobs.state`
11. `Build Jobs.state_out` -> `Route Plan.state`
12. `Route Plan.finish_out` -> `Merge Result.finish_result`
13. `Route Plan.single_out` -> `Execute Jobs(single).state`
14. `Execute Jobs(single).state_out` -> `Route Single.state`
15. `Route Single.direct_out` -> `Build Single.state`
16. `Build Single.state_out` -> `Merge Result.single_direct_result`
17. `Route Single.analysis_out` -> `Analyze Single.state`
18. `Analyze Single.state_out` -> `Merge Result.single_analysis_result`
19. `Route Plan.multi_out` -> `Execute Jobs(multi).state`
20. `Execute Jobs(multi).state_out` -> `Route Multi.state`
21. `Route Multi.overview_out` -> `Build Multi.state`
22. `Build Multi.state_out` -> `Merge Result.multi_overview_result`
23. `Route Multi.analysis_out` -> `Analyze Multi.state`
24. `Analyze Multi.state_out` -> `Merge Result.multi_analysis_result`
25. `Merge Result.result_out` -> `Session Memory(save).result`
26. `Domain Rules.rules` -> `Session Memory(save).domain_rules`
27. `Domain Registry.registry` -> `Session Memory(save).domain_registry`
28. `Chat Input.message` -> `Session Memory(save).message`
29. `Session Memory(save).saved_out` -> `Chat Output.input_value`

## 핵심 payload 예시

### 1. Chat Input.message

`Chat Input`은 Langflow 기본 `Message` 객체를 내보냅니다.

예시:

```json
{
  "text": "오늘 DA공정에서 DDR5 제품의 생산 달성율을 세부 공정별로 알려줘",
  "session_id": "demo-session-1"
}
```

### 2. Domain Rules.rules

예시:

```json
{
  "domain_rules_text": "HBM/3DS는 TSV 제품으로 간주하고, AUTO_PRODUCT 별칭도 같이 본다."
}
```

### 3. Domain Registry.registry

예시:

```json
{
  "domain_registry_payload": {
    "entries": [
      {
        "title": "custom achievement note",
        "analysis_rules": [
          {
            "name": "custom_achievement",
            "required_datasets": ["production", "target"],
            "formula": "production / target"
          }
        ]
      }
    ]
  }
}
```

### 4. Session Memory(load).state_out

이 노드부터는 대부분 `Data` 안에 `state` dict를 넣어서 넘깁니다.

예시:

```json
{
  "state": {
    "user_input": "오늘 DA공정에서 DDR5 제품의 생산 달성율을 세부 공정별로 알려줘",
    "chat_history": [],
    "context": {},
    "current_data": null,
    "domain_rules_text": "HBM/3DS는 TSV 제품으로 간주한다.",
    "domain_registry_payload": {},
    "session_id": "demo-session-1"
  }
}
```

### 5. Merge Result.result_out

최종 결과는 아래 형태를 중심으로 유지합니다.

```json
{
  "response": "오늘(2026-04-15) DDR5 제품의 DA 세부 공정별 생산 달성율은 ...",
  "tool_results": [
    {
      "dataset_key": "production"
    },
    {
      "dataset_key": "target"
    }
  ],
  "current_data": {
    "table": [
      {
        "OPER_NAME": "D/A1",
        "achievement_rate": 92.0
      }
    ],
    "source_snapshots": {
      "production": [],
      "target": []
    },
    "retrieval_applied_params": {
      "date": "20260415",
      "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
      "mode": ["DDR5"]
    }
  },
  "extracted_params": {
    "date": "20260415",
    "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
    "mode": ["DDR5"]
  }
}
```

## 노드별 설명

### Domain Rules

- 역할: 사용자가 자유 텍스트로 적은 도메인 메모를 payload로 감쌉니다.
- 입력: `domain_rules_text` 문자열
- 출력: `rules`
- 예시 입력: `HBM/3DS는 TSV 제품으로 본다`
- 예시 출력:

```json
{
  "domain_rules_text": "HBM/3DS는 TSV 제품으로 본다"
}
```

### Domain Registry

- 역할: web에서 저장해 둔 registry JSON을 직접 붙여 넣어 active registry payload로 만듭니다.
- 입력: `registry_json` 문자열 또는 JSON
- 출력: `registry`
- 예시 입력: `{"entries":[{"title":"DDR alias","dataset_keywords":[]}]}` 

### Chat Input

- 역할: 사용자 질문과 `session_id`를 flow 시작점으로 넣습니다.
- 입력: Langflow Playground 입력창
- 출력: `message`
- 실무 팁: 멀티턴 테스트를 하려면 같은 `session_id`를 유지해야 합니다.

### Session Memory

- 역할: load 인스턴스는 과거 세션을 읽고, save 인스턴스는 이번 턴 결과를 저장합니다.
- load 입력: `message`, `domain_rules`, `domain_registry`
- load 출력: `state_out`
- save 입력: `result`, `message`, `domain_rules`, `domain_registry`
- save 출력: `saved_out`
- 저장 위치 기본값: `.langflow_session_store`

### Extract Params

- 역할: 질문에서 date, process, mode, product 같은 retrieval parameter를 추출합니다.
- 입력: `state`
- 출력: `state_out`
- 내부 반영 포인트:
  `raw_extracted_params`
  `extracted_params`
  context 상속 결과

### Decide Mode

- 역할: 이번 턴이 새 조회인지, 현재 `current_data` 변환만 하면 되는 후속 질문인지 판단합니다.
- 입력: `state`
- 출력: `state_out`
- 대표 결과:
  `query_mode = "retrieval"`
  `query_mode = "followup_transform"`

### Route Mode

- 역할: query mode 분기를 Langflow의 출력 포트로 보이게 만듭니다.
- 입력: `state`
- 출력:
  `followup_out`
  `retrieval_out`

### Run Followup

- 역할: 이미 가지고 있는 `current_data`를 다시 필터링하거나 재집계하거나 raw snapshot으로 재시도해서 후속 질문을 처리합니다.
- 입력: `state`
- 출력: `state_out`
- 중요 포인트: 현재 결과표에 필요한 컬럼이 없으면 `source_snapshots`를 이용해서 재가공을 시도합니다.

### Plan Datasets

- 역할: 현재 질문에 필요한 dataset key를 정합니다.
- 입력: `state`
- 출력: `state_out`
- 예시 결과:

```json
{
  "retrieval_plan": {
    "dataset_keys": ["production", "target"]
  }
}
```

### Build Jobs

- 역할: dataset key와 extracted params를 실제 retrieval job 목록으로 만듭니다.
- 입력: `state`
- 출력: `state_out`
- 예시 결과:

```json
{
  "retrieval_jobs": [
    {
      "dataset_key": "production",
      "params": {
        "date": "20260415",
        "mode": ["DDR5"]
      }
    }
  ]
}
```

### Route Plan

- 역할: retrieval plan 결과를 `finish`, `single`, `multi` 세 갈래로 나눕니다.
- 입력: `state`
- 출력:
  `finish_out`
  `single_out`
  `multi_out`

### Execute Jobs

- 역할: `retrieval_jobs`를 실제 실행하고 정규화된 `source_results`를 state에 붙입니다.
- 입력: `state`
- 출력: `state_out`
- 단일 lane, 다중 lane 둘 다 같은 노드를 복제해서 씁니다.

### Route Single

- 역할: 단일 조회 결과가 바로 답변 가능한지, 추가 분석이 필요한지 나눕니다.
- 입력: `state`
- 출력:
  `direct_out`
  `analysis_out`

### Build Single

- 역할: 단일 조회 결과를 바로 사용자 답변으로 만듭니다.
- 입력: `state`
- 출력: `state_out`

### Analyze Single

- 역할: 단일 조회 결과에 대해 grouping, ratio 계산, 세부 공정별 재가공 같은 post-analysis를 수행합니다.
- 입력: `state`
- 출력: `state_out`

### Route Multi

- 역할: 다중 dataset 결과를 overview로 끝낼지, merge/analysis를 더 할지 나눕니다.
- 입력: `state`
- 출력:
  `overview_out`
  `analysis_out`

### Build Multi

- 역할: 다중 dataset 결과를 overview 응답으로 만듭니다.
- 입력: `state`
- 출력: `state_out`

### Analyze Multi

- 역할: 다중 dataset join, 계산식 적용, derived metric 계산을 수행합니다.
- 입력: `state`
- 출력: `state_out`

### Merge Result

- 역할: 여러 branch 중 실제로 값이 들어온 branch 하나를 최종 result payload로 합칩니다.
- 입력:
  `followup_result`
  `finish_result`
  `single_direct_result`
  `single_analysis_result`
  `multi_overview_result`
  `multi_analysis_result`
- 출력: `result_out`

### Chat Output

- 역할: `Session Memory(save).saved_out` 결과를 Langflow chat 화면에 보여줍니다.
- 입력: `input_value`
- 출력: 최종 Message

## 권장 검증 순서

아래 4개는 import 직후 꼭 확인하는 편이 좋습니다.

1. 단일 조회
   `오늘 DA공정 생산량 알려줘`
2. 후속 질문
   같은 `session_id`로 `그 결과를 MODE별로 정리해줘`
3. 다중 dataset
   `오늘 생산과 목표를 같이 보여줘`
4. 첫 턴 post-analysis
   `오늘 DA공정에서 DDR5 제품의 생산 달성율을 세부 공정별로 알려줘`

## 주의 사항

- `Session Memory`는 반드시 2개가 있어야 합니다.
  하나는 load, 하나는 save 용도입니다.
- `Execute Jobs`도 single lane, multi lane에 각각 1개씩 두는 편이 화면에서 분기가 잘 보입니다.
- Langflow가 예전 코드 snapshot을 잡고 있으면 새 JSON을 다시 import하는 것만으로 부족할 수 있습니다.
  그럴 때는 기존 flow나 기존 custom node 인스턴스를 지우고 다시 import하는 편이 안전합니다.
