---
name: manufacturing-agent-harness
description: Use when implementing, invoking, or porting the manufacturing agent into Codex CLI or another agentic tool while preserving the repository's canonical state model, routing order, multi-turn behavior, and final result payload.
---

# Manufacturing Agent Harness

Use this skill when the task is to make another tool behave like this repository's manufacturing agent.

## Workflow

1. Read `../../harness/manufacturing-agent/HARNESS.md`.
2. Read `../../harness/manufacturing-agent/references/state-contract.md`.
3. Read `../../harness/manufacturing-agent/references/routing-contract.md`.
4. Prefer calling repo entrypoints instead of rebuilding logic.
5. If direct execution is impossible, preserve the same state keys and branch order.
6. Validate with `../../harness/manufacturing-agent/references/validation-checklist.md`.
7. If you discover a new stable rule while fixing errors or changing direction, update the harness and any affected skill files before closing the task.

## Preferred Entrypoints

- `manufacturing_agent/agent.py::run_agent_with_progress`
- `manufacturing_agent/agent.py::run_agent`
- `langflow_version/workflow.py::run_langflow_workflow`

## Non-Negotiables

- Do not invent a new routing policy.
- Do not drop `chat_history`, `context`, or `current_data` in multi-turn flows.
- Preserve final payload shape centered on `response`, `tool_results`, `current_data`, and `extracted_params`.
- If you add a UI or wrapper, keep the wrapper thin and reuse repo logic.
- Do not leave harness or skill docs stale when the implementation meaningfully changes.
