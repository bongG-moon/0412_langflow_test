---
name: manufacturing-domain-authoring
description: Use when adding, reviewing, or validating manufacturing domain rules, aliases, dataset keywords, or analysis rules so they fit the repository's current domain registry and execution flow.
---

# Manufacturing Domain Authoring

Use this skill for domain registration and domain-rule edits.

## Workflow

1. Decide whether the request can be handled through domain registration or needs code changes.
2. Prefer no-code/domain-registration changes first.
3. When authoring rules, be explicit about:
   - datasets
   - source columns
   - formula or condition
   - output column
   - grouping intent
4. Check how the rule affects:
   - parameter extraction
   - retrieval planning
   - analysis planning
5. Validate with a before/after question pair.
6. For metric rules, ensure aliases cover common spelling variants and that
   `required_datasets` contains every dataset needed by the formula. Matched
   metric `required_datasets` must expand the retrieval plan before branch
   selection.

## Use This For

- dataset keyword additions
- value group aliases
- calculation rules
- decision or threshold rules
- domain-guided question refinement

## Avoid

- changing core code when a domain rule is enough
- adding vague rules without datasets or columns
- introducing a rule name or alias that collides with an existing meaning
