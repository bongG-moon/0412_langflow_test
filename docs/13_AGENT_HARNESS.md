# Agent Harness

The harness records the behavior that should remain stable when the
manufacturing agent changes.

Source of truth:

- `.codex/harness/manufacturing-agent/HARNESS.md`
- `.codex/harness/manufacturing-agent/references/state-contract.md`
- `.codex/harness/manufacturing-agent/references/routing-contract.md`
- `.codex/harness/manufacturing-agent/references/validation-checklist.md`

## Canonical Entrypoints

- `manufacturing_agent.agent.run_agent`
- `manufacturing_agent.agent.run_agent_with_progress`

## Stable Contract

Preserve:

- state keys
- routing order
- multi-turn context handling
- final payload shape

The most important payload fields are `response`, `tool_results`,
`current_data`, and `extracted_params`.

## Validation

Use representative cases for:

- single retrieval
- follow-up transform
- multi-dataset retrieval
- first-turn post-analysis

The validation checklist in `.codex/harness/manufacturing-agent/references/`
contains the detailed prompts and expectations.
