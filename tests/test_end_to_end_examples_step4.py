import json
import unittest
from unittest.mock import patch

from manufacturing_agent.agent import run_agent_with_progress


TODAY = "20260415"
DA_PROCESS = ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"]
WB_PROCESS = ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"]


def _build_param_payload(user_question: str):
    mapping = {
        "오늘 DA 공정에서 DDR5 생산량이랑 재공 알려줘": {
            "date": TODAY,
            "process": DA_PROCESS,
            "product_name": "DDR5",
            "group_by": None,
        },
        "오늘 WB공정에서 생산량 알려줘": {
            "date": TODAY,
            "process": WB_PROCESS,
            "product_name": None,
            "group_by": None,
        },
        "오늘 DA공정 생산량 알려줘": {
            "date": TODAY,
            "process": DA_PROCESS,
            "product_name": None,
            "group_by": None,
        },
        "그 결과를 MODE별로 정리해줘": {
            "date": None,
            "process": None,
            "product_name": None,
            "group_by": "MODE",
        },
        "오늘 생산과 목표를 같이 보여줘": {
            "date": TODAY,
            "process": None,
            "product_name": None,
            "group_by": None,
        },
        "오늘 DA공정에서 MODE별 생산량 알려줘": {
            "date": TODAY,
            "process": DA_PROCESS,
            "product_name": None,
            "group_by": "MODE",
        },
    }
    payload = mapping.get(user_question)
    if payload is None:
        raise AssertionError(f"Unexpected parameter question: {user_question}")
    return {
        "date": payload["date"],
        "process": payload["process"],
        "oper_num": None,
        "pkg_type1": None,
        "pkg_type2": None,
        "product_name": payload["product_name"],
        "line_name": None,
        "mode": None,
        "den": None,
        "tech": None,
        "lead": None,
        "mcp_no": None,
        "group_by": payload["group_by"],
    }


def _build_plan_payload(user_question: str):
    mapping = {
        "오늘 DA 공정에서 DDR5 생산량이랑 재공 알려줘": {
            "dataset_keys": ["production", "wip"],
            "needs_post_processing": False,
            "analysis_goal": "show production and wip",
            "merge_hints": {},
        },
        "오늘 WB공정에서 생산량 알려줘": {
            "dataset_keys": ["production"],
            "needs_post_processing": False,
            "analysis_goal": "show production",
            "merge_hints": {},
        },
        "오늘 DA공정 생산량 알려줘": {
            "dataset_keys": ["production"],
            "needs_post_processing": False,
            "analysis_goal": "show production",
            "merge_hints": {},
        },
        "오늘 생산과 목표를 같이 보여줘": {
            "dataset_keys": ["production", "target"],
            "needs_post_processing": False,
            "analysis_goal": "show production and target",
            "merge_hints": {},
        },
        "오늘 DA공정에서 MODE별 생산량 알려줘": {
            "dataset_keys": ["production"],
            "needs_post_processing": True,
            "analysis_goal": "group production by mode",
            "merge_hints": {
                "pre_aggregate_before_join": False,
                "group_dimensions": ["MODE"],
                "dataset_metrics": {"production": ["production"]},
                "aggregation": "sum",
                "reason": "group single dataset after retrieval",
            },
        },
    }
    payload = mapping.get(user_question)
    if payload is None:
        raise AssertionError(f"Unexpected planner question: {user_question}")
    return payload


def _build_review_payload(user_question: str):
    mapping = {
        "오늘 DA 공정에서 DDR5 생산량이랑 재공 알려줘": {
            "missing_dataset_keys": [],
            "needs_post_processing": False,
            "reason": "",
        },
        "오늘 WB공정에서 생산량 알려줘": {
            "missing_dataset_keys": [],
            "needs_post_processing": False,
            "reason": "",
        },
        "오늘 DA공정 생산량 알려줘": {
            "missing_dataset_keys": [],
            "needs_post_processing": False,
            "reason": "",
        },
        "오늘 생산과 목표를 같이 보여줘": {
            "missing_dataset_keys": [],
            "needs_post_processing": False,
            "reason": "",
        },
        "오늘 DA공정에서 MODE별 생산량 알려줘": {
            "missing_dataset_keys": [],
            "needs_post_processing": True,
            "reason": "grouping needs post processing",
        },
    }
    payload = mapping.get(user_question)
    if payload is None:
        raise AssertionError(f"Unexpected review question: {user_question}")
    return payload


def _extract_user_question(prompt: str) -> str:
    marker = "User question:\n"
    if marker not in prompt:
        raise AssertionError(f"Prompt does not contain user question marker: {prompt[:120]}")
    return prompt.split(marker, 1)[1].split("\n\n", 1)[0].strip()


class _FakeResponse:
    def __init__(self, payload):
        self.content = json.dumps(payload, ensure_ascii=False)


class _ParameterLLM:
    def invoke(self, messages):
        question = _extract_user_question(messages[-1].content)
        return _FakeResponse(_build_param_payload(question))


class _PlannerLLM:
    def invoke(self, messages):
        prompt = messages[-1].content
        question = _extract_user_question(prompt)
        if "planned manufacturing datasets miss any base datasets" in prompt:
            return _FakeResponse(_build_review_payload(question))
        return _FakeResponse(_build_plan_payload(question))


def _fake_generate_response(user_input, result, chat_history):
    return f"{result.get('tool_name', 'result')}:{len(result.get('data', []))}"


def _fake_execute_analysis_query(query_text, data, source_tool_name=""):
    grouped = {}
    for row in data:
        mode = str(row.get("MODE", "UNKNOWN"))
        grouped.setdefault(mode, 0)
        grouped[mode] += float(row.get("production", 0) or 0)

    result_rows = [
        {"MODE": mode, "production": int(total)}
        for mode, total in sorted(grouped.items())
    ]
    return {
        "success": True,
        "tool_name": "analyze_current_data",
        "data": result_rows,
        "summary": f"grouped {len(result_rows)} rows",
        "analysis_plan": {"group_by": ["MODE"]},
        "analysis_logic": "test_groupby_mode",
    }


class EndToEndExampleStep4Tests(unittest.TestCase):
    def _run_agent(self, user_input, chat_history=None, context=None, current_data=None):
        progress_steps = []

        with patch("manufacturing_agent.services.parameter_service.get_llm_for_task", return_value=_ParameterLLM()), patch(
            "manufacturing_agent.services.retrieval_planner.get_llm_for_task",
            return_value=_PlannerLLM(),
        ), patch(
            "manufacturing_agent.services.runtime_service.generate_response",
            side_effect=_fake_generate_response,
        ), patch(
            "manufacturing_agent.services.runtime_service.execute_analysis_query",
            side_effect=_fake_execute_analysis_query,
        ):
            result = run_agent_with_progress(
                user_input=user_input,
                chat_history=chat_history or [],
                context=context or {},
                current_data=current_data,
                progress_callback=lambda title, detail: progress_steps.append(title),
            )

        return result, progress_steps

    def test_followup_scope_change_triggers_new_retrieval(self):
        first_result, first_steps = self._run_agent("오늘 DA 공정에서 DDR5 생산량이랑 재공 알려줘")
        second_result, second_steps = self._run_agent(
            "오늘 WB공정에서 생산량 알려줘",
            chat_history=[
                {"role": "user", "content": "오늘 DA 공정에서 DDR5 생산량이랑 재공 알려줘"},
                {"role": "assistant", "content": first_result["response"]},
            ],
            context=first_result["extracted_params"],
            current_data=first_result["current_data"],
        )

        self.assertEqual(len(first_steps), 3)
        self.assertEqual(len(second_steps), 3)
        self.assertEqual(
            second_result["current_data"]["retrieval_applied_params"].get("process_name"),
            WB_PROCESS,
        )
        self.assertIsNone(second_result["current_data"]["retrieval_applied_params"].get("product_name"))
        self.assertTrue(
            all(str(row.get("OPER_NAME", "")).startswith("W/B") for row in second_result["current_data"].get("data", []))
        )

    def test_same_scope_grouping_stays_followup_transform(self):
        first_result, first_steps = self._run_agent("오늘 DA공정 생산량 알려줘")
        second_result, second_steps = self._run_agent(
            "그 결과를 MODE별로 정리해줘",
            chat_history=[
                {"role": "user", "content": "오늘 DA공정 생산량 알려줘"},
                {"role": "assistant", "content": first_result["response"]},
            ],
            context=first_result["extracted_params"],
            current_data=first_result["current_data"],
        )

        self.assertEqual(len(first_steps), 3)
        self.assertEqual([step[:3] for step in second_steps], ["1/3", "3/3"])
        self.assertEqual(second_result["current_data"]["tool_name"], "analyze_current_data")
        self.assertTrue(second_result["current_data"].get("source_snapshots"))
        self.assertEqual(second_result["current_data"].get("source_dataset_keys"), ["production"])

    def test_multi_dataset_question_keeps_both_sources(self):
        result, progress_steps = self._run_agent("오늘 생산과 목표를 같이 보여줘")

        self.assertEqual(len(progress_steps), 3)
        self.assertEqual(result["current_data"].get("source_dataset_keys"), ["production", "target"])
        self.assertIn("production", result["current_data"].get("current_datasets", {}))
        self.assertIn("target", result["current_data"].get("current_datasets", {}))

    def test_first_turn_post_processing_runs_after_single_retrieval(self):
        result, progress_steps = self._run_agent("오늘 DA공정에서 MODE별 생산량 알려줘")

        self.assertEqual(len(progress_steps), 3)
        self.assertEqual(result["current_data"]["tool_name"], "analyze_current_data")
        self.assertTrue(result["current_data"].get("source_snapshots"))
        self.assertEqual(result["current_data"].get("source_dataset_keys"), ["production"])


if __name__ == "__main__":
    unittest.main()
