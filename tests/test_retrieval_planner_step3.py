import json
import unittest
from unittest.mock import patch

from manufacturing_agent.services.retrieval_planner import plan_retrieval_request


class _FakeResponse:
    def __init__(self, payload):
        self.content = json.dumps(payload, ensure_ascii=False)


class _PlannerStubLLM:
    def __init__(self, plan_payload, review_payload):
        self.plan_payload = plan_payload
        self.review_payload = review_payload

    def invoke(self, messages):
        prompt = messages[-1].content
        if "planning which registered datasets should be retrieved" in prompt:
            return _FakeResponse(self.plan_payload)
        if "reviewing whether the planned manufacturing datasets miss any base datasets" in prompt:
            return _FakeResponse(self.review_payload)
        raise AssertionError(f"Unexpected prompt: {prompt[:120]}")


class RetrievalPlannerStep3Tests(unittest.TestCase):
    def test_review_adds_missing_base_dataset(self):
        llm = _PlannerStubLLM(
            plan_payload={
                "dataset_keys": ["production"],
                "needs_post_processing": True,
                "analysis_goal": "achievement rate",
                "merge_hints": {
                    "pre_aggregate_before_join": True,
                    "group_dimensions": ["OPER_NAME"],
                    "dataset_metrics": {
                        "production": ["production"],
                        "target": ["target"],
                    },
                    "aggregation": "sum",
                    "reason": "Need numerator and denominator",
                },
            },
            review_payload={
                "missing_dataset_keys": ["target"],
                "needs_post_processing": True,
                "reason": "achievement rate needs target",
            },
        )

        with patch("manufacturing_agent.services.retrieval_planner.get_llm_for_task", return_value=llm):
            result = plan_retrieval_request("오늘 생산 달성률 보여줘", [], None)

        self.assertEqual(result["dataset_keys"], ["production", "target"])
        self.assertTrue(result["needs_post_processing"])
        self.assertEqual(
            set(result["merge_hints"].get("dataset_metrics", {}).keys()),
            {"production", "target"},
        )

    def test_merge_hints_are_pruned_to_final_dataset_keys(self):
        llm = _PlannerStubLLM(
            plan_payload={
                "dataset_keys": ["production", "wip"],
                "needs_post_processing": False,
                "analysis_goal": "overview",
                "merge_hints": {
                    "pre_aggregate_before_join": True,
                    "group_dimensions": ["OPER_NAME"],
                    "dataset_metrics": {
                        "production": ["production"],
                        "target": ["target"],
                        "wip": ["재공수량"],
                    },
                    "aggregation": "sum",
                    "reason": "stale target should be removed",
                },
            },
            review_payload={
                "missing_dataset_keys": [],
                "needs_post_processing": False,
                "reason": "",
            },
        )

        with patch("manufacturing_agent.services.retrieval_planner.get_llm_for_task", return_value=llm):
            result = plan_retrieval_request("오늘 생산이랑 재공 보여줘", [], None)

        self.assertEqual(result["dataset_keys"], ["production", "wip"])
        self.assertEqual(
            set(result["merge_hints"].get("dataset_metrics", {}).keys()),
            {"production", "wip"},
        )

    def test_slash_query_keeps_post_processing_when_review_flags_analysis(self):
        llm = _PlannerStubLLM(
            plan_payload={
                "dataset_keys": ["production", "target"],
                "needs_post_processing": True,
                "analysis_goal": "ratio",
                "merge_hints": {
                    "pre_aggregate_before_join": True,
                    "group_dimensions": ["OPER_NAME"],
                    "dataset_metrics": {
                        "production": ["production"],
                        "target": ["target"],
                    },
                    "aggregation": "sum",
                    "reason": "ratio needs join",
                },
            },
            review_payload={
                "missing_dataset_keys": [],
                "needs_post_processing": True,
                "reason": "ratio question still needs analysis",
            },
        )

        with patch("manufacturing_agent.services.retrieval_planner.get_llm_for_task", return_value=llm):
            result = plan_retrieval_request("오늘 production/target ratio 보여줘", [], None)

        self.assertEqual(result["dataset_keys"], ["production", "target"])
        self.assertTrue(result["needs_post_processing"])


if __name__ == "__main__":
    unittest.main()
