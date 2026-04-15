# Langflow Standalone Components

이 폴더의 개별 노드 파일은 Langflow Desktop custom component 코드 편집기에
그대로 붙여넣을 수 있는 standalone 정본입니다.

중요 규칙:

- `domain_rules.py` 같은 루트 노드 파일 자체가 정본입니다.
- 각 노드 파일 안에 runtime bootstrap과 필요한 내부 로직이 같이 들어 있습니다.
- 즉, `langflow_custom_component.*` 같은 외부 패키지 import 없이도 동작하도록 만든 상태가 기준입니다.
- `_runtime`, `component_base.py`, `workflow.py`, `node_utils.py` 등은 유지보수와 생성 스크립트 지원용입니다.
- `paste_ready/` 는 루트 노드 파일을 다시 모아둔 mirror 입니다.

관련 파일:

- flow import JSON: `manufacturing_langflow_import.json`
- flow JSON 생성: `../scripts/generate_langflow_import.py`
- standalone mirror 생성: `../scripts/export_standalone_langflow_nodes.py`
