---
name: manufacturing-regression-check
description: Use when validating that changes to LangGraph, Langflow, Streamlit, Codex CLI, or another wrapper still preserve the manufacturing agent's core branch behavior, payload shape, and multi-turn semantics.
---

# Manufacturing Regression Check

Use this skill for behavior verification after changes or migrations.

## Workflow

1. Read `../../harness/manufacturing-agent/references/validation-checklist.md`.
2. Run at least:
   - one single-retrieval case
   - one follow-up case
   - one multi-dataset case
   - one first-turn post-analysis case
3. Confirm branch choice and final payload shape.
4. Record mismatches as routing, session, or response-contract issues.

## What Matters Most

- same branch choice
- same final `response`
- same `current_data` persistence
- same session reuse behavior

## Rule

A wrapper is not "compatible" just because it returns some answer.
It should preserve the harness contract closely enough that later turns and downstream tools still behave the same way.
