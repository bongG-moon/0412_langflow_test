# langflow_version 안내

`langflow_version`은 현재 분기형 Langflow 노드가 공통으로 사용하는 helper 레이어만 남겨둔 디렉터리입니다.

## 현재 남는 이유

- Langflow `Data` payload를 일관되게 읽고 쓰기 위한 helper가 필요합니다.
- 세션 메모리 노드가 초기 state를 만들 때 공통 초기화 로직을 재사용합니다.
- 코어 제조 로직은 `manufacturing_agent/`에 두고, Langflow 전용 glue code만 따로 유지합니다.

## 현재 주요 파일

- `component_base.py`
  - `read_state_payload`
  - `make_data`
  - `make_branch_data`
- `workflow.py`
  - 세션 메모리에서 재사용하는 초기 state 생성 helper

## 현재 사용 방식

이 디렉터리는 더 이상 단일 통합 노드나 압축형 단계 노드를 제공하지 않습니다.

현재 Langflow에서는 아래와 같은 분기 가시형 구조만 기준으로 사용합니다.

- `Chat Input`
- `Manufacturing Session Memory`
- `Extract Manufacturing Params`
- `Decide Manufacturing Query Mode`
- `Route Manufacturing Query Mode`
- `Plan Manufacturing Datasets`
- `Build Manufacturing Jobs`
- `Route Manufacturing Retrieval Plan`
- `Execute Manufacturing Jobs`
- `Route Single/Multi Post Processing`
- `Build ... Response` 또는 `Run ... Analysis`
- `Merge Final Manufacturing Result`

자세한 배선은 아래 문서를 보면 됩니다.

- [../docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md](../docs/06_BRANCH_VISIBLE_LANGFLOW_FLOW.md)
- [../docs/07_LANGFLOW_CANVAS_SETUP.md](../docs/07_LANGFLOW_CANVAS_SETUP.md)
- [../docs/08_MULTITURN_CHAT_FLOW.md](../docs/08_MULTITURN_CHAT_FLOW.md)
