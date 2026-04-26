# Additional Reading

작업 목적별로 어떤 문서를 읽으면 좋은지 정리한 안내입니다.

## Agent 동작을 바꿀 때

1. `.codex/harness/manufacturing-agent/HARNESS.md`
2. `.codex/harness/manufacturing-agent/references/state-contract.md`
3. `.codex/harness/manufacturing-agent/references/routing-contract.md`
4. `docs/02_BUILD_FLOW.md`
5. `manufacturing_agent/graph/`

## Domain 규칙을 바꿀 때

1. `docs/04_DOMAIN_AND_USAGE_GUIDE.md`
2. `manufacturing_agent/domain/knowledge.py`
3. `manufacturing_agent/domain/registry.py`
4. `langflow_v2/registration_web/README.md`

## Streamlit UI를 바꿀 때

1. `docs/05_STREAMLIT_APP.md`
2. `app.py`
3. `manufacturing_agent/app/ui_renderer.py`

## Langflow v2 flow를 바꿀 때

1. `langflow_v2/README.md`
2. `langflow_v2/detail_desc/README.md`
3. 바꾸려는 노드 번호의 `langflow_v2/detail_desc/*.md`
4. 바꾸려는 노드의 `langflow_v2/*.py`
5. `langflow_v2/docs/02_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md`
6. `langflow_v2/docs/03_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`

## Langflow v2 domain 등록 웹을 바꿀 때

1. `langflow_v2/registration_web/README.md`
2. `langflow_v2/registration_web/app.py`
3. `langflow_v2/registration_web/services/domain_text_v2.py`
4. `langflow_v2/registration_web/services/table_text_v2.py`

## 검증할 때

먼저 전체 테스트를 실행합니다.

```powershell
python -m pytest -q
```

Langflow v2만 빠르게 확인할 때는 다음 테스트를 우선 실행합니다.

```powershell
python -m pytest tests/test_langflow_v2_simplified_flow.py tests/test_langflow_v2_registration_web.py -q
```
