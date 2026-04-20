# Standalone Langflow Components

This folder contains standalone Langflow custom components for the manufacturing data-analysis agent.

The current implementation covers the Data Answer Flow from session/domain loading through query mode decision. Retrieval planning, data query execution, pandas analysis, and final answer generation are intentionally left for later phases.

For the basic code-writing theory behind Langflow custom nodes, see `docs/16_LANGFLOW_CUSTOM_NODE_CODE_GUIDE.md`.

## Data Answer Flow Order

Use these custom helper inputs when your Langflow build does not show a built-in multiline text input:

1. `00_domain_json_input.py`
2. `00_previous_state_json_input.py`

Use built-in Langflow inputs only for values that are already easy to enter:

| Label in this guide | Langflow node to add | Value |
| --- | --- | --- |
| `Chat Input` | built-in Chat Input or Text Input | Current user question |
| `Session ID Text Input` | built-in Text Input | Session id such as `default`; optional |

Then connect the custom components in this order:

```text
00_domain_json_input.py
00_previous_state_json_input.py
01_session_state_loader.py
02_domain_json_loader.py
03_build_intent_prompt.py
04_llm_json_caller.py
05_parse_intent_json.py
06_normalize_intent_with_domain.py
07_request_type_router.py
08_query_mode_decider.py
```

## Wiring Contract

All custom component-to-component links in this flow use Langflow `Data`/`JSON` ports. The helper input nodes do not need a value before wiring; if a link is disabled in the canvas, refresh/reload the custom components so Langflow re-reads the updated port metadata.

Connections to build:

| From | To | Required |
| --- | --- | --- |
| `Chat Input` | `Session State Loader.user_question` | Yes |
| `Chat Input` | `Build Intent Prompt.user_question` | Yes |
| `Chat Input` | `Normalize Intent With Domain.user_question` | Yes |
| `Previous State JSON Input.previous_state_payload` | `Session State Loader.previous_state_payload` | Yes |
| `Session ID Text Input` | `Session State Loader.session_id` | Optional |
| `Domain JSON Input.domain_json_payload` | `Domain JSON Loader.domain_json_payload` | Yes |
| `Session State Loader.agent_state` | `Build Intent Prompt.agent_state` | Yes |
| `Session State Loader.agent_state` | `Normalize Intent With Domain.agent_state` | Yes |
| `Session State Loader.agent_state` | `Request Type Router.agent_state` | Yes |
| `Domain JSON Loader.domain_payload` | `Build Intent Prompt.domain_payload` | Yes |
| `Domain JSON Loader.domain_payload` | `Normalize Intent With Domain.domain_payload` | Yes |
| `Domain JSON Loader.domain_payload` | `Query Mode Decider.domain_payload` | Yes |
| `Build Intent Prompt.intent_prompt` | `LLM JSON Caller.prompt` | Yes |
| `LLM JSON Caller.llm_result` | `Parse Intent JSON.llm_result` | Yes |
| `Parse Intent JSON.intent_raw` | `Normalize Intent With Domain.intent_raw` | Yes |
| `Normalize Intent With Domain.intent` | `Request Type Router.intent` | Yes |
| `Request Type Router.data_question` | `Query Mode Decider.intent` | Yes for data branch |

Same connections as a compact chain:

```text
Chat Input
  -> Session State Loader.user_question
  -> Build Intent Prompt.user_question
  -> Normalize Intent With Domain.user_question

Previous State JSON Input
  -> Session State Loader.previous_state_payload

Domain JSON Input
  -> Domain JSON Loader.domain_json_payload

Session State Loader.agent_state
  -> Build Intent Prompt.agent_state
  -> Normalize Intent With Domain.agent_state
  -> Request Type Router.agent_state

Domain JSON Loader.domain_payload
  -> Build Intent Prompt.domain_payload
  -> Normalize Intent With Domain.domain_payload
  -> Query Mode Decider.domain_payload

Build Intent Prompt.intent_prompt
  -> LLM JSON Caller.prompt

LLM JSON Caller.llm_result
  -> Parse Intent JSON.llm_result

Parse Intent JSON.intent_raw
  -> Normalize Intent With Domain.intent_raw

Normalize Intent With Domain.intent
  -> Request Type Router.intent

Request Type Router.data_question
  -> Query Mode Decider.intent
```

`Query Mode Decider.agent_state` is optional when the `Request Type Router.data_question` branch is connected, because that branch already carries `agent_state`. It is still safe to connect `Session State Loader.agent_state` directly as well.

Do not connect these for the current implementation:

```text
LLM JSON Caller.llm_text -> Parse Intent JSON.llm_text
```

`Domain JSON Loader` exposes only `domain_payload` as a visible output. `domain_payload` carries the domain document, detailed domain definitions, `domain_index`, and any domain parsing errors. Downstream nodes read `domain_index` from this payload, so no separate `domain_index` edge is needed.

`LLM JSON Caller.llm_text` is accepted only as a defensive/manual fallback in `Parse Intent JSON`; the implemented Langflow output is `llm_result`.

Use `00_domain_json_input.py` or the future Domain Authoring Flow output as the source for `Domain JSON Loader.domain_json_payload`. You can still skip `00_previous_state_json_input.py` and type directly into `Session State Loader.previous_state_json`. The helper input nodes are provided so the fields are visible as separate canvas nodes.

Each LLM caller receives its own `llm_api_key`, `model_name`, `temperature`, and `timeout_seconds` inputs. There is no shared LLM config node. The current implementation calls `langchain_google_genai.ChatGoogleGenerativeAI`, matching the LangGraph implementation style.

## Domain JSON Sample

Use this sample as the initial Domain JSON Input:

```text
reference_materials/domain_json_examples/phase1_domain_input_example.json
```
