# Langflow Manufacturing Flow

`langflow_v2/` is a standalone Langflow custom-component flow for the
manufacturing data-analysis agent. Each `.py` file is self-contained so it can
be registered directly in Langflow without importing sibling project modules.

Core rules:

- Do not use `langflow_v2.*` imports inside component files.
- Intent, retrieval, and postprocess branches are visible on the canvas.
- `LLM JSON Caller` is placed three times on the canvas:
  - `LLM JSON Caller (Intent)`
  - `LLM JSON Caller (Pandas)`
  - `LLM JSON Caller (Answer)`
- Single and multi retrieval branches use separate component instances, even
  when they use the same retriever file.

## Documentation Layout

- `README.md`: canvas connection map and full v2 flow contract.
- `detail_desc/`: beginner-friendly explanation for each numbered node.
- `docs/`: Langflow-specific planning and learning documents moved from the root `docs/` folder.
- `registration_web/README.md`: PKG Domain Registry web UI guide.

## Python File Order

| No. | File | Langflow Node | Role |
| --- | --- | --- | --- |
| 00 | `00_state_memory_extractor.py` | `State Memory Extractor` | Extract previous state from Langflow Message History |
| 01 | `01_state_loader.py` | `State Loader` | Build canonical state from question and previous state |
| 02 | `02_mongodb_domain_loader.py` | `MongoDB Domain Loader` | Load MongoDB domain rules |
| 03 | `03_domain_json_loader.py` | `Domain JSON Loader` | Load direct JSON domain rules |
| 04 | `04_table_catalog_loader.py` | `Table Catalog Loader` | Load dataset/tool catalog |
| 05 | `05_main_flow_filters_loader.py` | `Main Flow Filters Loader` | Load shared semantic filter definitions |
| 06 | `06_build_intent_prompt.py` | `Build Intent Prompt` | Build intent-classification prompt |
| 07 | `07_llm_json_caller.py` | `LLM JSON Caller` | Call LLM and return raw JSON text |
| 08 | `08_normalize_intent_plan.py` | `Normalize Intent Plan` | Normalize intent JSON and create route/retrieval jobs |
| 09 | `09_intent_route_router.py` | `Intent Route Router` | Split into single/multi/follow-up/finish branches |
| 10 | `10_dummy_data_retriever.py` | `Dummy Data Retriever` | Retrieve dummy data |
| 11 | `11_oracle_data_retriever.py` | `Oracle Data Retriever` | Retrieve Oracle DB data |
| 12 | `12_mongodb_data_loader.py` | `MongoDB Data Loader` | Load row lists back from MongoDB refs when needed |
| 13 | `13_current_data_retriever.py` | `Current Data Retriever` | Reuse `state.current_data` for follow-up analysis |
| 14 | `14_early_result_adapter.py` | `Early Result Adapter` | Convert finish/clarification branch to `analysis_result` |
| 15 | `15_retrieval_payload_merger.py` | `Retrieval Payload Merger` | Merge retrieval branches |
| 16 | `16_retrieval_postprocess_router.py` | `Retrieval Postprocess Router` | Split direct response vs pandas post-analysis |
| 17 | `17_direct_result_adapter.py` | `Direct Result Adapter` | Convert direct retrieval result to `analysis_result` |
| 18 | `18_build_pandas_prompt.py` | `Build Pandas Prompt` | Build pandas-code prompt |
| 19 | `19_normalize_pandas_plan.py` | `Normalize Pandas Plan` | Normalize pandas code plan |
| 20 | `20_pandas_analysis_executor.py` | `Pandas Analysis Executor` | Execute pandas code |
| 21 | `21_analysis_result_merger.py` | `Analysis Result Merger` | Merge early/direct/pandas results |
| 22 | `22_mongodb_data_store.py` | `MongoDB Data Store` | Store large row lists in MongoDB and keep compact refs |
| 23 | `23_build_final_answer_prompt.py` | `Build Final Answer Prompt` | Build final answer prompt from analysis result |
| 24 | `24_normalize_answer_text.py` | `Normalize Answer Text` | Normalize final-answer LLM JSON into answer text |
| 25 | `25_final_answer_builder.py` | `Final Answer Builder` | Build final payload, chat message with final data, and next state |
| 26 | `26_state_memory_message_builder.py` | `State Memory Message Builder` | Build a state snapshot message for Langflow Message History |

## Canvas Overview

```text
Message History (Retrieve, native Langflow)
  -> 00 State Memory Extractor
  -> 01 State Loader.previous_state

Chat Input
  -> 01 State Loader

02 MongoDB Domain Loader
  OR 03 Domain JSON Loader

04 Table Catalog Loader
05 Main Flow Filters Loader

01 + 02/03 + 04 + 05
  -> 06 Build Intent Prompt
  -> 07A LLM JSON Caller (Intent)
  -> 08 Normalize Intent Plan
  -> 09 Intent Route Router

09.single_retrieval
  -> 10A Dummy Retriever OR 11A Oracle Retriever
09.multi_retrieval
  -> 10B Dummy Retriever OR 11B Oracle Retriever
09.followup_transform
  -> 12 MongoDB Data Loader (optional, when current_data has data_ref)
  -> 13 Current Data Retriever
09.finish
  -> 14 Early Result Adapter

10A/11A + 10B/11B + 13
  -> 15 Retrieval Payload Merger
  -> 16 Retrieval Postprocess Router

16.direct_response
  -> 17 Direct Result Adapter
16.post_analysis
  -> 18 Build Pandas Prompt
  -> 07B LLM JSON Caller (Pandas)
  -> 19 Normalize Pandas Plan
  -> 20 Pandas Analysis Executor

14 + 17 + 20
  -> 21 Analysis Result Merger

21 Analysis Result Merger
  -> 22 MongoDB Data Store (optional compact data_ref mode)
  -> 23 Build Final Answer Prompt
  -> 07C LLM JSON Caller (Answer)
  -> 24 Normalize Answer Text

21 Analysis Result Merger OR 22 MongoDB Data Store
  -> 25 Final Answer Builder.analysis_result
24 Normalize Answer Text
  -> 25 Final Answer Builder.answer_text

25 Final Answer Builder
  -> Chat Output
25 Final Answer Builder.next_state
  -> 26 State Memory Message Builder
  -> Message History (Store, native Langflow)
```

## Exact Connection Map

Use this table as the canvas wiring checklist. The format is `Node.Port`.

| Step | From Node.Port | To Node.Port | Required | Note |
| --- | --- | --- | --- | --- |
| 0A | `Message History (Retrieve).messages` | `State Memory Extractor.memory_messages` | Recommended | Native Langflow short-term memory |
| 0B | `State Memory Extractor.previous_state` | `State Loader.previous_state` | Recommended | Previous `chat_history/context/current_data` |
| 1 | `Chat Input.message` | `State Loader.chat_input` | Required | User question plus optional session metadata |
| 2A | `MongoDB Domain Loader.domain_payload` | `Build Intent Prompt.domain_payload` | Choose 1 | MongoDB domain |
| 2B | `Domain JSON Loader.domain_payload` | `Build Intent Prompt.domain_payload` | Choose 1 | Direct JSON domain |
| 3 | `Table Catalog Loader.table_catalog_payload` | `Build Intent Prompt.table_catalog_payload` | Required | Dataset/tool descriptions |
| 4 | `Main Flow Filters Loader.main_flow_filters_payload` | `Build Intent Prompt.main_flow_filters_payload` | Required | Shared semantic filters and aliases |
| 5 | `State Loader.state_payload` | `Build Intent Prompt.state_payload` | Required | Current question and state |
| 6 | `Build Intent Prompt.prompt_payload` | `LLM JSON Caller (Intent).prompt_payload` | Required | Intent LLM call |
| 7 | `LLM JSON Caller (Intent).llm_result` | `Normalize Intent Plan.llm_result` | Required | Intent JSON normalization |
| 8 | `Normalize Intent Plan.intent_plan` | `Intent Route Router.intent_plan` | Required | Visible route branch |
| 8A-1 | `Intent Route Router.single_retrieval` | `Dummy Data Retriever (Single).intent_plan` | Choose 1 | Dummy single retrieval |
| 8A-2 | `Intent Route Router.single_retrieval` | `Oracle Data Retriever (Single).intent_plan` | Choose 1 | Oracle single retrieval |
| 8B-1 | `Intent Route Router.multi_retrieval` | `Dummy Data Retriever (Multi).intent_plan` | Choose 1 | Dummy multi retrieval |
| 8B-2 | `Intent Route Router.multi_retrieval` | `Oracle Data Retriever (Multi).intent_plan` | Choose 1 | Oracle multi retrieval |
| 8C-1 | `Intent Route Router.followup_transform` | `Current Data Retriever.intent_plan` | Basic | Follow-up when state contains actual rows |
| 8C-2 | `Intent Route Router.followup_transform` | `MongoDB Data Loader (Follow-up).payload` | Recommended with refs | Load rows for follow-up |
| 8C-3 | `MongoDB Data Loader (Follow-up).loaded_payload` | `Current Data Retriever.intent_plan` | Recommended with refs | Hydrated follow-up state |
| 8D | `Intent Route Router.finish` | `Early Result Adapter.intent_plan` | Required | Finish/clarification branch |
| 9A-1 | `Dummy Data Retriever (Single).retrieval_payload` | `Retrieval Payload Merger.single_retrieval` | Choose 1 | Merge dummy single result |
| 9A-2 | `Oracle Data Retriever (Single).retrieval_payload` | `Retrieval Payload Merger.single_retrieval` | Choose 1 | Merge Oracle single result |
| 9B-1 | `Dummy Data Retriever (Multi).retrieval_payload` | `Retrieval Payload Merger.multi_retrieval` | Choose 1 | Merge dummy multi result |
| 9B-2 | `Oracle Data Retriever (Multi).retrieval_payload` | `Retrieval Payload Merger.multi_retrieval` | Choose 1 | Merge Oracle multi result |
| 9C | `Current Data Retriever.retrieval_payload` | `Retrieval Payload Merger.followup_retrieval` | Required | Merge follow-up result |
| 10 | `Retrieval Payload Merger.retrieval_payload` | `Retrieval Postprocess Router.retrieval_payload` | Required | Direct/post-analysis branch |
| 11A | `Retrieval Postprocess Router.direct_response` | `Direct Result Adapter.retrieval_payload` | Required | No pandas needed |
| 11B | `Retrieval Postprocess Router.post_analysis` | `Build Pandas Prompt.retrieval_payload` | Required | Pandas needed |
| 12A | `MongoDB Domain Loader.domain_payload` | `Build Pandas Prompt.domain_payload` | Choose 1 | Domain hints for pandas |
| 12B | `Domain JSON Loader.domain_payload` | `Build Pandas Prompt.domain_payload` | Choose 1 | Domain hints for pandas |
| 13 | `Build Pandas Prompt.prompt_payload` | `LLM JSON Caller (Pandas).prompt_payload` | Required | Pandas LLM call |
| 14 | `LLM JSON Caller (Pandas).llm_result` | `Normalize Pandas Plan.llm_result` | Required | Pandas JSON normalization |
| 15 | `Normalize Pandas Plan.analysis_plan_payload` | `Pandas Analysis Executor.analysis_plan_payload` | Required | Pandas execution |
| 16A | `Early Result Adapter.analysis_result` | `Analysis Result Merger.early_result` | Required | Merge early branch |
| 16B | `Direct Result Adapter.analysis_result` | `Analysis Result Merger.direct_result` | Required | Merge direct branch |
| 16C | `Pandas Analysis Executor.analysis_result` | `Analysis Result Merger.pandas_result` | Required | Merge pandas branch |
| 17A | `Analysis Result Merger.analysis_result` | `Build Final Answer Prompt.analysis_result` | Basic | No MongoDB data ref mode |
| 17B | `Analysis Result Merger.analysis_result` | `MongoDB Data Store.payload` | Recommended with refs | Store full rows and emit preview+ref |
| 17C | `MongoDB Data Store.stored_payload` | `Build Final Answer Prompt.analysis_result` | Recommended with refs | Final prompt uses preview and counts |
| 18 | `Build Final Answer Prompt.prompt_payload` | `LLM JSON Caller (Answer).prompt_payload` | Required | Final answer LLM call |
| 19 | `LLM JSON Caller (Answer).llm_result` | `Normalize Answer Text.llm_result` | Required | Final answer JSON normalization |
| 20A | `Analysis Result Merger.analysis_result` | `Final Answer Builder.analysis_result` | Basic | No MongoDB data ref mode |
| 20B | `MongoDB Data Store.stored_payload` | `Final Answer Builder.analysis_result` | Recommended with refs | Compact next-state payload |
| 20C | `Normalize Answer Text.answer_text` | `Final Answer Builder.answer_text` | Required | LLM-created natural-language answer |
| 21A | `Final Answer Builder.answer_message` | `Chat Output.input` | Required | User-facing answer plus final data preview |
| 21B | `Final Answer Builder.final_result` | `API/Storage Node.input` | Optional | Full payload |
| 22A | `Final Answer Builder.next_state` | `State Memory Message Builder.next_state` | Recommended | Build native memory state message |
| 22B | `State Memory Message Builder.memory_message` | `Message History (Store).message` | Recommended | Persist state in Langflow storage |
| 22C | `Final Answer Builder.next_state` | `State Loader.previous_state` | Optional/dev only | Manual feedback instead of Message History |

## LLM Call Points

The flow has three LLM call points:

1. Intent planning: `06 -> 07A -> 08`
2. Pandas analysis planning: `18 -> 07B -> 19`
3. Final answer writing: `23 -> 07C -> 24`

If an LLM API key is empty, the normalize node after that call uses fallback
logic so the flow remains testable locally.

## Branch Behavior

### Intent Route Branch

`Intent Route Router` exposes `intent_plan.route` as visible outputs:

- `single_retrieval`: one dataset/job retrieval
- `multi_retrieval`: multiple dataset/job retrieval
- `followup_transform`: reuse previous `current_data`
- `finish`: finish early or ask for missing conditions

Unselected outputs emit `{skipped: true}`. Downstream nodes detect this and skip
actual retrieval or analysis.

### Retrieval Postprocess Branch

`Retrieval Postprocess Router` splits retrieved data into:

- `direct_response`: return retrieved rows without pandas
- `post_analysis`: run pandas aggregation/calculation

The usual `post_analysis` triggers are:

- `intent_plan.needs_pandas == true`
- `query_mode == followup_transform`
- more than one source result

## Node Detail

| File | Input name | Output name | Payload key |
| --- | --- | --- | --- |
| `00_state_memory_extractor.py` | `memory_messages`, `memory_marker` | `previous_state` | extracts `{state, state_json}` from Langflow Message History |
| `01_state_loader.py` | `chat_input`, `user_question`, `previous_state`, `session_id` | `state_payload` | `{user_question, state}` |
| `02_mongodb_domain_loader.py` | `mongo_uri`, `db_name`, `collection_name`, `domain_status`, `limit` | `domain_payload` | `{domain_payload: {domain, domain_source, domain_errors}}` |
| `03_domain_json_loader.py` | `domain_json` | `domain_payload` | `{domain_payload: {domain, domain_source, domain_errors}}` |
| `04_table_catalog_loader.py` | `table_catalog_json` | `table_catalog_payload` | `{table_catalog_payload: {table_catalog, table_catalog_errors}}` |
| `05_main_flow_filters_loader.py` | `main_flow_filters_json` | `main_flow_filters_payload` | `{main_flow_filters_payload: {main_flow_filters, main_flow_filter_errors}}` |
| `06_build_intent_prompt.py` | `state_payload`, `domain_payload`, `table_catalog_payload`, `main_flow_filters_payload`, `reference_date` | `prompt_payload` | `{prompt_payload: {prompt, state, domain, table_catalog, main_flow_filters}}` |
| `07_llm_json_caller.py` | `prompt_payload`, `llm_api_key`, `model_name`, `temperature` | `llm_result` | `{llm_result: {llm_text, errors, prompt_payload}}` |
| `08_normalize_intent_plan.py` | `llm_result`, `reference_date` | `intent_plan` | `{intent_plan, retrieval_jobs, state, domain, table_catalog}` |
| `09_intent_route_router.py` | `intent_plan` | `single_retrieval`, `multi_retrieval`, `followup_transform`, `finish` | selected branch payload |
| `10_dummy_data_retriever.py` | `intent_plan` | `retrieval_payload` | dummy `source_results` |
| `11_oracle_data_retriever.py` | `intent_plan`, `db_config`, `fetch_limit` | `retrieval_payload` | Oracle `source_results` |
| `12_mongodb_data_loader.py` | `payload`, `mongo_uri`, `db_name`, `collection_name`, `enabled` | `loaded_payload` | rehydrates row lists from `data_ref` |
| `13_current_data_retriever.py` | `intent_plan` | `retrieval_payload` | current data as `source_results` |
| `14_early_result_adapter.py` | `intent_plan` | `analysis_result` | finish branch result |
| `15_retrieval_payload_merger.py` | `single_retrieval`, `multi_retrieval`, `followup_retrieval` | `retrieval_payload` | active retrieval branch |
| `16_retrieval_postprocess_router.py` | `retrieval_payload` | `direct_response`, `post_analysis` | selected postprocess branch |
| `17_direct_result_adapter.py` | `retrieval_payload` | `analysis_result` | direct branch result |
| `18_build_pandas_prompt.py` | `retrieval_payload`, `domain_payload` | `prompt_payload` | pandas prompt payload |
| `19_normalize_pandas_plan.py` | `llm_result` | `analysis_plan_payload` | pandas code plan |
| `20_pandas_analysis_executor.py` | `analysis_plan_payload`, optional `retrieval_payload` | `analysis_result` | pandas branch result |
| `21_analysis_result_merger.py` | `early_result`, `direct_result`, `pandas_result` | `analysis_result` | active analysis branch |
| `22_mongodb_data_store.py` | `payload`, `mongo_uri`, `db_name`, `collection_name`, controls | `stored_payload` | replaces row lists with preview rows plus `data_ref` |
| `23_build_final_answer_prompt.py` | `analysis_result`, `preview_row_limit` | `prompt_payload` | final answer prompt payload |
| `24_normalize_answer_text.py` | `llm_result` | `answer_text` | `{answer_text: {response, answer_source}}` |
| `25_final_answer_builder.py` | `analysis_result`, `answer_text`, row limits | `answer_message`, `final_result`, `next_state` | final contract, final data table, and next-state payload |
| `26_state_memory_message_builder.py` | `next_state`, `memory_marker` | `memory_message`, `memory_payload` | stores next state as a marked Message History message |

## Minimal Inputs

Local dummy test:

- `State Loader.chat_input`
- `Domain JSON Loader.domain_json`
- `Table Catalog Loader.table_catalog_json`
- `Main Flow Filters Loader.main_flow_filters_json`
- `LLM JSON Caller.*.llm_api_key`: can be empty for fallback behavior
- `LLM JSON Caller.*.model_name`: required when `llm_api_key` is set; use the model id for the configured LangChain chat model adapter

Real Oracle retrieval:

- `Oracle Data Retriever (Single).db_config`
- `Oracle Data Retriever (Multi).db_config`
- optional `fetch_limit` values

## Registration Web

The v2 folder includes a Streamlit registry app for creating domain items and
table-catalog metadata in the format expected by this flow:

```powershell
streamlit run C:\Users\qkekt\Desktop\langflow_local_manufacturing_project\langflow_v2\registration_web\app.py
```

Use it to:

- create `gbn/key/payload` domain item documents for MongoDB
- paste aggregate domain JSON and convert it to item documents
- create table catalog dataset metadata without storing SQL text
- export JSON for `Domain JSON Loader` and `Table Catalog Loader`

See `registration_web/README.md` for details.

## Table Catalog Input

The table catalog is dataset/tool metadata. Do not put SQL here. SQL belongs in
the individual retrieval functions inside `11_oracle_data_retriever.py`.

Use `filter_mappings` to map standard keys from `main_flow_filters` to the real
columns in each dataset. This is what lets one table use `process`, another use
`process_name`, and another use `process_nm` while the intent plan still says
`process_name`.

Example file: `examples/table_catalog_example.json`

Recommended shape:

```json
{
  "datasets": {
    "production": {
      "display_name": "Production",
      "description": "Daily production quantity by date, process, line, and product.",
      "keywords": ["production", "output", "actual", "?ㅼ쟻", "?앹궛"],
      "question_examples": ["?ㅻ뒛 D/A3 ?앹궛 蹂댁뿬以?],
      "tool_name": "get_production_data",
      "db_key": "PKG_RPT",
      "required_params": ["date"],
      "param_format": {"date": "YYYYMMDD"},
      "grain": ["WORK_DT", "OPER_NAME", "MODE"],
      "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "MODE"}, {"name": "production"}],
      "filter_mappings": {
        "process_name": ["OPER_NAME"],
        "mode": ["MODE"]
      }
    }
  }
}
```

Column metadata is optional for pandas because `Build Pandas Prompt` inspects
actual columns after retrieval, but it is recommended because direct
`column_filters` can only be validated against known table/current-data columns.

## Main Flow Filters Input

`Main Flow Filters Loader` defines common semantic filter keys once:
`process_name`, `mode`, `line`, `product_name`, `equipment_id`, `den`, `tech`,
and `mcp_no`. Keep this input small: it should describe filter meanings and
alternate key names, not every possible value.

Do not put operational value expansion rules here by default. For example,
`WB공정 -> ["W/B1", "W/B2"]` belongs in `domain.process_groups`, not in
`main_flow_filters.value_aliases`.

Example file: `examples/main_flow_filters_example.json`

If a condition is not defined here but the column exists in the table catalog or
current data, the planner can still use `column_filters` with the real column
name, for example `{"PKG_TYPE1": ["PKG_A"]}`.

Optional advanced fields such as `known_values` or `value_aliases` are still
accepted for special cases, but the recommended operating model is:

- `main_flow_filters`: standard meaning keys and aliases
- `table_catalog.filter_mappings`: standard key to real table columns
- `domain.process_groups`: process group aliases and expansion values

Follow-up behavior:

- `required_params` such as `date` and `lot_id` are retrieval boundaries. If
  they change, the next turn becomes a new retrieval.
- Filters are inherited across follow-up questions unless the user overrides
  them.
- If a new filter is outside the scope of `current_data`, the next turn becomes
  a new retrieval.

## Domain Input

Domain information is used only by:

- `Build Intent Prompt`
- `Build Pandas Prompt`

Retrieval nodes do not need domain metadata.

MongoDB and direct JSON input both support aggregate documents and item
documents.

Aggregate document:

```json
{
  "domain_id": "manufacturing_default",
  "status": "active",
  "metadata": {"version": "v2"},
  "domain": {
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  }
}
```

Item document:

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "Achievement Rate",
    "aliases": ["달성률", "달성율", "목표 대비", "achievement", "achievement rate"],
    "required_datasets": ["production", "target"],
    "formula": "sum(production) / sum(target) * 100",
    "output_column": "achievement_rate",
    "source_columns": ["production", "target"],
    "grouping_hint": ["MODE", "OPER_NAME"]
  }
}
```

For a question such as `어제 wb공정 생산달성율을 mode별로 알려줘`,
`Normalize Intent Plan` expands the retrieval plan to both `production` and
`target` from the metric's `required_datasets`, then the pandas step calculates
`achievement_rate`.

Example files:

- `examples/domain_payload_example.json`
- `examples/mongodb_domain_items_example.json`
- `examples/mongodb_domain_document_example.json`

## Oracle DB Config Input

`Oracle Data Retriever.db_config` accepts strict JSON and JSON-ish text with
triple-quoted DSN/TNS strings.

Strict JSON:

```json
{
  "PKG_RPT": {
    "user": "PKG_USER",
    "password": "PKG_PASSWORD",
    "dsn": "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=svc)))"
  }
}
```

Triple quote form:

```python
{
  "PKG_RPT": {
    "user": "PKG_USER",
    "password": "PKG_PASSWORD",
    "dsn": """(DESCRIPTION=
      (ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))
      (CONNECT_DATA=(SERVICE_NAME=svc))
    )"""
  }
}
```

The parser tries strict JSON, safe `ast.literal_eval`, then triple-quote
normalization. It never executes the input string.

## Final Contract

`Final Answer Builder.final_result` preserves:

- `response`
- `answer_message`
- `final_data`
- `tool_results`
- `current_data`
- `extracted_params`
- `awaiting_analysis_choice`
- `state_json`

`response` is the clean natural-language answer. `answer_message` is the
Playground-facing message and includes `response` plus a markdown table built
from the final processed data. `final_data.rows` displays all rows currently
held in the final analysis payload, with row count, columns, preview metadata,
and optional `data_ref`.

`Final Answer Builder.display_row_limit` is kept only for backward
compatibility. The answer message now displays the full final-data row list by
default.

`current_data` can contain either actual preview rows or:

```json
{
  "data": [{"preview": "rows"}],
  "data_ref": {
    "store": "mongodb",
    "ref_id": "...",
    "row_count": 1234,
    "columns": ["WORK_DT", "MODE", "production"]
  },
  "data_is_reference": true
}
```

The `data_ref` mode keeps the next-state payload small. Use
`MongoDB Data Loader` before follow-up analysis to restore the full rows.

## Langflow Native Memory

For Playground follow-up analysis, prefer Langflow's native Message History:

1. Add `Message History (Retrieve)` at the beginning of the flow.
2. Connect `Message History (Retrieve).messages` to `State Memory Extractor.memory_messages`.
3. Connect `State Memory Extractor.previous_state` to `State Loader.previous_state`.
4. Connect `Final Answer Builder.next_state` to `State Memory Message Builder.next_state`.
5. Connect `State Memory Message Builder.memory_message` to `Message History (Store).message`.
6. Use the same Playground chat session for follow-up questions.

If the Message History component shows a singular output label in your Langflow
version, use its only Message output port for step 2. The state message is a
marked JSON message, so `State Memory Extractor` ignores normal user and
assistant chat messages.

## MongoDB Data Reference Mode

This mode is possible and implemented as optional nodes. It is useful when the
retrieved or analyzed data is too large to keep inside `current_data` and
`state_json`.

Recommended wiring:

1. Connect `Analysis Result Merger.analysis_result` to `MongoDB Data Store.payload`.
2. Connect `MongoDB Data Store.stored_payload` to `Build Final Answer Prompt.analysis_result`.
3. Connect `MongoDB Data Store.stored_payload` to `Final Answer Builder.analysis_result`.
4. For follow-up branches, connect `Intent Route Router.followup_transform` to `MongoDB Data Loader (Follow-up).payload`.
5. Connect `MongoDB Data Loader (Follow-up).loaded_payload` to `Current Data Retriever.intent_plan`.

The final answer LLM still receives only preview rows and summary/count
metadata. The full rows are loaded again only when a later follow-up branch
actually needs pandas/current-data analysis.

Example stored row document:

- `examples/mongodb_data_ref_document_example.json`

## Playground Follow-up Analysis

For the Playground:

- Connect `Chat Input.message` to `State Loader.chat_input`.
- Use the same Playground chat session for follow-up questions.

`State Loader` still reads a manual `session_id` if you set one, but Message
History can use the current Langflow session automatically when its `session_id`
input is empty.

