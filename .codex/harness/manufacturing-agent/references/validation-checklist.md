# Validation Checklist

Use this checklist after changes, ports, or migrations.

## Core Behavior

1. Single retrieval question
   - `어제 D/A3 생산 보여줘`
2. Follow-up question on the same session
   - `그 결과를 MODE별로 정리해줘`
3. Multi-dataset question
   - `오늘 생산과 목표를 같이 보여줘`
4. First-turn post-processing question
   - `오늘 DA공정에서 MODE별 생산량 알려줘`

## What To Verify

- query mode routing is correct
- retrieval plan routing is correct
- single vs multi branch selection is correct
- direct response vs post-analysis routing is correct
- final `response` is present
- `current_data` is preserved for follow-up
- `chat_history` and `context` are persisted across turns when sessions are enabled

## Failure Signals

- fresh retrieval happens when follow-up was expected
- output shape is missing `response` or `current_data`
- branch-visible flow produces multiple conflicting finals
- tool-specific wrapper changes the routing order

## Acceptance Rule

If the ported tool preserves branch choice, final payload shape, and follow-up behavior for the above cases, it is close enough to the repository baseline.
