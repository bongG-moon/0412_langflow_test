import unittest
from unittest.mock import patch

from manufacturing_agent.services.response_service import build_response_prompt, generate_response


class _FakeResponseLLM:
    def __init__(self):
        self.prompts = []

    def invoke(self, messages):
        self.prompts.append(messages[-1].content)

        class _Response:
            content = "요약 응답"

        return _Response()


class ResponsePromptStep5Tests(unittest.TestCase):
    def test_build_response_prompt_includes_applied_filter_scope(self):
        result = {
            "summary": "DA 공정 달성율 분석 완료",
            "data": [
                {"OPER_NAME": "D/A1", "achievement_rate": 0.92},
                {"OPER_NAME": "D/A2", "achievement_rate": 0.64},
            ],
            "analysis_plan": {"group_by": ["OPER_NAME"]},
            "retrieval_applied_params": {
                "date": "20260415",
                "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
                "product_name": "DDR5",
            },
            "source_dataset_keys": ["production", "target"],
            "available_columns": ["OPER_NAME", "achievement_rate"],
            "analysis_base_info": {
                "join_columns": ["OPER_NAME"],
                "requested_dimensions": ["OPER_NAME"],
            },
        }

        prompt = build_response_prompt(
            "오늘 DA공정에서 DDR5제품의 생산 달성율을 세부 공정별로 알려줘",
            result,
            [],
        )

        self.assertIn("조회 범위 정보", prompt)
        self.assertIn('"product_name": "DDR5"', prompt)
        self.assertIn('"source_dataset_keys": ["production", "target"]', prompt)
        self.assertIn("필터가 이미 원본 데이터에 적용된 것으로 간주", prompt)

    def test_generate_response_passes_scope_info_to_llm(self):
        fake_llm = _FakeResponseLLM()
        result = {
            "summary": "분석 완료",
            "data": [{"OPER_NAME": "D/A1", "achievement_rate": 0.92}],
            "analysis_plan": {"group_by": ["OPER_NAME"]},
            "retrieval_applied_params": {
                "date": "20260415",
                "product_name": "DDR5",
            },
            "source_dataset_keys": ["production", "target"],
            "available_columns": ["OPER_NAME", "achievement_rate"],
        }

        with patch("manufacturing_agent.services.response_service.get_llm_for_task", return_value=fake_llm):
            response = generate_response(
                "오늘 DA공정에서 DDR5제품의 생산 달성율을 세부 공정별로 알려줘",
                result,
                [],
            )

        self.assertEqual(response, "요약 응답")
        self.assertTrue(fake_llm.prompts)
        self.assertIn('"product_name": "DDR5"', fake_llm.prompts[0])
        self.assertIn("조회 범위 정보", fake_llm.prompts[0])


if __name__ == "__main__":
    unittest.main()
