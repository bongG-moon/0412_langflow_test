import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW_DIR = ROOT / "langflow" / "data_answer_flow"


def load_flow_module(filename: str, module_name: str):
    path = FLOW_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


main_context_mod = load_flow_module("05_main_flow_context_builder.py", "flow_05_main_context")
intent_prompt_mod = load_flow_module("06_build_intent_prompt.py", "flow_06_intent_prompt")
table_catalog_mod = load_flow_module("04_table_catalog_loader.py", "flow_04_table_catalog")
retrieval_plan_mod = load_flow_module("12_retrieval_plan_builder.py", "flow_12_retrieval_plan")
oracle_mod = load_flow_module("14_oracledb_data_retriever.py", "flow_14_oracle")
pandas_prompt_mod = load_flow_module("16_build_pandas_analysis_prompt.py", "flow_16_pandas_prompt")
pandas_exec_mod = load_flow_module("18_execute_pandas_analysis.py", "flow_18_pandas_exec")


class LangflowContextSourceAndPandasTests(unittest.TestCase):
    def test_main_context_does_not_carry_table_catalog(self):
        payload = main_context_mod.build_main_context(
            "show production",
            {"agent_state": {"turn_id": 1}},
            {"domain": {"datasets": {"production": {"display_name": "Production"}}}},
            table_catalog_payload_value={
                "table_catalog": {
                    "datasets": {
                        "production": {
                            "sql_template": "SELECT * FROM PROD_TABLE",
                            "columns": [{"name": "production"}],
                        }
                    }
                }
            },
        )

        self.assertNotIn("table_catalog", payload["main_context"])
        self.assertNotIn("table_catalog_prompt_context", payload["main_context"])
        self.assertIn("domain_prompt_context", payload["main_context"])

    def test_intent_prompt_omits_table_catalog_summary(self):
        main_context = main_context_mod.build_main_context(
            "show production",
            {"agent_state": {}},
            {"domain": {"datasets": {"production": {"display_name": "Production"}}}},
        )

        prompt = intent_prompt_mod.build_intent_prompt("", None, None, main_context_payload=main_context)

        self.assertNotIn("Available table catalog summary", prompt)
        self.assertNotIn("sql_template", prompt)

    def test_table_catalog_loader_drops_sql_fields_but_keeps_columns(self):
        raw_catalog = {
            "catalog_id": "test",
            "datasets": {
                "production": {
                    "display_name": "Production",
                    "tool_name": "get_production_data",
                    "source_type": "oracle",
                    "db_key": "MES",
                    "sql_template": "SELECT hacked FROM nowhere",
                    "oracle": {"sql": "SELECT nested FROM nowhere", "db_key": "MES"},
                    "format_params": ["date"],
                    "columns": [{"name": "WORK_DT", "type": "date"}, {"name": "production", "type": "number"}],
                }
            },
        }

        loaded = table_catalog_mod.load_table_catalog({"table_catalog_json": json.dumps(raw_catalog)})
        dataset = loaded["table_catalog"]["datasets"]["production"]

        self.assertNotIn("sql_template", dataset)
        self.assertNotIn("sql", dataset["oracle"])
        self.assertEqual(dataset["format_params"], ["date"])
        self.assertEqual([column["name"] for column in dataset["columns"]], ["WORK_DT", "production"])

    def test_table_catalog_ports_are_visible_for_direct_connections(self):
        loader_inputs = {item.name: item for item in table_catalog_mod.TableCatalogLoader.inputs}
        planner_inputs = {item.name: item for item in retrieval_plan_mod.RetrievalPlanBuilder.inputs}
        oracle_inputs = {item.name: item for item in oracle_mod.OracleDBDataRetriever.inputs}

        self.assertIn("table_catalog_json_payload", loader_inputs)
        self.assertIn("table_catalog_payload", planner_inputs)
        self.assertIn("table_catalog_payload", oracle_inputs)
        self.assertFalse(getattr(planner_inputs["table_catalog_payload"], "advanced", False))
        self.assertFalse(getattr(oracle_inputs["table_catalog_payload"], "advanced", False))

    def test_table_catalog_example_matches_metadata_only_contract(self):
        example_path = FLOW_DIR / "examples" / "phase1_table_catalog_input_example.txt"
        raw_text = example_path.read_text(encoding="utf-8")
        raw_catalog = json.loads(raw_text)

        serialized = json.dumps(raw_catalog, ensure_ascii=False)
        self.assertNotIn("sql_template", serialized)
        self.assertNotIn("bind_params", serialized)
        self.assertNotIn(":date", serialized)
        self.assertIn("format_params", serialized)
        self.assertIn("external_quality_note", raw_catalog["datasets"])

        loaded = table_catalog_mod.load_table_catalog({"table_catalog_json": raw_text})
        self.assertEqual(loaded["table_catalog_errors"], [])
        self.assertIn("production", loaded["table_catalog"]["datasets"])
        self.assertEqual(loaded["table_catalog"]["datasets"]["production"]["format_params"], ["date"])

    def test_oracle_tool_function_owns_sql_and_ignores_catalog_sql(self):
        class FakeDBConnector:
            def __init__(self):
                self.calls = []

            def execute_query(self, target_db, sql, fetch_limit=5000):
                self.calls.append(
                    {
                        "target_db": target_db,
                        "sql": sql,
                        "fetch_limit": fetch_limit,
                    }
                )
                return [{"WORK_DT": "2026-04-22", "production": 10}]

        connector = FakeDBConnector()
        result = oracle_mod.get_production_data(
            connector,
            {},
            {"datasets": {"production": {"sql_template": "SELECT hacked FROM nowhere", "format_params": ["date"]}}},
            {"date": "2026-04-22"},
            100,
        )

        self.assertTrue(result["success"])
        self.assertIn("PROD_TABLE", connector.calls[0]["sql"])
        self.assertNotIn("hacked", connector.calls[0]["sql"])
        self.assertNotIn(":date", connector.calls[0]["sql"])
        self.assertNotIn("{0}", connector.calls[0]["sql"])
        self.assertIn("WORK_DT = '20260422'", connector.calls[0]["sql"])
        self.assertEqual(result["format_params"], {"date": "20260422"})
        self.assertEqual(result["required_params"], ["date"])

    def test_oracle_tool_returns_missing_required_params_without_query(self):
        class FakeDBConnector:
            def __init__(self):
                self.calls = []

            def execute_query(self, target_db, sql, fetch_limit=5000):
                self.calls.append({"target_db": target_db, "sql": sql, "fetch_limit": fetch_limit})
                return []

        connector = FakeDBConnector()
        result = oracle_mod.get_production_data(connector, {}, {}, {}, 100)

        self.assertFalse(result["success"])
        self.assertEqual(result["failure_type"], "missing_required_params")
        self.assertEqual(result["required_params"], ["date"])
        self.assertEqual(result["missing_params"], ["date"])
        self.assertEqual(connector.calls, [])

    def test_oracle_sql_format_allows_with_query(self):
        class FakeDBConnector:
            def __init__(self):
                self.calls = []

            def execute_query(self, target_db, sql, fetch_limit=5000):
                self.calls.append({"target_db": target_db, "sql": sql, "fetch_limit": fetch_limit})
                return [{"WORK_DT": "2026-04-22"}]

        connector = FakeDBConnector()
        sql = """
            WITH base AS (
                SELECT {0} AS WORK_DT FROM DUAL
            )
            SELECT WORK_DT FROM base
        """

        result = oracle_mod._execute_sql_dataset(
            "get_with_data",
            "with_dataset",
            "MES",
            sql,
            connector,
            {"date": "2026-04-22"},
            50,
            ["date"],
        )

        self.assertTrue(result["success"])
        self.assertTrue(connector.calls[0]["sql"].lstrip().upper().startswith("WITH"))
        self.assertIn("'2026-04-22'", connector.calls[0]["sql"])
        self.assertEqual(connector.calls[0]["fetch_limit"], 50)

    def test_pandas_prompt_filters_domain_columns_to_actual_dataframe_columns(self):
        analysis_context = {
            "analysis_context": {
                "analysis_table": {
                    "data": [{"MODE": "DDR5", "production": 10}],
                    "columns": ["MODE", "production"],
                },
                "retrieval_plan": {"dataset_keys": ["production"]},
                "intent": {"dataset_hints": ["production"], "metric_hints": ["production_qty"]},
            }
        }
        domain = {
            "domain": {
                "datasets": {
                    "production": {
                        "display_name": "Production",
                        "columns": [{"name": "MODE"}, {"name": "production"}, {"name": "not_in_df"}],
                    }
                },
                "metrics": {"production_qty": {"required_datasets": ["production"], "formula": "sum(production)"}},
            }
        }

        prompt = pandas_prompt_mod.build_pandas_analysis_prompt(analysis_context, domain)

        self.assertIn('"MODE"', prompt)
        self.assertIn('"production"', prompt)
        self.assertNotIn("not_in_df", prompt)

    def test_missing_pandas_column_uses_safe_fallback(self):
        analysis_context = {
            "analysis_context": {
                "analysis_table": {
                    "data": [{"MODE": "DDR5", "production": 10}, {"MODE": "LPDDR5", "production": 5}],
                    "columns": ["MODE", "production"],
                },
                "source_results": [{"dataset_key": "production"}],
                "retrieval_plan": {"jobs": [{"params": {"date": "2026-04-22"}}]},
                "intent": {"group_by": ["MODE"]},
            }
        }
        analysis_plan = {
            "analysis_plan": {
                "code": "result = df.groupby('not_in_df', as_index=False)['production'].sum()",
                "warnings": [],
            }
        }

        result = pandas_exec_mod.execute_pandas_analysis(analysis_context, analysis_plan)["analysis_result"]

        self.assertTrue(result["success"])
        self.assertEqual(result["analysis_logic"], "fallback_after_error")
        self.assertIn("not_in_df", " ".join(result["analysis_plan"]["warnings"]))
        self.assertEqual({row["MODE"] for row in result["data"]}, {"DDR5", "LPDDR5"})

    def test_pandas_code_can_create_derived_columns_from_existing_columns(self):
        analysis_context = {
            "analysis_context": {
                "analysis_table": {
                    "data": [{"production": 80, "target": 100}],
                    "columns": ["production", "target"],
                },
                "source_results": [{"dataset_key": "production"}, {"dataset_key": "target"}],
                "retrieval_plan": {"jobs": [{"params": {"date": "2026-04-22"}}]},
                "intent": {},
            }
        }
        analysis_plan = {
            "analysis_plan": {
                "code": "result = df.copy()\nresult['achievement_rate'] = result['production'] / result['target']",
                "warnings": [],
            }
        }

        result = pandas_exec_mod.execute_pandas_analysis(analysis_context, analysis_plan)["analysis_result"]

        self.assertTrue(result["success"])
        self.assertEqual(result["analysis_logic"], "llm_primary")
        self.assertEqual(result["data"][0]["achievement_rate"], 0.8)


if __name__ == "__main__":
    unittest.main()
