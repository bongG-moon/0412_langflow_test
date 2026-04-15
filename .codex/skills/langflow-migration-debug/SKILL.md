---
name: langflow-migration-debug
description: Use when Langflow custom components for this repository fail to load, show the wrong port types, lose imports, keep stale code, or behave differently from the canonical manufacturing-agent flow.
---

# Langflow Migration Debug

Use this skill when debugging Langflow-specific failures in this repository.

## Workflow

1. Read `../../../docs/12_LANGFLOW_MIGRATION_ISSUES.md`.
2. Check whether the problem is:
   - component discovery
   - import / project root resolution
   - output type metadata
   - stale stored node code
   - direct-paste mode vs package-import mode mismatch
   - branch visibility mismatch
   - session persistence mismatch
3. Inspect the custom node under `custom_components/manufacturing_nodes/`.
4. Keep fixes thin and aligned with the canonical harness.
5. Re-test the specific failing branch or node path.

## High-Value Checks

- custom folder name conflicts with core package name
- repo root is not inserted into `sys.path`
- outputs are missing `types=["Data"], selected="Data"`
- old node instances still carry stale code snapshots
- branch-visible flow is missing merge or session nodes
- if the user is pasting code directly into Langflow Desktop, package-style imports like `langflow_custom_component.*` will fail unless the whole package exists in the Desktop components path; prefer standalone exported node files for direct-paste mode

## Rule

Do not "fix" Langflow by changing business logic first.
First confirm that the adapter layer still matches the repository baseline.
