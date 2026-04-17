# Local Skills

This repository keeps a few local Codex skills under `.codex/skills/`.

## Available Project Skills

- `manufacturing-agent-harness`
  - Use when invoking, porting, or changing the agent while preserving state,
    routing, and final payload behavior.
- `manufacturing-domain-authoring`
  - Use when adding or validating manufacturing domain rules, aliases, dataset
    keywords, or analysis rules.
- `manufacturing-regression-check`
  - Use when validating behavior after changes to graph, services, UI, or other
    wrappers.

## Baseline Rule

Before changing behavior, read the harness:

```text
.codex/harness/manufacturing-agent/HARNESS.md
```

If a stable behavior rule changes, update the harness and the relevant skill in
the same change set.
