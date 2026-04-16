import unittest
from datetime import datetime
from unittest.mock import patch

from manufacturing_agent.services.parameter_service import (
    adjust_retrieval_params_for_context_reset,
    apply_context_inheritance,
    resolve_required_params,
)
from manufacturing_agent.services.query_mode import choose_query_mode


class QueryModeStep1Tests(unittest.TestCase):
    def test_context_inheritance_marks_date_like_other_fields(self):
        inherited = apply_context_inheritance(
            extracted_params={},
            context={
                "date": "20260415",
                "product_name": "DDR5",
            },
        )

        self.assertEqual(inherited.get("date"), "20260415")
        self.assertTrue(inherited.get("date_inherited"))
        self.assertEqual(inherited.get("product_name"), "DDR5")
        self.assertTrue(inherited.get("product_inherited"))

    def test_process_change_resets_old_inherited_product_filter(self):
        raw_params = {
            "date": "20260415",
            "process_name": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"],
        }
        inherited_params = apply_context_inheritance(
            extracted_params=raw_params,
            context={
                "date": "20260415",
                "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
                "product_name": "DDR5",
            },
        )

        adjusted_params = adjust_retrieval_params_for_context_reset(
            raw_extracted_params=raw_params,
            extracted_params=inherited_params,
            current_data={
                "retrieval_applied_params": {
                    "date": "20260415",
                    "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
                    "product_name": "DDR5",
                }
            },
        )

        self.assertEqual(adjusted_params.get("date"), "20260415")
        self.assertEqual(adjusted_params.get("process_name"), raw_params["process_name"])
        self.assertIsNone(adjusted_params.get("product_name"))

    def test_raw_params_do_not_inherit_old_product_filter(self):
        today = datetime.now().strftime("%Y%m%d")
        context = {
            "date": today,
            "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
            "product_name": "DDR5",
        }
        with patch("manufacturing_agent.services.parameter_service.get_llm_for_task", side_effect=RuntimeError("skip llm")):
            params = resolve_required_params(
                user_input="오늘 WB공정에서 생산량 알려줘",
                chat_history_text="",
                current_data_columns=[],
                context=context,
                inherit_context=False,
            )

        self.assertEqual(params.get("date"), today)
        self.assertEqual(
            params.get("process_name"),
            ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"],
        )
        self.assertIsNone(params.get("product_name"))

    def test_process_change_goes_to_retrieval(self):
        current_data = {
            "tool_name": "get_production_data",
            "data": [{"OPER_NAME": "D/A3", "MODE": "DDR5", "production": 2940}],
            "dataset_key": "production",
            "source_dataset_keys": ["production", "wip"],
            "applied_params": {
                "date": "20260415",
                "process_name": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
                "product_name": "DDR5",
            },
        }
        extracted_params = {
            "date": "20260415",
            "process_name": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"],
        }

        query_mode = choose_query_mode(
            user_input="오늘 WB공정에서 생산량 알려줘",
            current_data=current_data,
            extracted_params=extracted_params,
        )

        self.assertEqual(query_mode, "retrieval")

    def test_required_date_change_goes_to_retrieval(self):
        current_data = {
            "tool_name": "get_production_data",
            "data": [{"OPER_NAME": "D/A3", "production": 2940}],
            "dataset_key": "production",
            "source_dataset_keys": ["production"],
            "applied_params": {"date": "20260415"},
        }

        query_mode = choose_query_mode(
            user_input="어제로 바꿔서 다시 알려줘",
            current_data=current_data,
            extracted_params={"date": "20260414"},
        )

        self.assertEqual(query_mode, "retrieval")

    def test_grouping_request_stays_followup(self):
        current_data = {
            "tool_name": "get_production_data",
            "data": [{"OPER_NAME": "D/A3", "MODE": "DDR5", "production": 2940}],
            "dataset_key": "production",
            "source_dataset_keys": ["production"],
            "applied_params": {"date": "20260415"},
        }

        query_mode = choose_query_mode(
            user_input="그 결과를 MODE별로 정리해줘",
            current_data=current_data,
            extracted_params={},
        )

        self.assertEqual(query_mode, "followup_transform")

    def test_filter_removal_goes_to_retrieval(self):
        current_data = {
            "tool_name": "get_production_data",
            "data": [{"OPER_NAME": "D/A3", "MODE": "DDR5", "production": 2940}],
            "dataset_key": "production",
            "source_dataset_keys": ["production"],
            "retrieval_applied_params": {
                "date": "20260415",
                "product_name": "DDR5",
            },
        }

        query_mode = choose_query_mode(
            user_input="DDR5 조건 빼고 전체 생산량 알려줘",
            current_data=current_data,
            extracted_params={},
        )

        self.assertEqual(query_mode, "retrieval")


if __name__ == "__main__":
    unittest.main()
