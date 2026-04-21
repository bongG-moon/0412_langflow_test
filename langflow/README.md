# Standalone Langflow Components

This folder contains standalone Langflow custom components for the manufacturing data-analysis agent.

The current implementation covers the Data Answer Flow from session/domain loading through query mode decision, retrieval planning, dummy/Oracle source data loading, pandas post-processing, and final stateful answer assembly.

For the basic code-writing theory behind Langflow custom nodes, see `docs/16_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`.

## Available Flows

| Folder | Purpose |
| --- | --- |
| `data_answer_flow` | Runtime question answering flow. It loads active domain items from MongoDB, extracts intent, routes request type, decides query mode, retrieves source data, runs pandas analysis, and updates session state. |
| `domain_item_authoring_flow` | Preferred admin/preprocessing flow. It converts one raw domain note into item-level MongoDB documents. |
| `domain_authoring_flow` | Legacy admin/preprocessing flow. It converts raw domain notes into larger MongoDB domain fragments. |

Use `domain_item_authoring_flow` when you want to turn natural language domain notes, copied tables, partial JSON, filter definitions, formulas, and join rules into MongoDB domain items.

The default storage output of the preferred flow is:

```text
domain_item_authoring_flow / MongoDB Domain Item Saver.saved_items
```

The Main Flow can then load active items directly with:

```text
data_answer_flow / MongoDB Domain Item Payload Loader.domain_payload
```

## Data Answer Flow Order

Use this custom helper input when your Langflow build does not show a built-in multiline text input:

1. `00_previous_state_json_input.py`

Use built-in Langflow inputs only for values that are already easy to enter:

| Label in this guide | Langflow node to add | Value |
| --- | --- | --- |
| `Chat Input` | built-in Chat Input or Text Input | Current user question |
| `Session ID Text Input` | built-in Text Input | Session id such as `default`; optional |

Then connect the custom components in this order:

```text
00_previous_state_json_input.py
01_session_state_loader.py
10_mongodb_domain_item_payload_loader.py
02_main_flow_context_builder.py
03_build_intent_prompt.py
built-in LLM node
05_parse_intent_json.py
06_normalize_intent_with_domain.py
07_request_type_router.py
08_query_mode_decider.py
11_retrieval_plan_builder.py
12_dummy_data_retriever.py or 13_oracledb_data_retriever.py
14_analysis_base_builder.py
15_build_pandas_analysis_prompt.py
built-in LLM node
16_parse_pandas_analysis_json.py
17_execute_pandas_analysis.py
18_build_answer_prompt.py
built-in LLM node
19_final_answer_builder.py
```

For user-facing Playground output, connect:

```text
Final Answer Builder.answer_message
-> Chat Output
```

Use `Final Answer Builder.final_result` only when you need the full JSON/Data payload for debugging or downstream state handling.

For the detailed post-query-mode wiring, see:

```text
langflow/data_answer_flow/README.md
```

`10_mongodb_domain_item_payload_loader.py` replaces `00_domain_json_input.py -> 02_domain_json_loader.py` for the MongoDB-based Main Flow. It loads active item-level documents saved by `domain_item_authoring_flow` and returns the same `domain_payload` shape expected by the downstream nodes.

`00_domain_json_input.py` and `02_domain_json_loader.py` remain available only as a manual/local fallback when you want to test with pasted JSON instead of MongoDB.

`09_mongodb_domain_payload_loader.py` remains available as a legacy fragment loader for data saved by the older `domain_authoring_flow`.

## Wiring Contract

All custom component-to-component links in this flow use Langflow `Data`/`JSON` ports. The helper input nodes do not need a value before wiring; if a link is disabled in the canvas, refresh/reload the custom components so Langflow re-reads the updated port metadata.

The current Main Flow uses `02_main_flow_context_builder.py` to reduce canvas clutter. Connect the MongoDB domain payload and session state into this node once, then pass `main_context` into the first intent nodes. Downstream nodes propagate `main_context` inside their payloads, so repeated direct `domain_payload` edges are no longer required.

Connections to build:

| From | To | Required |
| --- | --- | --- |
| `Chat Input` | `Session State Loader.user_question` | Yes |
| `Chat Input` | `Main Flow Context Builder.user_question` | Yes |
| `Previous State JSON Input.previous_state_payload` | `Session State Loader.previous_state_payload` | Yes |
| `Session ID Text Input` | `Session State Loader.session_id` | Optional |
| `Session State Loader.agent_state` | `Main Flow Context Builder.agent_state` | Yes |
| `MongoDB Domain Item Payload Loader.domain_payload` | `Main Flow Context Builder.domain_payload` | Yes |
| `Main Flow Context Builder.main_context` | `Build Intent Prompt.main_context` | Yes |
| `Main Flow Context Builder.main_context` | `Normalize Intent With Domain.main_context` | Yes |
| `Build Intent Prompt.prompt` | built-in LLM prompt/chat input | Yes |
| built-in LLM output | `Parse Intent JSON.llm_result` | Yes |
| `Parse Intent JSON.intent_raw` | `Normalize Intent With Domain.intent_raw` | Yes |
| `Normalize Intent With Domain.intent` | `Request Type Router.intent` | Yes |
| `Request Type Router.data_question` | `Query Mode Decider.intent` | Yes for data branch |
| `Query Mode Decider.query_mode_decision` | `Retrieval Plan Builder.query_mode_decision` | Yes |
| `Retrieval Plan Builder.retrieval_plan` | `Dummy Data Retriever.retrieval_plan` or `OracleDB Data Retriever.retrieval_plan` | Yes |
| `Dummy/Oracle Data Retriever.retrieval_result` | `Analysis Base Builder.retrieval_result` | Yes |

Same connections as compact from/to pairs:

```text
Chat Input
-> Session State Loader.user_question

Chat Input
-> Main Flow Context Builder.user_question

Previous State JSON Input
-> Session State Loader.previous_state_payload

Session State Loader.agent_state
-> Main Flow Context Builder.agent_state

MongoDB Domain Item Payload Loader.domain_payload
-> Main Flow Context Builder.domain_payload

Main Flow Context Builder.main_context
-> Build Intent Prompt.main_context

Main Flow Context Builder.main_context
-> Normalize Intent With Domain.main_context

Build Intent Prompt.prompt
-> built-in LLM prompt/chat input

built-in LLM output
-> Parse Intent JSON.llm_result

Parse Intent JSON.intent_raw
-> Normalize Intent With Domain.intent_raw

Normalize Intent With Domain.intent
-> Request Type Router.intent

Request Type Router.data_question
-> Query Mode Decider.intent

Query Mode Decider.query_mode_decision
-> Retrieval Plan Builder.query_mode_decision

Retrieval Plan Builder.retrieval_plan
-> Dummy Data Retriever.retrieval_plan

Dummy Data Retriever.retrieval_result
-> Analysis Base Builder.retrieval_result
```

Manual JSON fallback:

```text
Domain JSON Input.domain_json_payload
  -> Domain JSON Loader.domain_json_payload

Domain JSON Loader.domain_payload
  -> Main Flow Context Builder.domain_payload
```

For MongoDB-based domain storage, keep the same `Database Name` and `Collection Name` values in these nodes:

```text
domain_item_authoring_flow / MongoDB Existing Domain Item Loader
domain_item_authoring_flow / MongoDB Domain Item Saver
data_answer_flow / MongoDB Domain Item Payload Loader
```

`datagov` is the default MongoDB database name. The default item collection name is `manufacturing_domain_items`. If you want to store domain items somewhere else, change the advanced `Database Name` or `Collection Name` inputs in all three nodes.

Some direct state/domain/question inputs remain available as legacy advanced inputs for local tests. In the current canvas, prefer `Main Flow Context Builder.main_context` and the propagated payloads instead of wiring repeated `domain_payload` edges.

Legacy/custom LLM fallback:

```text
Build Intent Prompt.intent_prompt
  -> LLM JSON Caller.prompt

LLM JSON Caller.llm_result
  -> Parse Intent JSON.llm_result
```

Use this fallback only when you need the custom `04_llm_json_caller.py` node to call `langchain_google_genai.ChatGoogleGenerativeAI` directly. The default Main Flow should use Langflow's built-in LLM node.

`MongoDB Domain Item Payload Loader` exposes `domain_payload` as the Main Flow domain source. `domain_payload` carries the merged domain document, detailed domain definitions, `domain_index`, domain loading errors, and MongoDB load status. Downstream nodes read `domain_index` from this payload, so no separate `domain_index` edge is needed.

`Domain JSON Loader` also exposes `domain_payload`, but it is now only the manual fallback for local JSON tests.

`LLM JSON Caller.llm_text` is accepted only as a defensive/manual fallback in `Parse Intent JSON`; the implemented custom caller output is `llm_result`.

You can still skip `00_previous_state_json_input.py` and type directly into `Session State Loader.previous_state_json`. The helper input node is provided so the field is visible as a separate canvas node.

When the built-in LLM path is used, API key, provider, model, and temperature are configured in the built-in LLM node. The custom `04_llm_json_caller.py` still receives its own `llm_api_key`, `model_name`, `temperature`, and `timeout_seconds` inputs, but it is now an optional fallback instead of the default path.

## Domain JSON Fallback Sample

Use this sample only when testing the manual JSON fallback path:

```text
reference_materials/domain_json_examples/phase1_domain_input_example.json
```
