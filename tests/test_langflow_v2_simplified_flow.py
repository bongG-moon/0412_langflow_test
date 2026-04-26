import importlib
from pathlib import Path
import sys
import types
import unittest


def _install_lfx_stubs() -> None:
    if "lfx.custom.custom_component.component" in sys.modules:
        return

    class StubComponent:
        status = None

    class StubData:
        def __init__(self, data=None):
            self.data = data or {}

    class StubMessage:
        def __init__(self, text=None, content=None):
            self.text = text if text is not None else content
            self.content = self.text

    class StubInput:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    module_names = [
        "lfx",
        "lfx.custom",
        "lfx.custom.custom_component",
        "lfx.custom.custom_component.component",
        "lfx.io",
        "lfx.schema",
        "lfx.schema.data",
        "lfx.schema.message",
    ]
    for name in module_names:
        sys.modules.setdefault(name, types.ModuleType(name))

    sys.modules["lfx.custom.custom_component.component"].Component = StubComponent
    for name in ("DataInput", "MessageTextInput", "MultilineInput", "Output"):
        setattr(sys.modules["lfx.io"], name, StubInput)
    sys.modules["lfx.schema.data"].Data = StubData
    sys.modules["lfx.schema.message"].Message = StubMessage


try:
    importlib.import_module("lfx.custom.custom_component.component")
except ModuleNotFoundError:
    _install_lfx_stubs()


state_mod = importlib.import_module("langflow_v2.01_state_loader")
mongo_domain_mod = importlib.import_module("langflow_v2.02_mongodb_domain_loader")
domain_json_mod = importlib.import_module("langflow_v2.03_domain_json_loader")
table_loader_mod = importlib.import_module("langflow_v2.04_table_catalog_loader")
main_filters_mod = importlib.import_module("langflow_v2.05_main_flow_filters_loader")
intent_prompt_mod = importlib.import_module("langflow_v2.06_build_intent_prompt")
llm_mod = importlib.import_module("langflow_v2.07_llm_json_caller")
intent_normalize_mod = importlib.import_module("langflow_v2.08_normalize_intent_plan")
intent_router_mod = importlib.import_module("langflow_v2.09_intent_route_router")
dummy_mod = importlib.import_module("langflow_v2.10_dummy_data_retriever")
oracle_mod = importlib.import_module("langflow_v2.11_oracle_data_retriever")
current_mod = importlib.import_module("langflow_v2.13_current_data_retriever")
retrieval_merger_mod = importlib.import_module("langflow_v2.15_retrieval_payload_merger")
early_mod = importlib.import_module("langflow_v2.14_early_result_adapter")
post_router_mod = importlib.import_module("langflow_v2.16_retrieval_postprocess_router")
direct_mod = importlib.import_module("langflow_v2.17_direct_result_adapter")
pandas_prompt_mod = importlib.import_module("langflow_v2.18_build_pandas_prompt")
pandas_normalize_mod = importlib.import_module("langflow_v2.19_normalize_pandas_plan")
pandas_executor_mod = importlib.import_module("langflow_v2.20_pandas_analysis_executor")
merger_mod = importlib.import_module("langflow_v2.21_analysis_result_merger")
answer_prompt_mod = importlib.import_module("langflow_v2.23_build_final_answer_prompt")
answer_normalize_mod = importlib.import_module("langflow_v2.24_normalize_answer_text")
final_mod = importlib.import_module("langflow_v2.25_final_answer_builder")
memory_extract_mod = importlib.import_module("langflow_v2.00_state_memory_extractor")
memory_builder_mod = importlib.import_module("langflow_v2.26_state_memory_message_builder")
mongo_store_mod = importlib.import_module("langflow_v2.22_mongodb_data_store")
mongo_loader_mod = importlib.import_module("langflow_v2.12_mongodb_data_loader")


TABLE_CATALOG = {
    "datasets": {
        "production": {
            "display_name": "Production",
            "description": "Daily production output.",
            "keywords": ["production", "output", "production data"],
            "tool_name": "get_production_data",
            "db_key": "PKG_RPT",
            "required_params": ["date"],
            "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "MODE"}, {"name": "LINE"}, {"name": "DEN"}, {"name": "TECH"}, {"name": "MCP_NO"}, {"name": "PKG_TYPE1"}, {"name": "production"}],
            "filter_mappings": {"process_name": ["OPER_NAME"], "mode": ["MODE"], "line": ["LINE"], "den": ["DEN"], "tech": ["TECH"], "mcp_no": ["MCP_NO"], "product_name": ["MCP_NO", "MODE", "DEN", "TECH"]},
        },
        "target": {
            "display_name": "Target",
            "description": "Daily production target.",
            "keywords": ["target", "plan"],
            "tool_name": "get_target_data",
            "db_key": "PKG_RPT",
            "required_params": ["date"],
            "columns": [{"name": "WORK_DT"}, {"name": "OPER_NAME"}, {"name": "MODE"}, {"name": "LINE"}, {"name": "DEN"}, {"name": "TECH"}, {"name": "MCP_NO"}, {"name": "PKG_TYPE1"}, {"name": "target"}],
            "filter_mappings": {"process_name": ["OPER_NAME"], "mode": ["MODE"], "line": ["LINE"], "den": ["DEN"], "tech": ["TECH"], "mcp_no": ["MCP_NO"], "product_name": ["MCP_NO", "MODE", "DEN", "TECH"]},
        },
    }
}

MAIN_FLOW_FILTERS = {
    "required_params": {
        "date": {
            "value_type": "date",
            "value_shape": "scalar",
            "normalized_format": "YYYYMMDD",
            "aliases": ["date", "work_date", "WORK_DT", "일자", "날짜"],
        }
    },
    "filters": {
        "process_name": {
            "aliases": ["process", "process_name", "oper", "공정"],
        },
        "mode": {"aliases": ["mode", "모드"]},
        "line": {"aliases": ["line", "라인"]},
        "product_name": {"aliases": ["product", "제품"]},
        "equipment_id": {"aliases": ["equipment", "설비"]},
        "den": {"aliases": ["den", "density"]},
        "tech": {"aliases": ["tech"]},
        "mcp_no": {"aliases": ["mcp", "mcp_no"]},
    }
}

DOMAIN_PAYLOAD = {
    "domain": {
        "products": {
            "DDR5": {
                "display_name": "DDR5",
                "aliases": ["DDR5"],
                "filters": {"mode": ["DDR5"]},
            },
            "LPDDR5": {
                "display_name": "LPDDR5",
                "aliases": ["LPDDR5"],
                "filters": {"mode": ["LPDDR5"]},
            },
            "HBM3": {
                "display_name": "HBM3",
                "aliases": ["HBM3", "HBM"],
                "filters": {"mode": ["HBM3"]},
            },
        },
        "process_groups": {
            "DA": {
                "display_name": "Die Attach",
                "aliases": ["DA", "D/A", "DA공정", "D/A공정", "DA process"],
                "processes": ["D/A1", "D/A2", "D/A3"],
            },
            "WB": {
                "display_name": "Wire Bond",
                "aliases": ["WB", "W/B", "WB공정", "W/B공정"],
                "processes": ["W/B1", "W/B2"],
            }
        },
        "terms": {},
        "datasets": {
            "production": {
                "display_name": "Production",
                "aliases": ["생산", "실적", "생산량", "output", "production"],
                "keywords": ["생산", "실적", "production"],
                "primary_quantity_column": "production",
            },
            "target": {
                "display_name": "Target",
                "aliases": ["목표", "계획", "목표량", "target", "plan"],
                "keywords": ["목표", "계획", "target"],
                "primary_quantity_column": "target",
            },
        },
        "metrics": {
            "achievement_rate": {
                "display_name": "Achievement Rate",
                "aliases": ["달성률", "목표 대비", "achievement", "achievement rate"],
                "required_datasets": ["production", "target"],
                "formula": "sum(production) / sum(target) * 100",
                "output_column": "achievement_rate",
                "source_columns": ["production", "target"],
                "grouping_hint": ["MODE", "OPER_NAME"],
            }
        },
        "join_rules": [],
    }
}


def run_visible_branch_flow(question, previous_state=None, session_id="session-a"):
    state = state_mod.load_state(question, previous_state, session_id)
    domain_payload = domain_json_mod._normalize_domain_payload(DOMAIN_PAYLOAD)
    table_payload = table_loader_mod.load_table_catalog(TABLE_CATALOG)
    main_filters_payload = main_filters_mod.load_main_flow_filters(MAIN_FLOW_FILTERS)

    intent_prompt = intent_prompt_mod.build_intent_prompt(state, domain_payload, table_payload, main_filters_payload, "2026-04-24")
    intent_llm = llm_mod.call_llm_json(intent_prompt)
    planned = intent_normalize_mod.normalize_intent_plan(intent_llm)

    single_branch = intent_router_mod.route_intent(planned, "single_retrieval")
    multi_branch = intent_router_mod.route_intent(planned, "multi_retrieval")
    followup_branch = intent_router_mod.route_intent(planned, "followup_transform")
    finish_branch = intent_router_mod.route_intent(planned, "finish")

    single_retrieval = dummy_mod.retrieve_dummy_data(single_branch)
    multi_retrieval = dummy_mod.retrieve_dummy_data(multi_branch)
    followup_retrieval = current_mod.retrieve_current_data(followup_branch)
    early_result = early_mod.build_early_analysis_result(finish_branch)
    active_retrieval = retrieval_merger_mod.merge_retrieval_payloads(single_retrieval, multi_retrieval, followup_retrieval)

    direct_branch = post_router_mod.route_retrieval_postprocess(active_retrieval, "direct_response")
    post_analysis_branch = post_router_mod.route_retrieval_postprocess(active_retrieval, "post_analysis")
    direct_result = direct_mod.adapt_direct_result(direct_branch)

    pandas_prompt = pandas_prompt_mod.build_pandas_prompt(post_analysis_branch, domain_payload)
    pandas_llm = llm_mod.call_llm_json(pandas_prompt)
    analysis_plan = pandas_normalize_mod.normalize_pandas_plan(pandas_llm)
    pandas_result = pandas_executor_mod.execute_pandas_analysis(analysis_plan)
    merged = merger_mod.merge_analysis_results(early_result, direct_result, pandas_result)
    answer_prompt = answer_prompt_mod.build_final_answer_prompt(merged)
    answer_llm = llm_mod.call_llm_json(answer_prompt)
    answer_text = answer_normalize_mod.normalize_answer_text(answer_llm)

    return {
        "state": state,
        "domain_payload": domain_payload,
        "table_payload": table_payload,
        "planned": planned,
        "single_branch": single_branch,
        "multi_branch": multi_branch,
        "followup_branch": followup_branch,
        "finish_branch": finish_branch,
        "single_retrieval": single_retrieval,
        "multi_retrieval": multi_retrieval,
        "followup_retrieval": followup_retrieval,
        "active_retrieval": active_retrieval,
        "direct_branch": direct_branch,
        "post_analysis_branch": post_analysis_branch,
        "direct_result": direct_result,
        "analysis_plan": analysis_plan,
        "pandas_result": pandas_result,
        "merged": merged,
        "answer_prompt": answer_prompt,
        "answer_text": answer_text,
    }


class LangflowV2SimplifiedFlowTests(unittest.TestCase):
    def test_main_flow_filters_include_date_required_param_metadata(self):
        payload = main_filters_mod.load_main_flow_filters(MAIN_FLOW_FILTERS)["main_flow_filters_payload"]["main_flow_filters"]
        date_param = payload["required_params"]["date"]

        self.assertEqual(date_param["value_type"], "date")
        self.assertEqual(date_param["value_shape"], "scalar")
        self.assertEqual(date_param["normalized_format"], "YYYYMMDD")

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
            {"gbn": "metrics", "key": "achievement_rate", "payload": {"aliases": ["achievement"], "required_datasets": ["production", "target"]}},
        )

        self.assertEqual(domain["metrics"]["achievement_rate"]["required_datasets"], ["production", "target"])

    def test_domain_json_loader_accepts_item_document_shape(self):
        item_doc = {
            "gbn": "metrics",
            "key": "achievement_rate",
            "status": "active",
            "payload": {
                "aliases": ["달성률"],
                "required_datasets": ["production", "target"],
                "formula": "sum(production) / sum(target) * 100",
                "output_column": "achievement_rate",
            },
        }

        payload = domain_json_mod._normalize_domain_payload(item_doc)
        metric = payload["domain_payload"]["domain"]["metrics"]["achievement_rate"]

        self.assertEqual(metric["required_datasets"], ["production", "target"])

    def test_intent_router_exposes_multi_dataset_branch(self):
        result = run_visible_branch_flow("20260422 D/A3 DDR5 production target achievement")
        plan = result["planned"]["intent_plan"]

        self.assertEqual(plan["route"], "multi_retrieval")
        self.assertTrue(result["single_branch"]["skipped"])
        self.assertFalse(result["multi_branch"].get("skipped", False))
        self.assertEqual(result["multi_retrieval"]["retrieval_payload"]["route"], "multi_retrieval")
        self.assertEqual(len(result["multi_retrieval"]["retrieval_payload"]["source_results"]), 2)

    def test_direct_response_branch_handles_single_lookup_without_pandas(self):
        result = run_visible_branch_flow("20260422 production")
        plan = result["planned"]["intent_plan"]
        merged = result["merged"]["analysis_result"]

        self.assertEqual(plan["route"], "single_retrieval")
        self.assertEqual(result["direct_branch"]["retrieval_payload"]["selected_postprocess_route"], "direct_response")
        self.assertTrue(result["post_analysis_branch"]["retrieval_payload"]["skipped"])
        self.assertEqual(merged["merged_from"], "direct_result")
        self.assertTrue(merged["success"])

    def test_followup_branch_reuses_current_data_and_pandas_groups(self):
        first = run_visible_branch_flow("20260422 D/A3 DDR5 production")
        first_final = final_mod.build_final_answer(first["merged"], first["answer_text"], "200", "5")

        followup = run_visible_branch_flow("that result by mode", {"state": first_final["next_state"]}, "session-a")
        analyzed = followup["merged"]["analysis_result"]

        self.assertEqual(followup["planned"]["intent_plan"]["query_mode"], "followup_transform")
        self.assertFalse(followup["followup_branch"].get("skipped", False))
        self.assertEqual(followup["followup_retrieval"]["retrieval_payload"]["route"], "followup_transform")
        self.assertEqual(analyzed["merged_from"], "pandas_result")
        self.assertTrue(analyzed["success"])
        self.assertIn("MODE", analyzed["data"][0])

    def test_korean_direct_answer_summarizes_data_instead_of_dumping_columns(self):
        result = run_visible_branch_flow("오늘 da공정 생산량 알려줘")
        final_payload = final_mod.build_final_answer(result["merged"], result["answer_text"], "200", "5")
        final_result = final_payload["final_result"]
        response = final_result["response"]

        self.assertIn("생산량", response)
        self.assertNotIn("Columns:", response)
        self.assertNotIn("Result rows:", response)
        self.assertIn("final_data", final_result)
        self.assertEqual(len(final_result["final_data"]["rows"]), final_result["final_data"]["row_count"])
        self.assertEqual(final_result["final_data"]["display_row_limit"], "all")
        self.assertIn("### 최종 데이터", final_payload["answer_message"])
        self.assertIn("총 12건", final_payload["answer_message"])
        self.assertIn("| WORK_DT |", final_payload["answer_message"])
        self.assertIn("\n\n| WORK_DT |", final_payload["answer_message"])
        self.assertNotIn("화면에는", final_payload["answer_message"])

    def test_final_builder_fallback_summarizes_data_when_answer_text_is_missing(self):
        result = run_visible_branch_flow("오늘 da공정 생산량 알려줘")
        final_result = final_mod.build_final_answer(result["merged"], "", "200", "5")["final_result"]
        response = final_result["response"]

        self.assertIn("생산량", response)
        self.assertNotIn("Columns:", response)
        self.assertNotIn("Result rows:", response)

    def test_korean_followup_this_time_routes_to_current_data_analysis(self):
        first = run_visible_branch_flow("오늘 da공정 생산량 알려줘")
        first_final = final_mod.build_final_answer(first["merged"], first["answer_text"], "200", "5")

        followup = run_visible_branch_flow("이때 가장 생산량이 많았던 mode를 알려줘", {"state": first_final["next_state"]}, "session-a")
        plan = followup["planned"]["intent_plan"]
        analyzed = followup["merged"]["analysis_result"]
        final_result = final_mod.build_final_answer(followup["merged"], followup["answer_text"], "200", "5")["final_result"]

        self.assertEqual(plan["query_mode"], "followup_transform")
        self.assertEqual(plan["route"], "followup_transform")
        self.assertEqual(plan["group_by"], ["MODE"])
        self.assertEqual(plan["top_n"], 1)
        self.assertEqual(analyzed["merged_from"], "pandas_result")
        self.assertTrue(analyzed["success"])
        self.assertEqual(len(analyzed["data"]), 1)
        self.assertIn("MODE", analyzed["data"][0])
        self.assertIn("가장", final_result["response"])
        self.assertEqual(len(final_result["final_data"]["rows"]), 1)
        self.assertEqual(final_result["final_data"]["columns"], ["MODE", "production"])

    def test_intent_prompt_teaches_followup_metric_words_do_not_force_retrieval(self):
        state = {
            "state": {
                "pending_user_question": "이때 가장 생산량이 많았던 mode를 알려줘",
                "current_data": {"data": [{"MODE": "DDR5", "production": 100}]},
            }
        }
        domain_payload = domain_json_mod._normalize_domain_payload(DOMAIN_PAYLOAD)
        table_payload = table_loader_mod.load_table_catalog(TABLE_CATALOG)

        prompt = intent_prompt_mod.build_intent_prompt(state, domain_payload, table_payload, "2026-04-24")["prompt_payload"]["prompt"]

        self.assertIn("이때 가장 생산량이 많았던 mode를 알려줘", prompt)
        self.assertIn('"query_mode": "followup_transform"', prompt)
        self.assertIn('"needed_datasets": []', prompt)
        self.assertIn("dataset/metric words", prompt)

    def test_normalizer_respects_llm_retrieval_even_when_followup_words_exist(self):
        prompt_payload = {
            "state": {
                "pending_user_question": "이때 생산량을 새로 조회해줘",
                "current_data": {"data": [{"MODE": "DDR5", "production": 100}]},
            },
            "domain": DOMAIN_PAYLOAD["domain"],
            "table_catalog": TABLE_CATALOG,
            "user_question": "이때 생산량을 새로 조회해줘",
            "reference_date": "2026-04-24",
        }
        llm_result = {
            "llm_result": {
                "prompt_payload": prompt_payload,
                "llm_text": """{
                  "request_type": "data_question",
                  "query_mode": "retrieval",
                  "needed_datasets": ["production"],
                  "required_params": {"date": "20260424"},
                  "filters": {},
                  "group_by": [],
                  "sort": null,
                  "top_n": null,
                  "needs_pandas": false,
                  "analysis_goal": "Retrieve production again.",
                  "reason": "The user asked for a fresh retrieval."
                }""",
            }
        }

        plan = intent_normalize_mod.normalize_intent_plan(llm_result)["intent_plan"]

        self.assertEqual(plan["planner_source"], "llm")
        self.assertEqual(plan["query_mode"], "retrieval")
        self.assertEqual(plan["route"], "single_retrieval")

    def test_fresh_retrieval_term_guards_against_llm_followup_misclassification(self):
        main_filters = main_filters_mod.load_main_flow_filters(MAIN_FLOW_FILTERS)["main_flow_filters_payload"]["main_flow_filters"]
        prompt_payload = {
            "state": {
                "pending_user_question": "20260422 이때 생산량을 새로 조회해줘",
                "current_data": {
                    "data": [{"MODE": "DDR5", "production": 100}],
                    "source_dataset_keys": ["production"],
                },
            },
            "domain": DOMAIN_PAYLOAD["domain"],
            "table_catalog": TABLE_CATALOG,
            "main_flow_filters": main_filters,
            "user_question": "20260422 이때 생산량을 새로 조회해줘",
            "reference_date": "2026-04-24",
        }
        llm_result = {
            "llm_result": {
                "prompt_payload": prompt_payload,
                "llm_text": """{
                  "request_type": "data_question",
                  "query_mode": "followup_transform",
                  "needed_datasets": [],
                  "filters": {},
                  "group_by": [],
                  "needs_pandas": true
                }""",
            }
        }

        plan = intent_normalize_mod.normalize_intent_plan(llm_result)["intent_plan"]

        self.assertEqual(plan["planner_source"], "llm")
        self.assertEqual(plan["query_mode"], "retrieval")
        self.assertEqual(plan["query_mode_source"], "guard:fresh_retrieval")
        self.assertEqual(plan["needed_datasets"], ["production"])

    def test_relative_date_keyword_overrides_llm_hallucinated_date(self):
        prompt_payload = {
            "state": {"pending_user_question": "오늘 생산 보여줘"},
            "domain": DOMAIN_PAYLOAD["domain"],
            "table_catalog": TABLE_CATALOG,
            "main_flow_filters": MAIN_FLOW_FILTERS,
            "user_question": "오늘 생산 보여줘",
            "reference_date": "2026-04-26",
        }
        llm_result = {
            "llm_result": {
                "prompt_payload": prompt_payload,
                "llm_text": """{
                  "request_type": "data_question",
                  "query_mode": "retrieval",
                  "needed_datasets": ["production"],
                  "required_params": {"date": "20250522"},
                  "filters": {},
                  "needs_pandas": false
                }""",
            }
        }

        plan = intent_normalize_mod.normalize_intent_plan(llm_result)["intent_plan"]

        self.assertEqual(plan["required_params"]["date"], "20260426")

    def test_metric_domain_expands_single_dataset_llm_plan_to_multi_retrieval(self):
        state = state_mod.load_state("어제 wb공정 생산달성율을 mode별로 알려줘", None, "metric-session")
        domain_payload = domain_json_mod._normalize_domain_payload(DOMAIN_PAYLOAD)
        table_payload = table_loader_mod.load_table_catalog(TABLE_CATALOG)
        main_filters_payload = main_filters_mod.load_main_flow_filters(MAIN_FLOW_FILTERS)
        prompt_payload = intent_prompt_mod.build_intent_prompt(state, domain_payload, table_payload, main_filters_payload, "2026-04-25")["prompt_payload"]
        llm_result = {
            "llm_result": {
                "prompt_payload": prompt_payload,
                "llm_text": """{
                  "request_type": "data_question",
                  "query_mode": "retrieval",
                  "needed_datasets": ["production"],
                  "required_params": {"date": ""},
                  "filters": {},
                  "group_by": ["MODE"],
                  "needs_pandas": false,
                  "analysis_goal": "Production achievement rate by mode."
                }""",
            }
        }

        plan = intent_normalize_mod.normalize_intent_plan(llm_result)["intent_plan"]

        self.assertEqual(plan["planner_source"], "llm")
        self.assertEqual(plan["route"], "multi_retrieval")
        self.assertEqual(plan["needed_datasets"], ["production", "target"])
        self.assertEqual(plan["required_params"]["date"], "20260424")
        self.assertEqual(plan["filters"]["process_name"], ["W/B1", "W/B2"])
        self.assertEqual(plan["group_by"], ["MODE"])
        self.assertTrue(plan["needs_pandas"])
        self.assertEqual(plan["metric_keys"], ["achievement_rate"])

    def test_semantic_filter_plan_maps_standard_keys_to_dataset_columns(self):
        result = run_visible_branch_flow("20260422 WB공정 DDR5 production")
        plan = result["planned"]["intent_plan"]

        self.assertEqual(plan["filters"]["process_name"], ["W/B1", "W/B2"])
        self.assertEqual(plan["filters"]["mode"], ["DDR5"])
        self.assertTrue(any(item["field"] == "process_name" and item["columns"] == ["OPER_NAME"] for item in plan["filter_plan"]))
        self.assertTrue(any(item["field"] == "mode" and item["columns"] == ["MODE"] for item in plan["filter_plan"]))
        process_plan = next(item for item in plan["filter_plan"] if item["field"] == "process_name")
        self.assertEqual(process_plan["operator"], "in")
        self.assertEqual(process_plan["value_type"], "string")
        self.assertEqual(process_plan["value_shape"], "list")

    def test_group_by_uses_catalog_filter_mapping_not_hardcoded_columns(self):
        custom_catalog = {
            "datasets": {
                "production": {
                    "display_name": "Production",
                    "required_params": ["date"],
                    "columns": [{"name": "WORK_DAY"}, {"name": "PROCESS_NM"}, {"name": "MODEL_CODE"}, {"name": "QTY"}],
                    "filter_mappings": {"process_name": ["PROCESS_NM"], "mode": ["MODEL_CODE"]},
                }
            }
        }
        custom_filters = {
            "planner_terms": {
                "rank_desc": ["가장", "많"],
                "rank_asc": ["최소"],
                "sort": ["정렬", "순위"],
                "top_n": ["top", "상위", "하위"],
                "grouping_suffixes": ["별", "별로"],
                "grouping_prefixes": ["by", "group by"],
                "grouping_postfixes": ["wise"],
            },
            "required_params": {"date": {"aliases": ["date", "WORK_DAY"], "column_candidates": ["WORK_DAY"]}},
            "filters": {
                "process_name": {"aliases": ["process", "공정"]},
                "mode": {"aliases": ["mode", "모드"]},
            },
        }
        custom_domain = {
            "datasets": {
                "production": {
                    "aliases": ["생산", "생산량", "production"],
                    "primary_quantity_column": "QTY",
                }
            }
        }
        prompt_payload = {
            "state": {"pending_user_question": "20260422 생산량이 가장 많은 모드 알려줘"},
            "domain": custom_domain,
            "table_catalog": custom_catalog,
            "main_flow_filters": custom_filters,
            "user_question": "20260422 생산량이 가장 많은 모드 알려줘",
            "reference_date": "2026-04-24",
        }
        llm_result = {"llm_result": {"prompt_payload": prompt_payload, "llm_text": ""}}

        plan = intent_normalize_mod.normalize_intent_plan(llm_result)["intent_plan"]

        self.assertEqual(plan["group_by"], ["MODEL_CODE"])
        self.assertEqual(plan["sort"], {"column": "QTY", "ascending": False})
        self.assertNotIn("MODE", plan["group_by"])

    def test_required_param_change_forces_retrieval_on_followup_like_question(self):
        first = run_visible_branch_flow("오늘 DA공정 DDR5 생산 보여줘")
        first_final = final_mod.build_final_answer(first["merged"], first["answer_text"], "200", "5")

        second = run_visible_branch_flow("어제 WB공정은?", {"state": first_final["next_state"]}, "session-a")
        plan = second["planned"]["intent_plan"]

        self.assertEqual(plan["query_mode"], "retrieval")
        self.assertEqual(plan["required_params"]["date"], "20260423")
        self.assertEqual(plan["filters"]["process_name"], ["W/B1", "W/B2"])
        self.assertTrue(plan["required_param_changed"])

    def test_filter_outside_current_scope_forces_retrieval(self):
        first = run_visible_branch_flow("20260422 D/A3 DDR5 production")
        first_final = final_mod.build_final_answer(first["merged"], first["answer_text"], "200", "5")

        second = run_visible_branch_flow("그중 WB공정은?", {"state": first_final["next_state"]}, "session-a")
        plan = second["planned"]["intent_plan"]

        self.assertEqual(plan["query_mode"], "retrieval")
        self.assertEqual(plan["filters"]["process_name"], ["W/B1", "W/B2"])

    def test_direct_column_filter_survives_without_main_flow_definition(self):
        prompt_payload = {
            "state": {"pending_user_question": "20260422 production PKG_TYPE1 PKG_A만 보여줘"},
            "domain": DOMAIN_PAYLOAD["domain"],
            "table_catalog": TABLE_CATALOG,
            "main_flow_filters": MAIN_FLOW_FILTERS,
            "user_question": "20260422 production PKG_TYPE1 PKG_A만 보여줘",
            "reference_date": "2026-04-24",
        }
        llm_result = {
            "llm_result": {
                "prompt_payload": prompt_payload,
                "llm_text": """{
                  "request_type": "data_question",
                  "query_mode": "retrieval",
                  "needed_datasets": ["production"],
                  "required_params": {"date": "20260422"},
                  "filters": {},
                  "column_filters": {"PKG_TYPE1": ["PKG_A"]},
                  "needs_pandas": false
                }""",
            }
        }

        plan = intent_normalize_mod.normalize_intent_plan(llm_result)["intent_plan"]

        self.assertEqual(plan["column_filters"], {"PKG_TYPE1": ["PKG_A"]})
        self.assertTrue(any(item["kind"] == "column" and item["columns"] == ["PKG_TYPE1"] for item in plan["filter_plan"]))

    def test_korean_achievement_rate_query_runs_multi_retrieval_and_calculation(self):
        result = run_visible_branch_flow("어제 wb공정 생산달성율을 mode별로 알려줘")
        plan = result["planned"]["intent_plan"]
        analyzed = result["merged"]["analysis_result"]
        final_result = final_mod.build_final_answer(result["merged"], result["answer_text"], "200", "5")["final_result"]

        self.assertEqual(plan["route"], "multi_retrieval")
        self.assertEqual(plan["needed_datasets"], ["production", "target"])
        self.assertEqual(plan["required_params"]["date"], "20260423")
        self.assertEqual(plan["group_by"], ["MODE"])
        self.assertEqual(analyzed["merged_from"], "pandas_result")
        self.assertTrue(analyzed["success"])
        self.assertIn("achievement_rate", analyzed["data"][0])
        self.assertIn("achievement_rate", final_result["final_data"]["columns"])

    def test_final_payload_preserves_contract_after_merge(self):
        result = run_visible_branch_flow("20260422 production")
        final_result = final_mod.build_final_answer(result["merged"], result["answer_text"], "200", "5")["final_result"]

        for key in ("response", "answer_message", "final_data", "tool_results", "current_data", "extracted_params", "awaiting_analysis_choice"):
            self.assertIn(key, final_result)
        self.assertIsInstance(final_result["state_json"], str)

    def test_first_turn_post_processing_uses_post_analysis_branch(self):
        result = run_visible_branch_flow("20260422 production by mode")
        plan = result["planned"]["intent_plan"]
        analyzed = result["merged"]["analysis_result"]

        self.assertEqual(plan["route"], "single_retrieval")
        self.assertTrue(plan["needs_pandas"])
        self.assertEqual(result["post_analysis_branch"]["retrieval_payload"]["selected_postprocess_route"], "post_analysis")
        self.assertEqual(analyzed["merged_from"], "pandas_result")
        self.assertTrue(analyzed["success"])
        self.assertIn("MODE", analyzed["data"][0])

    def test_oracle_retriever_reports_empty_db_config_without_parsing_error(self):
        result = run_visible_branch_flow("20260422 production")
        single_branch = intent_router_mod.route_intent(result["planned"], "single_retrieval")
        retrieved = oracle_mod.retrieve_oracle_data(single_branch, "{}", "100")["retrieval_payload"]

        self.assertEqual(len(retrieved["source_results"]), 1)
        self.assertFalse(retrieved["source_results"][0]["success"])
        self.assertEqual(retrieved["source_results"][0]["failure_type"], "missing_db_config")

    def test_split_flow_calculates_achievement_rate(self):
        result = run_visible_branch_flow("20260422 D/A3 DDR5 production target achievement by mode")
        analyzed = result["merged"]["analysis_result"]
        final_result = final_mod.build_final_answer(result["merged"], result["answer_text"], "200", "5")["final_result"]

        self.assertEqual(result["planned"]["intent_plan"]["route"], "multi_retrieval")
        self.assertEqual(analyzed["merged_from"], "pandas_result")
        self.assertTrue(analyzed["success"])
        self.assertIn("achievement_rate", analyzed["data"][0])
        self.assertIn("response", final_result)
        self.assertIn("current_data", final_result)
        self.assertEqual(result["answer_text"]["answer_text"]["answer_source"], "fallback")

    def test_pandas_fallback_uses_domain_metric_formula_not_hardcoded_names(self):
        domain = {
            "metrics": {
                "good_rate": {
                    "formula": "sum(pass_qty) / sum(input_qty) * 100",
                    "output_column": "good_rate",
                    "source_columns": ["pass_qty", "input_qty"],
                }
            },
            "datasets": {
                "custom_quality": {
                    "primary_quantity_column": "pass_qty",
                }
            },
        }
        rows = [
            {"MODEL": "A", "pass_qty": 80, "input_qty": 100},
            {"MODEL": "A", "pass_qty": 15, "input_qty": 20},
            {"MODEL": "B", "pass_qty": 30, "input_qty": 60},
        ]
        plan = {
            "needs_pandas": True,
            "needed_datasets": ["custom_quality"],
            "group_by": ["MODEL"],
            "metric_keys": ["good_rate"],
            "metric_definitions": domain["metrics"],
        }
        llm_result = {
            "llm_result": {
                "prompt_payload": {
                    "retrieval_payload": {"intent_plan": plan},
                    "table": {"success": True, "data": rows, "columns": ["MODEL", "pass_qty", "input_qty"]},
                    "intent_plan": plan,
                    "domain": domain,
                    "columns": ["MODEL", "pass_qty", "input_qty"],
                },
                "llm_text": "",
            }
        }

        analysis_plan = pandas_normalize_mod.normalize_pandas_plan(llm_result)
        code = analysis_plan["analysis_plan"]["code"]
        executed = pandas_executor_mod.execute_pandas_analysis(analysis_plan)["analysis_result"]

        self.assertIn("good_rate", code)
        self.assertNotIn("achievement_rate", code)
        self.assertNotIn("production", code)
        self.assertTrue(executed["success"])
        self.assertEqual(executed["data"][0]["MODEL"], "A")
        self.assertAlmostEqual(executed["data"][0]["good_rate"], 95 / 120 * 100)

    def test_pandas_source_merge_uses_domain_join_rules(self):
        domain = {
            "join_rules": [
                {
                    "left_dataset": "actual",
                    "right_dataset": "goal",
                    "keys": ["DAY", "PRODUCT_CODE"],
                }
            ]
        }
        retrieval_payload = {
            "intent_plan": {"needed_datasets": ["actual", "goal"], "needs_pandas": True},
            "source_results": [
                {
                    "dataset_key": "actual",
                    "success": True,
                    "data": [
                        {"DAY": "20260422", "PRODUCT_CODE": "A", "actual_qty": 10},
                        {"DAY": "20260422", "PRODUCT_CODE": "B", "actual_qty": 7},
                    ],
                },
                {
                    "dataset_key": "goal",
                    "success": True,
                    "data": [
                        {"DAY": "20260422", "PRODUCT_CODE": "A", "target_qty": 12},
                        {"DAY": "20260422", "PRODUCT_CODE": "C", "target_qty": 5},
                    ],
                },
            ],
        }

        prompt_payload = pandas_prompt_mod.build_pandas_prompt(retrieval_payload, {"domain": domain})["prompt_payload"]
        executed = pandas_executor_mod.execute_pandas_analysis(
            {
                "analysis_plan_payload": {
                    "analysis_plan": {"code": "result = df.copy()", "source": "llm"},
                    "retrieval_payload": retrieval_payload,
                    "intent_plan": retrieval_payload["intent_plan"],
                    "domain": domain,
                }
            }
        )["analysis_result"]

        self.assertTrue(prompt_payload["table"]["success"])
        self.assertEqual(prompt_payload["row_count"], 1)
        self.assertIn("actual+goal: keys=DAY, PRODUCT_CODE", prompt_payload["table"]["merge_notes"])
        self.assertTrue(executed["success"])
        self.assertEqual(executed["data"], [{"DAY": "20260422", "PRODUCT_CODE": "A", "actual_qty": 10, "target_qty": 12}])

    def test_pandas_executor_requires_filter_plan_for_semantic_filter_columns(self):
        rows = [
            {"PROCESS_NM": "P1", "QTY": 10},
            {"PROCESS_NM": "P2", "QTY": 20},
        ]
        base_payload = {
            "analysis_plan": {"code": "result = df.copy()", "source": "llm"},
            "table": {"success": True, "data": rows, "columns": ["PROCESS_NM", "QTY"]},
        }

        without_plan = pandas_executor_mod.execute_pandas_analysis(
            {"analysis_plan_payload": {**base_payload, "intent_plan": {"filters": {"process_name": ["P1"]}}}}
        )["analysis_result"]
        with_plan = pandas_executor_mod.execute_pandas_analysis(
            {
                "analysis_plan_payload": {
                    **base_payload,
                    "intent_plan": {
                        "filters": {"process_name": ["P1"]},
                        "filter_plan": [{"field": "process_name", "columns": ["PROCESS_NM"], "values": ["P1"]}],
                    },
                }
            }
        )["analysis_result"]

        self.assertTrue(without_plan["success"])
        self.assertEqual(len(without_plan["data"]), 2)
        self.assertTrue(with_plan["success"])
        self.assertEqual(with_plan["data"], [{"PROCESS_NM": "P1", "QTY": 10}])

    def test_finish_branch_can_merge_without_retrieval(self):
        state = state_mod.load_state("unsupported question", None, "session-finish")
        domain_payload = domain_json_mod._normalize_domain_payload(DOMAIN_PAYLOAD)
        table_payload = table_loader_mod.load_table_catalog(TABLE_CATALOG)
        intent_prompt = intent_prompt_mod.build_intent_prompt(state, domain_payload, table_payload, "2026-04-24")
        planned = intent_normalize_mod.normalize_intent_plan(llm_mod.call_llm_json(intent_prompt))
        finish_branch = intent_router_mod.route_intent(planned, "finish")
        early_result = early_mod.build_early_analysis_result(finish_branch)
        merged = merger_mod.merge_analysis_results(early_result)
        answer_prompt = answer_prompt_mod.build_final_answer_prompt(merged)
        answer_text = answer_normalize_mod.normalize_answer_text(llm_mod.call_llm_json(answer_prompt))

        self.assertEqual(planned["intent_plan"]["route"], "finish")
        self.assertFalse(finish_branch.get("skipped", False))
        self.assertEqual(merged["analysis_result"]["merged_from"], "early_result")
        self.assertIn("response", answer_text["answer_text"])

    def test_korean_today_keyword_fills_required_date(self):
        result = run_visible_branch_flow("오늘 생산 보여줘")
        plan = result["planned"]["intent_plan"]

        self.assertEqual(plan["route"], "single_retrieval")
        self.assertEqual(plan["required_params"]["date"], "20260424")
        self.assertNotIn("missing_required_params", plan)

    def test_missing_required_param_message_is_readable_korean(self):
        state = state_mod.load_state("생산 보여줘", None, "missing-date-session")
        domain_payload = domain_json_mod._normalize_domain_payload(DOMAIN_PAYLOAD)
        table_payload = table_loader_mod.load_table_catalog(TABLE_CATALOG)
        intent_prompt = intent_prompt_mod.build_intent_prompt(state, domain_payload, table_payload, "")
        planned = intent_normalize_mod.normalize_intent_plan(llm_mod.call_llm_json(intent_prompt))
        response = planned["intent_plan"]["response"]

        self.assertEqual(planned["intent_plan"]["route"], "finish")
        self.assertIn("데이터 조회에 필요한 필수 조건이 부족합니다", response)
        self.assertIn("production.date", response)

    def test_message_history_state_memory_round_trip_enables_followup(self):
        first = run_visible_branch_flow("20260422 D/A3 DDR5 production", None, "native-memory-session")
        first_final = final_mod.build_final_answer(first["merged"], first["answer_text"], "200", "5")
        memory_message = memory_builder_mod.build_state_memory_message({"state": first_final["next_state"]})
        extracted = memory_extract_mod.extract_previous_state({"messages": [memory_message["memory_text"]]})

        self.assertTrue(extracted["memory_loaded"])
        followup = run_visible_branch_flow("that result by mode", extracted["previous_state"], "native-memory-session")

        self.assertEqual(followup["planned"]["intent_plan"]["query_mode"], "followup_transform")
        self.assertEqual(followup["merged"]["analysis_result"]["merged_from"], "pandas_result")

    def test_mongodb_data_reference_store_and_loader_round_trip(self):
        class FakeCollection:
            docs = {}

            def replace_one(self, query, doc, upsert=False):
                self.docs[query["ref_id"]] = doc

            def find_one(self, query):
                return self.docs.get(query["ref_id"])

        class FakeDatabase:
            def __getitem__(self, name):
                return FakeCollection()

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __getitem__(self, name):
                return FakeDatabase()

            def close(self):
                pass

        original = sys.modules.get("pymongo")
        sys.modules["pymongo"] = types.SimpleNamespace(MongoClient=FakeClient)
        try:
            payload = {
                "analysis_result": {
                    "state": {"session_id": "mongo-session"},
                    "success": True,
                    "data": [{"MODE": "A", "production": 10}, {"MODE": "B", "production": 20}],
                }
            }
            stored = mongo_store_mod.store_payload_in_mongo(payload, "mongodb://fake", "datagov", "manufacturing_agent_data_refs", "true", "1", "1")
            result = stored["analysis_result"]

            self.assertTrue(result["data_is_reference"])
            self.assertEqual(len(result["data"]), 1)
            self.assertEqual(result["data_ref"]["row_count"], 2)

            loaded = mongo_loader_mod.load_payload_from_mongo(stored, "mongodb://fake", "datagov", "manufacturing_agent_data_refs", "true")
            self.assertTrue(loaded["mongo_data_load"]["loaded"])
            self.assertEqual(len(loaded["analysis_result"]["data"]), 2)
        finally:
            if original is None:
                sys.modules.pop("pymongo", None)
            else:
                sys.modules["pymongo"] = original


if __name__ == "__main__":
    unittest.main()

