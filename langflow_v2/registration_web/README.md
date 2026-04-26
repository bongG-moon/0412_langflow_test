# Langflow v2 Registration Web

Streamlit app for registering Langflow v2 manufacturing domain knowledge and
table catalog metadata into MongoDB.

The main workflow is natural-language first:

1. Paste or type a domain/table explanation.
2. The LLM converts it into v2 MongoDB item documents.
3. Review or edit the generated JSON.
4. Validate and save to MongoDB.

## Run

```powershell
streamlit run C:\Users\qkekt\Desktop\langflow_local_manufacturing_project\langflow_v2\registration_web\app.py
```

## Settings

The sidebar reads defaults from `.env` through `services/config.py`.

```text
MONGO_URI
MONGO_DB_NAME
MONGO_DOMAIN_ITEMS_COLLECTION
MONGO_TABLE_CATALOG_ITEMS_COLLECTION
LLM_API_KEY
LLM_MODEL_NAME
LLM_TEMPERATURE
```

The UI also lets you enter the key and model name at runtime. `LLM_MODEL_NAME`
is provider-specific and should match the LangChain chat model adapter used by
`services/llm_client.py`.

## Pages

- `도메인 자동 등록`: natural language domain text to v2 domain item documents.
- `테이블 자동 등록`: natural language table/catalog text to v2 table catalog items.
- `JSON 가져오기`: direct JSON import for advanced/manual recovery cases.
- `조회/내보내기`: browse MongoDB items and export Langflow loader JSON.

## Domain Item Format

Domain information is saved as item documents:

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "생산달성율",
    "aliases": ["생산달성율", "생산달성률", "달성율", "달성률"],
    "required_datasets": ["production", "wip"],
    "formula": "sum(production) / sum(wip_qty) * 100",
    "output_column": "achievement_rate",
    "source_columns": ["production", "wip_qty"],
    "grouping_hint": ["MODE"]
  }
}
```

This format is compatible with the v2 domain loader, intent prompt builder,
intent normalizer, and pandas prompt builder components.

## Table Catalog Item Format

Table catalog information is saved as dataset metadata:

```json
{
  "dataset_key": "production",
  "status": "active",
  "display_name": "Production",
  "source_type": "oracle",
  "db_key": "PKG_RPT",
  "tool_name": "get_production_data",
  "required_params": ["date"],
  "format_params": ["date"],
  "keywords": ["생산", "production"],
  "columns": [
    {"name": "WORK_DT", "type": "date", "description": "work date"},
    {"name": "production", "type": "number", "description": "production quantity"}
  ]
}
```

SQL text, Oracle TNS strings, accounts, and passwords are intentionally not
stored in table catalog items. Those details stay inside the retriever
component or backend data function.
