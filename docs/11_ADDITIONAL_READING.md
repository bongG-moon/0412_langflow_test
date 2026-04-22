# Additional Reading

Use this file as a small routing guide for the docs.

## To Change Agent Behavior

1. Read `.codex/harness/manufacturing-agent/HARNESS.md`.
2. Read `docs/02_BUILD_FLOW.md`.
3. Inspect `manufacturing_agent/graph/`.
4. Update focused tests under `tests/`.

## To Change Domain Rules

1. Read `docs/04_DOMAIN_AND_USAGE_GUIDE.md`.
2. Inspect `manufacturing_agent/domain/knowledge.py`.
3. Inspect `manufacturing_agent/domain/registry.py`.
4. Run registry and retrieval planner tests.

## To Change The UI

1. Read `docs/05_STREAMLIT_APP.md`.
2. Inspect `app.py`.
3. Inspect `manufacturing_agent/app/ui_renderer.py`.
4. Run UI sanitizer and end-to-end tests.

## To Build The Standalone Langflow Version

1. Read `docs/08_LANGFLOW_STANDALONE_IMPLEMENTATION_PLAN.md`.
2. Use `langflow/domain_item_authoring_flow` for domain item preprocessing and MongoDB storage.
3. Keep each Langflow custom component standalone.
4. Preserve the state keys for `intent`, `retrieval_plan`, `source_snapshots`, and `current_data`.
5. Validate single retrieval, follow-up analysis, required-parameter changes, and multi-dataset metrics.

## To Validate A Change

Run the focused unit tests first:

```powershell
python -m pytest tests
```
