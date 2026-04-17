# Project Structure

This project is now centered on the LangGraph-based manufacturing agent and the
Streamlit UI that calls it.

```text
project_root/
|-- manufacturing_agent/
|   |-- agent.py
|   |-- graph/
|   |-- services/
|   |-- data/
|   |-- analysis/
|   |-- domain/
|   |-- app/
|   `-- shared/
|-- app.py
|-- docs/
|-- reference_materials/
|-- tests/
|-- .codex/
|-- requirements.txt
`-- README.md
```

## `manufacturing_agent`

Core implementation of the manufacturing data-analysis agent.

- `agent.py`: public entrypoints, including `run_agent` and
  `run_agent_with_progress`
- `graph/`: LangGraph state, branch routing, and graph construction
- `graph/nodes/`: graph node implementations
- `services/`: parameter resolution, query-mode decisions, retrieval planning,
  response building, and runtime orchestration helpers
- `data/`: mock/synthetic manufacturing dataset retrieval
- `analysis/`: pandas-based post-analysis and safe execution support
- `domain/`: manufacturing domain knowledge and registry rules
- `shared/`: common formatting, filtering, config, and sanitizing helpers
- `app/`: Streamlit rendering helpers

## `app.py`

Streamlit chat UI. It calls `manufacturing_agent.agent.run_agent_with_progress`
and persists `chat_history`, `context`, and `current_data` in session state.

## `tests`

Focused regression tests for routing, source snapshots, retrieval planning,
response prompts, domain registry behavior, UI sanitizing, and end-to-end
examples.

## `.codex`

Local operating notes for agents working on this repository.

- `harness/manufacturing-agent/`: canonical state and routing contract
- `skills/`: task-specific local instructions for this repository

## `docs`

Human-facing project notes. Start with `docs/README.md` or
`docs/00_START_HERE.md`.
