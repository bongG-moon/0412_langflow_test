# Start Here

This repository implements a manufacturing data-analysis chat agent.

The canonical execution path is the LangGraph graph in
`manufacturing_agent/graph/`. The Streamlit app in `app.py` is a UI surface that
calls the same agent entrypoint used by tests and other Python callers.

## What To Read First

1. `README.md` for the shortest project overview.
2. `docs/01_PROJECT_STRUCTURE.md` for directory ownership.
3. `docs/02_BUILD_FLOW.md` for the branch order.
4. `.codex/harness/manufacturing-agent/HARNESS.md` before changing behavior.

## Core State

The agent carries these values through a turn:

- `user_input`
- `chat_history`
- `context`
- `current_data`
- `extracted_params`
- `query_mode`
- `retrieval_plan`
- `retrieval_jobs`
- `result`

For multi-turn behavior, preserve `chat_history`, `context`, and
`current_data`. Dropping one of them can turn a follow-up question into an
incorrect fresh retrieval.

## Runtime Summary

```text
user question
-> resolve_request
-> route follow-up vs retrieval
-> plan_retrieval
-> route finish vs single vs multi
-> retrieve / analyze
-> finish
```

The final result payload should keep `response`, `tool_results`,
`current_data`, and `extracted_params` when available.
