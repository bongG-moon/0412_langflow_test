# Build Flow

The agent flow is intentionally small and explicit. LangGraph is the canonical
source of branch behavior.

## Branch Order

1. `resolve_request`
   - Extract required parameters.
   - Decide whether the turn can reuse `current_data`.
2. Route after resolve.
   - `followup_analysis` when the question is a same-context transform.
   - `plan_retrieval` for fresh or changed-scope retrieval.
3. `plan_retrieval`
   - Select required dataset keys.
   - Build retrieval jobs.
   - Return an early result if planning cannot continue.
4. Route after planning.
   - `finish`
   - `single_retrieval`
   - `multi_retrieval`
5. Retrieval and post-analysis.
   - Single retrieval handles one source path.
   - Multi retrieval merges multiple source paths.
   - Post-analysis handles grouping, aggregation, and table transforms.
6. `finish`
   - Normalize the final payload.

## Key Rule

Do not change routing order casually. Follow-up behavior depends on feeding back
`chat_history`, `context`, and `current_data` exactly enough for the query-mode
service to distinguish "same data, new view" from "new data needed".

## Main Files

- `manufacturing_agent/graph/builder.py`
- `manufacturing_agent/graph/state.py`
- `manufacturing_agent/graph/nodes/resolve_request.py`
- `manufacturing_agent/graph/nodes/plan_retrieval.py`
- `manufacturing_agent/graph/nodes/retrieve_single.py`
- `manufacturing_agent/graph/nodes/retrieve_multi.py`
- `manufacturing_agent/graph/nodes/followup_analysis.py`
- `manufacturing_agent/graph/nodes/finish.py`
