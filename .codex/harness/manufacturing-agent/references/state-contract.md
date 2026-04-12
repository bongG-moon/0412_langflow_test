# State Contract

The manufacturing agent uses a shared state model so that LangGraph, Langflow, Streamlit, Codex CLI, and other tools can preserve the same semantics.

## Core Inputs

- `user_input`
- `chat_history`
- `context`
- `current_data`

## Common Derived Fields

- `extracted_params`
- `query_mode`
- `retrieval_plan`
- `retrieval_jobs`
- `source_results`
- `result`

## Multi-Turn Requirements

For a follow-up question to behave correctly, preserve and feed back:

- `chat_history`
- `context`
- `current_data`

If one of these is dropped, later turns may be misrouted as fresh retrievals instead of follow-up analysis.

## Result Payload Contract

The final payload should preserve these fields when available:

- `response`
- `tool_results`
- `current_data`
- `extracted_params`
- `awaiting_analysis_choice`

Optional metadata is allowed if it does not break downstream readers.

## Practical Rule

If you are porting this workflow to another tool, keep the state dictionary stable first.
Only then adapt the UI, canvas, or session mechanics around it.
