# Routing Contract

The canonical routing behavior comes from the repository's LangGraph structure and related runtime helpers.

## Route 1: query mode

Decide whether the request is:

- `followup_transform`
- `retrieval`

Meaning:

- `followup_transform`: reuse `current_data` and transform the existing result
- `retrieval`: plan new dataset access

## Route 2: retrieval plan outcome

After planning retrieval, branch into one of:

- `finish`
- `single_retrieval`
- `multi_retrieval`

Typical meaning:

- `finish`: respond early because planning already determined the result or failure
- `single_retrieval`: one dataset or one retrieval path is enough
- `multi_retrieval`: multiple datasets or multiple retrieval passes are required

## Route 3: post-processing

After retrieval, branch into:

- `direct_response`
- `post_analysis`

For multi-retrieval this may appear as:

- `overview_response`
- `post_analysis`

## Canonical Branch Logic

Preserve this sequence:

1. resolve request
2. route query mode
3. if retrieval, plan datasets/jobs
4. route finish vs single vs multi
5. execute retrieval
6. route direct/overview vs post-analysis
7. finish response

Do not reorder these steps unless you are intentionally changing system behavior.
