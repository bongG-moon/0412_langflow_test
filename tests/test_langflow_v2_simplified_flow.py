import importlib
from pathlib import Path
import unittest


state_mod = importlib.import_module("langflow_v2.00_state_loader")
mongo_domain_mod = importlib.import_module("langflow_v2.01_mongodb_domain_loader")
domain_json_mod = importlib.import_module("langflow_v2.02_domain_json_loader")
table_loader_mod = importlib.import_module("langflow_v2.03_table_catalog_loader")
intent_prompt_mod = importlib.import_module("langflow_v2.04_build_intent_prompt")
llm_mod = importlib.import_module("langflow_v2.05_llm_json_caller")
intent_normalize_mod = importlib.import_module("langflow_v2.06_normalize_intent_plan")
dummy_mod = importlib.import_module("langflow_v2.07_dummy_data_retriever")
oracle_mod = importlib.import_module("langflow_v2.08_oracle_data_retriever")
pandas_prompt_mod = importlib.import_module("langflow_v2.09_build_pandas_prompt")
pandas_normalize_mod = importlib.import_module("langflow_v2.10_normalize_pandas_plan")
pandas_executor_mod = importlib.import_module("langflow_v2.11_pandas_analysis_executor")
final_mod = importlib.import_module("langflow_v2.12_final_answer_builder")


TABLE_CATALOG = {
    "datasets": {
        "production": {
            "display_name": "Production",
            "description": "Daily production output.",
            "keywords": ["production", "output", "생산", "실적"],
            "tool_name": "get_production_data",
            "db_key": "PKG_RPT",
            "required_params": ["date"],
        },
        "target": {
            "display_name": "Target",
            "description": "Daily production target.",
            "keywords": ["target", "plan", "목표", "계획"],
            "tool_name": "get_target_data",
            "db_key": "PKG_RPT",
            "required_params": ["date"],
        },
    }
}

DOMAIN_PAYLOAD = {
    "domain": {
        "products": {},
        "process_groups": {
            "DA": {
                "display_name": "Die Attach",
                "aliases": ["DA", "D/A", "DA공정"],
                "processes": ["D/A1", "D/A2", "D/A3"],
            }
        },
        "terms": {},
        "datasets": {},
        "metrics": {
            "achievement_rate": {
                "display_name": "Achievement Rate",
                "aliases": ["achievement", "achievement rate", "달성률", "목표 대비"],
                "required_datasets": ["production", "target"],
                "formula": "sum(production) / sum(target) * 100",
                "output_column": "achievement_rate",
            }
        },
        "join_rules": [],
    }
}


def run_split_flow(question, previous_state=None, session_id="session-a"):
    state = state_mod.load_state(question, previous_state, session_id)
    domain_payload = domain_json_mod._normalize_domain_payload(DOMAIN_PAYLOAD)
    table_payload = table_loader_mod.load_table_catalog(TABLE_CATALOG)

    intent_prompt = intent_prompt_mod.build_intent_prompt(state, domain_payload, table_payload, "2026-04-24")
    intent_llm = llm_mod.call_llm_json(intent_prompt)
    planned = intent_normalize_mod.normalize_intent_plan(intent_llm)
    retrieved = dummy_mod.retrieve_dummy_data(planned)

    pandas_prompt = pandas_prompt_mod.build_pandas_prompt(retrieved, domain_payload)
    pandas_llm = llm_mod.call_llm_json(pandas_prompt)
    analysis_plan = pandas_normalize_mod.normalize_pandas_plan(pandas_llm)
    analyzed = pandas_executor_mod.execute_pandas_analysis(analysis_plan)
    return {
        "state": state,
        "domain_payload": domain_payload,
        "table_payload": table_payload,
        "planned": planned,
        "retrieved": retrieved,
        "analysis_plan": analysis_plan,
        "analyzed": analyzed,
    }


class LangflowV2SimplifiedFlowTests(unittest.TestCase):
    def test_component_files_do_not_import_sibling_modules(self):
        root = Path(__file__).resolve().parents[1] / "langflow_v2"
        for path in root.glob("*.py"):
            if path.name == "__init__.py":
                continue
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from langflow_v2.", source, path.name)
            self.assertNotIn("import langflow_v2.", source, path.name)

    def test_jsonish_parser_accepts_triple_quoted_dsn(self):
        text = '''{
          "PKG_RPT": {
            "user": "u",
            "password": "p",
            "dsn": """(DESCRIPTION=
              (ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))
              (CONNECT_DATA=(SERVICE_NAME=svc))
            )"""
          }
        }'''

        parsed, errors = oracle_mod.parse_jsonish(text)

        self.assertEqual(errors, [])
        self.assertIn("PKG_RPT", parsed)
        self.assertIn("DESCRIPTION", parsed["PKG_RPT"]["dsn"])

    def test_mongodb_domain_loader_can_merge_item_documents(self):
        domain = mongo_domain_mod._empty_domain()
        mongo_domain_mod._merge_item(
            domain,
            {
                "gbn": "metrics",
                "key": "achievement_rate",
                "payload": {
                    "aliases": ["achievement"],
                    "required_datasets": ["production", "target"],
                },
            },
        )

        self.assertEqual(domain["metrics"]["achievement_rate"]["required_datasets"], ["production", "target"])

    def test_split_intent_builds_multi_dataset_jobs(self):
        result = run_split_flow("20260422 D/A3 DDR5 production target achievement")
        plan = result["planned"]["intent_plan"]

        self.assertEqual(plan["query_mode"], "retrieval")
        self.assertEqual(plan["route"], "multi_retrieval")
        self.assertEqual(plan["needed_datasets"], ["production", "target"])
        self.assertEqual(len(plan["retrieval_jobs"]), 2)
        self.assertEqual(plan["required_params"]["date"], "20260422")

    def test_dummy_retriever_runs_every_planned_dataset(self):
        result = run_split_flow("20260422 D/A3 DDR5 production target achievement")
        retrieved = result["retrieved"]["retrieval_payload"]

        self.assertEqual(retrieved["route"], "multi_retrieval")
        self.assertEqual(len(retrieved["source_results"]), 2)
        self.assertEqual(
            [item["dataset_key"] for item in retrieved["source_results"]],
            ["production", "target"],
        )

    def test_followup_reuses_current_data_and_pandas_groups(self):
        first = run_split_flow("20260422 D/A3 DDR5 production")
        first_final = final_mod.build_final_answer(first["analyzed"])

        followup = run_split_flow(
            "that result by mode",
            {"state": first_final["next_state"]},
            "session-a",
        )

        self.assertEqual(followup["planned"]["intent_plan"]["query_mode"], "followup_transform")
        self.assertEqual(followup["retrieved"]["retrieval_payload"]["route"], "followup_transform")
        self.assertTrue(followup["analyzed"]["analysis_result"]["success"])
        self.assertIn("MODE", followup["analyzed"]["analysis_result"]["data"][0])

    def test_final_payload_preserves_contract(self):
        result = run_split_flow("20260422 production")
        final_result = final_mod.build_final_answer(result["analyzed"])["final_result"]

        for key in ("response", "tool_results", "current_data", "extracted_params", "awaiting_analysis_choice"):
            self.assertIn(key, final_result)
        self.assertIsInstance(final_result["state_json"], str)

    def test_first_turn_post_processing_groups_after_retrieval(self):
        result = run_split_flow("20260422 production by mode")
        plan = result["planned"]["intent_plan"]
        analyzed = result["analyzed"]["analysis_result"]

        self.assertEqual(plan["query_mode"], "retrieval")
        self.assertEqual(plan["route"], "single_retrieval")
        self.assertTrue(plan["needs_pandas"])
        self.assertTrue(analyzed["success"])
        self.assertIn("MODE", analyzed["data"][0])

    def test_oracle_retriever_reports_empty_db_config_without_parsing_error(self):
        result = run_split_flow("20260422 production")
        retrieved = oracle_mod.retrieve_oracle_data(result["planned"], "{}", "100")["retrieval_payload"]

        self.assertEqual(len(retrieved["source_results"]), 1)
        self.assertFalse(retrieved["source_results"][0]["success"])
        self.assertEqual(retrieved["source_results"][0]["failure_type"], "missing_db_config")

    def test_split_flow_calculates_achievement_rate(self):
        result = run_split_flow("20260422 D/A3 DDR5 production target achievement by mode")
        analyzed = result["analyzed"]["analysis_result"]
        final_result = final_mod.build_final_answer(result["analyzed"])["final_result"]

        self.assertTrue(analyzed["success"])
        self.assertIn("achievement_rate", analyzed["data"][0])
        self.assertIn("response", final_result)
        self.assertIn("current_data", final_result)


if __name__ == "__main__":
    unittest.main()
