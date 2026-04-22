# Function Guide

This guide maps the most important runtime functions.

## Public Entrypoints

- `manufacturing_agent.agent.run_agent`
  - Invokes the compiled LangGraph graph and returns the final `result`.
- `manufacturing_agent.agent.run_agent_with_progress`
  - Runs the same branch order in a UI-friendly way and emits progress updates.

## Graph

- `manufacturing_agent.graph.builder.get_agent_graph`
  - Builds the LangGraph graph.
- `manufacturing_agent.graph.builder.route_after_resolve`
  - Routes follow-up analysis vs retrieval planning.
- `manufacturing_agent.graph.builder.route_after_retrieval_plan`
  - Routes finish vs single retrieval vs multi retrieval.
- `manufacturing_agent.graph.state.AgentGraphState`
  - Typed state contract for graph execution.

## Services

- `services.parameter_service.resolve_required_params`
  - Extracts date, process, product, and grouping parameters.
- `services.query_mode.choose_query_mode`
  - Chooses retrieval vs follow-up transform.
- `services.retrieval_planner.plan_retrieval_request`
  - Chooses required datasets.
- `services.retrieval_planner.build_retrieval_jobs`
  - Converts a retrieval plan into executable jobs.
- `services.runtime_service.run_retrieval`
  - Runs single retrieval and optional post-processing.
- `services.runtime_service.run_multi_retrieval_jobs`
  - Runs multiple retrieval jobs and merges results.
- `services.runtime_service.run_followup_analysis`
  - Reuses `current_data` for follow-up table analysis.
- `services.response_service.generate_response`
  - Builds the assistant-facing response text.

## Domain And Data

- `domain.knowledge`
  - Manufacturing vocabulary and aliases.
- `domain.registry`
  - Registry entries and domain rule loading.
- `data.retrieval`
  - Synthetic dataset construction, filtering, and retrieval helpers.

## UI Helpers

- `manufacturing_agent.app.ui_renderer`
  - Streamlit chat rendering and session helpers.
- `manufacturing_agent.app.ui_domain_knowledge`
  - Domain registry management UI.
