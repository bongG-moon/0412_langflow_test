# 05 Main Flow Filters Loader

## Role

`Main Flow Filters Loader` loads the shared semantic filter definitions used by
the intent planner.

This node is intentionally separate from `Table Catalog Loader` and domain
rules:

- `main_flow_filters` defines common meaning keys such as `process_name`,
  `mode`, `line`, `product_name`, `equipment_id`, `den`, `tech`, and `mcp_no`.
- `table_catalog.filter_mappings` maps those meaning keys to the real columns
  in each dataset.
- `domain.process_groups` defines process group aliases and expansion values,
  such as `DA공정 -> D/A1, D/A2, D/A3`.

For example, the intent plan can keep using `process_name` while each table maps
it to its own column:

```json
{
  "production": {"filter_mappings": {"process_name": ["OPER_NAME"]}},
  "some_other_table": {"filter_mappings": {"process_name": ["process_nm"]}}
}
```

## Input

- `main_flow_filters_json`: JSON or JSON-like text.

Recommended shape:

```json
{
  "filters": {
    "process_name": {
      "aliases": ["process", "process_name", "process_nm", "oper", "operation"]
    },
    "mode": {
      "aliases": ["mode", "product mode"]
    }
  }
}
```

Keep this input small. It should define the standard meaning keys and their
alternate names, not every possible value.

Process group expansion belongs in `domain.process_groups`:

```json
{
  "process_groups": {
    "DA": {
      "aliases": ["DA", "D/A", "DA공정"],
      "processes": ["D/A1", "D/A2", "D/A3"]
    },
    "WB": {
      "aliases": ["WB", "W/B", "WB공정"],
      "processes": ["W/B1", "W/B2"]
    }
  }
}
```

Optional advanced fields such as `known_values` or `value_aliases` are accepted
for special cases, but they are not the recommended default because they make
the main-flow filter JSON harder to maintain.

## Output

- `main_flow_filters_payload`

Payload shape:

```json
{
  "main_flow_filters_payload": {
    "main_flow_filters": {
      "filters": {}
    },
    "main_flow_filter_errors": []
  }
}
```

## How It Is Used

`Build Intent Prompt` gives these definitions to the LLM.

`Normalize Intent Plan` uses them to:

- understand standard semantic filter keys from the question and LLM output,
- inherit previous filters in follow-up turns,
- build `filter_plan` entries by combining semantic keys with
  `table_catalog.filter_mappings`,
- still allow `column_filters` for actual table columns that are not defined in
  `main_flow_filters`.

If `date` or another required parameter changes in a later turn, the normalizer
routes to retrieval instead of treating the question as a current-data follow-up.
