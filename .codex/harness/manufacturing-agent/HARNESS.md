# Manufacturing Agent Harness

Use this harness when you need Codex CLI or another agentic tool to produce the same manufacturing-agent behavior that this repository already supports in LangGraph, Langflow, and Streamlit.

## Goal

Preserve the same execution semantics across tools:

- same state contract
- same routing order
- same retrieval planning rules
- same follow-up behavior
- same response payload shape
- same session persistence expectations

## Non-Negotiables

1. Prefer calling repository entrypoints over reimplementing business logic.
2. If you cannot call repo code directly, reproduce the state and routing contracts exactly.
3. Treat LangGraph routing as the canonical decision model.
4. Preserve `chat_history`, `context`, and `current_data` for multi-turn behavior.
5. Validate behavior with representative regression prompts before considering the task done.
6. If runtime errors, new branch behavior, or development-direction changes reveal a better operating rule, update this harness and the relevant skills in the same change set.

## Preferred Execution Order

1. Read `references/state-contract.md`.
2. Read `references/routing-contract.md`.
3. Decide whether you can call repo code directly.
4. Prefer one of these entrypoints:
   - `manufacturing_agent/agent.py::run_agent_with_progress`
   - `manufacturing_agent/agent.py::run_agent`
5. If you are building a branch-visible flow, preserve the canonical branch split:
   - follow-up vs retrieval
   - finish vs single vs multi
   - direct response vs post analysis
6. Run the validation checklist in `references/validation-checklist.md`.

## Preferred Entry Points

### Best option: direct orchestration

- `manufacturing_agent/agent.py::run_agent_with_progress`
- `manufacturing_agent/agent.py::run_agent`

Use this when the tool can run Python directly and you want the closest behavior to the current Streamlit app.

### Second option: branch-visible orchestration

Use the branch-visible Langflow-compatible structure only when you need step-by-step visibility, debugging, or external orchestration.

## Tool-Neutral Rules

### Session handling

Always preserve:

- `chat_history`
- `context`
- `current_data`

If a runtime does not natively support sessions, emulate them with a persisted JSON snapshot keyed by session id.

### Response shape

Aim to preserve the final result payload fields:

- `response`
- `tool_results`
- `current_data`
- `extracted_params`
- `awaiting_analysis_choice`
- metadata such as session or branch origin when helpful

### Error handling

When something fails, do not silently swap in a different routing policy.
Prefer:

1. preserve the current branch contract
2. return a controlled result payload when possible
3. log the failure context
4. retry only when the existing planner/runtime rules allow it

## When To Read Extra References

- Read `references/state-contract.md` whenever you need to port or reconstruct state.
- Read `references/routing-contract.md` whenever you need to preserve LangGraph-equivalent branching.
- Read `references/validation-checklist.md` whenever you need to confirm that another tool still behaves like the repository baseline.

## Relationship To Skills

This harness is the baseline operating contract.
The skills under `.codex/skills/` are reusable task-level instructions that assume this harness exists.

Use the harness to preserve system behavior.
Use the skills to speed up specific recurring tasks.

## Maintenance Rule

Treat this harness as a living contract.

Update it when:

- repeated migration or runtime issues reveal a missing rule
- branch or state behavior changes
- session handling rules change
- another tool integration requires a new invariant

When you update the harness, also review:

- relevant files under `.codex/skills/`
- `docs/12_LANGFLOW_MIGRATION_ISSUES.md`
- any human-facing docs that describe the changed behavior
