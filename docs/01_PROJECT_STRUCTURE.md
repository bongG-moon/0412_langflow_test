# Project Structure

The repository is organized around one core package, one main UI, and a
standalone Langflow surface.

```text
project_root/
|-- manufacturing_agent/
|-- langflow/
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

## Langflow

`langflow/` contains standalone custom components and helper UIs.

- `data_answer_flow/`: main Langflow question-answering flow
- `domain_item_authoring_flow/`: domain item preprocessing and MongoDB save flow
- `registration_web/`: Streamlit UI for domain item and table catalog metadata registration

In the current table catalog design, SQL is not stored in table catalog JSON.
Table catalog items provide dataset/source metadata, required params, format
params, and columns. Oracle SQL is kept inside each `get_*` retriever function.

## Tests

`tests/` verifies the core branch behavior, prompt construction, retrieval
planning, domain registry behavior, UI sanitizing, and end-to-end examples.

## Operating Notes

`.codex/harness/manufacturing-agent/` defines the behavior contract that should
stay stable across changes.
