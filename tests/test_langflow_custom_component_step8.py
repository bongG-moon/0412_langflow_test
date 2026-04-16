import json
import shutil
import unittest
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import langflow_custom_component.analyze_multi as analyze_multi_module
import langflow_custom_component.analyze_single as analyze_single_module
import langflow_custom_component.build_multi as build_multi_module
import langflow_custom_component.build_single as build_single_module
import langflow_custom_component.decide_mode as decide_mode_module
import langflow_custom_component.extract_params as extract_params_module
import langflow_custom_component.plan_datasets as plan_datasets_module
import langflow_custom_component.run_followup as run_followup_module
from langflow_custom_component.component_base import read_data_payload, read_state_payload
from langflow_custom_component.domain_registry import DomainRegistryComponent
from langflow_custom_component.domain_rules import DomainRulesComponent
from langflow_custom_component.session_memory import SessionMemoryComponent
from langflow_custom_component.extract_params import ExtractParamsComponent
from langflow_custom_component.decide_mode import DecideModeComponent
from langflow_custom_component.route_mode import RouteModeComponent
from langflow_custom_component.plan_datasets import PlanDatasetsComponent
from langflow_custom_component.build_jobs import BuildJobsComponent
from langflow_custom_component.route_plan import RoutePlanComponent
from langflow_custom_component.exec_jobs import ExecuteJobsComponent
from langflow_custom_component.route_multi import RouteMultiComponent
from langflow_custom_component.analyze_multi import AnalyzeMultiComponent
from langflow_custom_component.run_followup import RunFollowupComponent
from langflow_custom_component.merge_final import MergeFinalComponent


@dataclass
class FakeMessage:
    text: str
    session_id: str = "langflow-test"


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, task: str):
        self.task = task

    def invoke(self, messages):
        prompt = "\n".join(str(getattr(message, "content", message)) for message in messages)
        if self.task == "parameter_extract":
            today = datetime.now().strftime("%Y%m%d")
            if "DDR5제품의 생산 달성율" in prompt:
                payload = {
                    "date": today,
                    "process": ["DA"],
                    "oper_num": None,
                    "pkg_type1": None,
                    "pkg_type2": None,
                    "product_name": "DDR5",
                    "line_name": None,
                    "mode": None,
                    "den": None,
                    "tech": None,
                    "lead": None,
                    "mcp_no": None,
                    "group_by": "OPER_NAME",
                }
            elif "MODE별로 정리" in prompt:
                payload = {
                    "date": None,
                    "process": None,
                    "oper_num": None,
                    "pkg_type1": None,
                    "pkg_type2": None,
                    "product_name": None,
                    "line_name": None,
                    "mode": None,
                    "den": None,
                    "tech": None,
                    "lead": None,
                    "mcp_no": None,
                    "group_by": "MODE",
                }
            else:
                payload = {
                    "date": today,
                    "process": None,
                    "oper_num": None,
                    "pkg_type1": None,
                    "pkg_type2": None,
                    "product_name": None,
                    "line_name": None,
                    "mode": None,
                    "den": None,
                    "tech": None,
                    "lead": None,
                    "mcp_no": None,
                    "group_by": None,
                }
            return FakeResponse(json.dumps(payload, ensure_ascii=False))

        if self.task == "retrieval_plan":
            if "reviewing whether the planned manufacturing datasets miss any base datasets" in prompt:
                return FakeResponse(json.dumps({"missing_dataset_keys": [], "needs_post_processing": False, "reason": "enough"}))
            payload = {
                "dataset_keys": ["production", "target"],
                "needs_post_processing": True,
                "analysis_goal": "achievement rate by detailed process",
                "merge_hints": {
                    "pre_aggregate_before_join": True,
                    "group_dimensions": ["OPER_NAME"],
                    "dataset_metrics": {"production": ["production"], "target": ["target"]},
                    "aggregation": "sum",
                    "reason": "need production and target",
                },
            }
            return FakeResponse(json.dumps(payload, ensure_ascii=False))

        if self.task == "query_mode_review":
            return FakeResponse(json.dumps({"query_mode": "followup_transform", "reason": "current data is enough"}, ensure_ascii=False))

        return FakeResponse("{}")


def fake_get_llm_for_task(task: str, temperature: float = 0.0):
    return FakeLLM(task)


class LangflowCustomComponentTest(unittest.TestCase):
    storage_subdir = ".langflow_test_store"
    flat_runtime_modules = [
        extract_params_module,
        decide_mode_module,
        plan_datasets_module,
        build_single_module,
        analyze_single_module,
        build_multi_module,
        analyze_multi_module,
        run_followup_module,
    ]

    def setUp(self):
        shutil.rmtree(Path.cwd() / self.storage_subdir, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(Path.cwd() / self.storage_subdir, ignore_errors=True)

    def _patch_runtime(self):
        patches = []
        for module in self.flat_runtime_modules:
            for attr_name in [
                "lf_runtime_services_parameter_service_get_llm_for_task",
                "lf_runtime_services_retrieval_planner_get_llm_for_task",
                "lf_runtime_services_request_context_get_llm_for_task",
            ]:
                if hasattr(module, attr_name):
                    patches.append(patch.object(module, attr_name, side_effect=fake_get_llm_for_task))

            if hasattr(module, "lf_runtime_analysis_engine_build_llm_plan"):
                patches.append(patch.object(module, "lf_runtime_analysis_engine_build_llm_plan", return_value=(None, "llm_failed")))

            if hasattr(module, "lf_runtime_services_runtime_service_generate_response"):
                patches.append(
                    patch.object(
                        module,
                        "lf_runtime_services_runtime_service_generate_response",
                        side_effect=lambda user_input, result, chat_history: f"{result.get('summary', '')} | {user_input}",
                    )
                )
        return patches

    def _enter_runtime_patches(self):
        stack = ExitStack()
        for patcher in self._patch_runtime():
            stack.enter_context(patcher)
        return stack

    def test_domain_inputs_are_carried_into_session_state(self):
        rules_node = DomainRulesComponent()
        rules_node.domain_rules_text = "DDR5는 제조팀에서 핵심 제품군으로 취급한다."
        rules_data = rules_node.build_rules()

        registry_node = DomainRegistryComponent()
        registry_node.registry_json = json.dumps({"notes": ["custom note"], "dataset_keywords": [{"dataset_key": "production", "keywords": ["생산실적"]}]}, ensure_ascii=False)
        registry_data = registry_node.build_registry()

        session_node = SessionMemoryComponent()
        session_node.message = FakeMessage(text="테스트 질문", session_id="domain-state")
        session_node.domain_rules = rules_data
        session_node.domain_registry = registry_data
        session_node.storage_subdir = self.storage_subdir

        state_payload = read_state_payload(session_node.session_state())
        self.assertEqual(state_payload["domain_rules_text"], "DDR5는 제조팀에서 핵심 제품군으로 취급한다.")
        self.assertIn("dataset_keywords", state_payload["domain_registry_payload"])

    def test_multi_retrieval_analysis_flow_runs_through_components(self):
        with self._enter_runtime_patches():
            session_node = SessionMemoryComponent()
            session_node.message = FakeMessage(
                text="오늘 DA공정에서 DDR5제품의 생산 달성율을 세부 공정별로 알려줘",
                session_id="flow-test",
            )
            session_node.storage_subdir = self.storage_subdir
            state_data = session_node.session_state()

            extract_node = ExtractParamsComponent()
            extract_node.state = state_data
            extracted_state_data = extract_node.extract_params()
            extracted_state = read_state_payload(extracted_state_data)
            self.assertEqual(extracted_state["raw_extracted_params"]["product_name"], "DDR5")

            decide_node = DecideModeComponent()
            decide_node.state = extracted_state_data
            decided_state_data = decide_node.decide_mode()
            decided_state = read_state_payload(decided_state_data)
            self.assertEqual(decided_state["query_mode"], "retrieval")

            route_mode_node = RouteModeComponent()
            route_mode_node.state = decided_state_data
            retrieval_state_data = route_mode_node.retrieval_state()
            self.assertIsNotNone(retrieval_state_data)

            plan_node = PlanDatasetsComponent()
            plan_node.state = retrieval_state_data
            planned_state_data = plan_node.plan_datasets()
            planned_state = read_state_payload(planned_state_data)
            self.assertEqual(planned_state["retrieval_keys"], ["production", "target"])

            jobs_node = BuildJobsComponent()
            jobs_node.state = planned_state_data
            jobs_state_data = jobs_node.build_jobs()
            jobs_state = read_state_payload(jobs_state_data)
            self.assertEqual(len(jobs_state["retrieval_jobs"]), 2)

            route_plan_node = RoutePlanComponent()
            route_plan_node.state = jobs_state_data
            multi_state_data = route_plan_node.multi_state()
            self.assertIsNotNone(multi_state_data)

            exec_node = ExecuteJobsComponent()
            exec_node.state = multi_state_data
            executed_state_data = exec_node.execute_jobs()
            executed_state = read_state_payload(executed_state_data)
            self.assertEqual(len(executed_state["source_results"]), 2)

            route_multi_node = RouteMultiComponent()
            route_multi_node.state = executed_state_data
            analysis_state_data = route_multi_node.analysis_state()
            self.assertIsNotNone(analysis_state_data)

            analyze_node = AnalyzeMultiComponent()
            analyze_node.state = analysis_state_data
            analyzed_state_data = analyze_node.run_analysis()
            analyzed_state = read_state_payload(analyzed_state_data)
            result = analyzed_state["result"]
            self.assertTrue(result["current_data"]["success"])
            self.assertIn("production", result["current_data"].get("source_dataset_keys", []))
            self.assertIn("target", result["current_data"].get("source_dataset_keys", []))

            merge_node = MergeFinalComponent()
            merge_node.multi_analysis_result = analyzed_state_data
            merged_output = merge_node.merged_result()
            merged_result = read_data_payload(merged_output)
            self.assertTrue(bool(merged_result.get("response")))
            self.assertEqual(getattr(merged_output, "text", None), merged_result.get("response"))

    def test_followup_branch_reuses_saved_session(self):
        with self._enter_runtime_patches():
            session_node = SessionMemoryComponent()
            session_node.message = FakeMessage(
                text="오늘 DA공정에서 DDR5제품의 생산 달성율을 세부 공정별로 알려줘",
                session_id="followup-test",
            )
            session_node.storage_subdir = self.storage_subdir
            state_data = session_node.session_state()

            extract_node = ExtractParamsComponent()
            extract_node.state = state_data
            extract_state_data = extract_node.extract_params()

            decide_node = DecideModeComponent()
            decide_node.state = extract_state_data
            decide_state_data = decide_node.decide_mode()

            plan_node = PlanDatasetsComponent()
            plan_node.state = decide_state_data
            plan_state_data = plan_node.plan_datasets()
            jobs_node = BuildJobsComponent()
            jobs_node.state = plan_state_data
            jobs_state_data = jobs_node.build_jobs()
            exec_node = ExecuteJobsComponent()
            exec_node.state = jobs_state_data
            executed_state_data = exec_node.execute_jobs()
            analyze_node = AnalyzeMultiComponent()
            analyze_node.state = executed_state_data
            analyzed_state_data = analyze_node.run_analysis()

            merge_node = MergeFinalComponent()
            merge_node.multi_analysis_result = analyzed_state_data
            merged_result_data = merge_node.merged_result()

            save_node = SessionMemoryComponent()
            save_node.message = FakeMessage(text="오늘 DA공정에서 DDR5제품의 생산 달성율을 세부 공정별로 알려줘", session_id="followup-test")
            save_node.result = merged_result_data
            save_node.storage_subdir = self.storage_subdir
            save_node.saved_result()

            followup_session = SessionMemoryComponent()
            followup_session.message = FakeMessage(text="그 결과를 MODE별로 정리해줘", session_id="followup-test")
            followup_session.storage_subdir = self.storage_subdir
            followup_state_data = followup_session.session_state()

            followup_extract = ExtractParamsComponent()
            followup_extract.state = followup_state_data
            followup_extract_state_data = followup_extract.extract_params()

            followup_decide = DecideModeComponent()
            followup_decide.state = followup_extract_state_data
            followup_decided_state_data = followup_decide.decide_mode()
            followup_state = read_state_payload(followup_decided_state_data)
            self.assertEqual(followup_state["query_mode"], "followup_transform")

            route_mode_node = RouteModeComponent()
            route_mode_node.state = followup_decided_state_data
            followup_branch_data = route_mode_node.followup_state()
            self.assertIsNotNone(followup_branch_data)

            run_followup_node = RunFollowupComponent()
            run_followup_node.state = followup_branch_data
            followup_result_state_data = run_followup_node.run_followup()
            followup_result_state = read_state_payload(followup_result_state_data)

            merge_final_node = MergeFinalComponent()
            merge_final_node.followup_result = followup_result_state_data
            merged_followup_output = merge_final_node.merged_result()
            merged_followup_result = read_data_payload(merged_followup_output)
            self.assertTrue(bool(merged_followup_result.get("response")))
            self.assertEqual(getattr(merged_followup_output, "text", None), merged_followup_result.get("response"))
            self.assertEqual(
                followup_result_state["result"]["current_data"].get("source_dataset_keys", []),
                ["production", "target"],
            )

    def test_saved_session_output_keeps_response_text_for_chat_output(self):
        result_payload = {
            "response": "오늘 DA 공정 생산량은 1,234입니다.",
            "current_data": {"success": True, "data": [{"OPER_NAME": "DA", "production": 1234}]},
            "extracted_params": {"date": "20260415", "process_name": ["DA"]},
        }

        save_node = SessionMemoryComponent()
        save_node.message = FakeMessage(text="오늘 da공정 생산량 알려줘", session_id="save-text-test")
        save_node.storage_subdir = self.storage_subdir
        save_node.result = {"result": result_payload}

        saved_output = save_node.saved_result()
        saved_payload = read_data_payload(saved_output)

        self.assertEqual(saved_payload.get("response"), result_payload["response"])
        self.assertEqual(getattr(saved_output, "text", None), result_payload["response"])


if __name__ == "__main__":
    unittest.main()
