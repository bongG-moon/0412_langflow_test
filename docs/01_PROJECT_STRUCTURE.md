# Project Structure

The repository is organized around one core package and one UI.

```text
project_root/
|-- manufacturing_agent/
|-- app.py
|-- docs/
|-- tests/
|-- reference_materials/
|-- .codex/
|-- requirements.txt
`-- README.md
```

## Core Package

`manufacturing_agent/` contains all runtime behavior.

- `agent.py`: public entrypoints
- `graph/`: LangGraph state, builder, routing, and nodes
- `services/`: application services used by graph nodes
- `data/`: retrieval source generation and filtering
- `analysis/`: pandas post-analysis and LLM analysis planning
- `domain/`: manufacturing domain vocabulary, aliases, and registry
- `shared/`: utility modules
- `app/`: Streamlit rendering helpers

## UI

`app.py` provides the Streamlit chat experience. It stores conversation context
in Streamlit session state and calls `run_agent_with_progress`.

## Tests

`tests/` verifies the core branch behavior, prompt construction, retrieval
planning, domain registry behavior, UI sanitizing, and end-to-end examples.

## Operating Notes

`.codex/harness/manufacturing-agent/` defines the behavior contract that should
stay stable across changes.
