import json
import unittest
from unittest.mock import patch

from manufacturing_agent.data.retrieval import (
    dataset_required_param_fields,
    dataset_requires_date,
    dataset_requires_param,
)
from manufacturing_agent.services.retrieval_planner import plan_retrieval_request


class _FakeResponse:
    def __init__(self, payload):
        self.content = json.dumps(payload, ensure_ascii=False)


class _PlannerFallbackLLM:
    def invoke(self, messages):
        prompt = messages[-1].content
        if "planning which registered datasets should be retrieved" in prompt:
            return _FakeResponse(
                {
                    "dataset_keys": [],
                    "needs_post_processing": False,
                    "analysis_goal": "",
                    "merge_hints": {},
                }
            )
        if "planned manufacturing datasets miss any base datasets" in prompt:
            return _FakeResponse(
                {
                    "missing_dataset_keys": [],
                    "needs_post_processing": False,
                    "reason": "",
                }
            )
        raise AssertionError(f"Unexpected prompt: {prompt[:120]}")


class RetrievalRegistryStep6Tests(unittest.TestCase):
    def test_dataset_required_param_fields_is_generic_source_of_truth(self):
        self.assertEqual(dataset_required_param_fields("production"), ["date"])
        self.assertTrue(dataset_requires_param("production", "date"))
        self.assertTrue(dataset_requires_date("production"))
        self.assertFalse(dataset_requires_param("production", "process_name"))
        self.assertEqual(dataset_required_param_fields("unknown_dataset"), [])

    def test_planner_uses_keyword_fallback_when_llm_returns_no_dataset(self):
        with patch("manufacturing_agent.services.retrieval_planner.get_llm_for_task", return_value=_PlannerFallbackLLM()):
            result = plan_retrieval_request("오늘 생산이랑 재공 보여줘", [], None)

        self.assertEqual(result["dataset_keys"], ["production", "wip"])
        self.assertFalse(result["needs_post_processing"])


if __name__ == "__main__":
    unittest.main()
