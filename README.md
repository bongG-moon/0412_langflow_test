# Manufacturing Data Analysis Agent

This repository contains a manufacturing data-analysis agent whose canonical
runtime is the `manufacturing_agent` package. The agent uses LangGraph for
request resolution, retrieval planning, retrieval execution, follow-up analysis,
and final response assembly.

The remaining runnable surfaces are:

- Python entrypoints in `manufacturing_agent/agent.py`
- Streamlit UI in `app.py`
- Tests under `tests/`
- Project operating notes under `.codex/`

Legacy visual-canvas component wrappers, generated standalone node files,
import JSON, session-store artifacts, and their tests/docs have been removed.

## Quick Start

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the Streamlit app from the repository root:

```powershell
streamlit run app.py
```

Call the agent directly from Python:

```python
from manufacturing_agent.agent import run_agent

result = run_agent("show D/A3 production")
print(result["response"])
```

## Main Layout

```text
project_root/
|-- manufacturing_agent/
|   |-- agent.py
|   |-- graph/
|   |-- services/
|   |-- data/
|   |-- analysis/
|   |-- domain/
|   |-- shared/
|   `-- app/
|-- app.py
|-- docs/
|-- reference_materials/
|-- tests/
|-- .codex/
|-- requirements.txt
`-- PROJECT_STRUCTURE.md
```

## Runtime Shape

The high-level flow is:

1. Resolve the user request and required parameters.
2. Decide whether this is a new retrieval or a follow-up transform.
3. Plan the required dataset access.
4. Execute single or multi-dataset retrieval.
5. Run post-analysis when the question requires grouping or calculation.
6. Build the final response payload.

The final payload is centered on `response`, `tool_results`, `current_data`,
and `extracted_params`, so multi-turn callers can preserve context safely.

## Useful Docs

- `docs/00_START_HERE.md`
- `docs/01_PROJECT_STRUCTURE.md`
- `docs/02_BUILD_FLOW.md`
- `docs/03_FUNCTION_GUIDE.md`
- `docs/04_DOMAIN_AND_USAGE_GUIDE.md`
- `docs/05_STREAMLIT_APP.md`
- `.codex/harness/manufacturing-agent/HARNESS.md`
