# Paste-Ready Langflow Nodes

이 폴더의 `.py` 파일은 Langflow Desktop의 custom component 코드 편집기에
그대로 붙여넣을 수 있도록 standalone 형태로 생성한 버전입니다.

주의:
- 현재 `langflow_custom_component/*.py` 자체가 standalone 정본입니다.
- 이 폴더는 그 정본을 다시 모아둔 mirror 입니다.
- 파일이 크기 때문에 저장 후 Langflow가 다시 로드하는 데 시간이 조금 걸릴 수 있습니다.
- `LLM_API_KEY` 같은 환경변수는 Langflow Desktop 실행 환경에 따로 넣어야 합니다.

생성 스크립트:
- `python scripts/export_standalone_langflow_nodes.py`

대상 노드:
- `domain_rules.py`
- `domain_registry.py`
- `session_memory.py`
- `extract_params.py`
- `decide_mode.py`
- `route_mode.py`
- `run_followup.py`
- `plan_datasets.py`
- `build_jobs.py`
- `route_plan.py`
- `exec_jobs.py`
- `route_single.py`
- `route_multi.py`
- `build_single.py`
- `analyze_single.py`
- `build_multi.py`
- `analyze_multi.py`
- `merge_final.py`
