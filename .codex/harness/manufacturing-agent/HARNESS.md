# Manufacturing Agent Harness

Use this harness when Codex CLI or another tool needs to preserve the behavior
of this repository's manufacturing data-analysis agent.

## Goal

Preserve the same execution semantics across supported surfaces:

- same state contract
- same routing order
- same retrieval planning rules
- same follow-up behavior
- same response payload shape
- same session persistence expectations

## Non-Negotiables

1. Prefer repository entrypoints over reimplementing business logic.
2. Treat LangGraph routing as the canonical decision model.
3. Preserve `chat_history`, `context`, and `current_data` for multi-turn
   behavior.
4. Keep final payloads centered on `response`, `tool_results`, `current_data`,
   and `extracted_params`.
5. Validate representative regression prompts before considering behavior
   changes done.
6. If a stable behavior rule changes, update this harness and the relevant
   skill files in the same change set.

## Preferred Entry Points

- `manufacturing_agent/agent.py::run_agent_with_progress`
- `manufacturing_agent/agent.py::run_agent`

## Canonical Branch Logic

Preserve this sequence:

1. resolve request
2. route query mode
3. if retrieval, plan datasets/jobs
4. route finish vs single vs multi
5. execute retrieval
6. route direct response vs post-analysis inside runtime services
7. finish response

## Session Handling

Always preserve:

- `chat_history`
- `context`
- `current_data`

If a runtime surface does not natively support sessions, emulate them with a
persisted state snapshot keyed by session id.

## References

- `references/state-contract.md`
- `references/routing-contract.md`
- `references/validation-checklist.md`
