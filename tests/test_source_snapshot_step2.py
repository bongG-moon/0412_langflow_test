import unittest
from unittest.mock import patch

from manufacturing_agent.services.runtime_service import (
    prepare_retrieval_source_results,
    run_followup_analysis,
)


class SourceSnapshotStep2Tests(unittest.TestCase):
    def test_prepare_retrieval_source_results_reuses_snapshot(self):
        current_data = {
            "source_snapshots": [
                {
                    "dataset_key": "production",
                    "dataset_label": "생산",
                    "tool_name": "get_production_data",
                    "summary": "raw snapshot",
                    "required_params": {"date": "20260415"},
                    "data": [
                        {"WORK_DT": "20260415", "OPER_NAME": "D/A3", "production": 2940},
                        {"WORK_DT": "20260415", "OPER_NAME": "W/B1", "production": 1840},
                    ],
                }
            ]
        }
        jobs = [
            {
                "dataset_key": "production",
                "params": {
                    "date": "20260415",
                    "process_name": ["W/B1", "W/B2", "W/B3", "W/B4", "W/B5", "W/B6"],
                },
            }
        ]

        with patch(
            "manufacturing_agent.services.runtime_service.execute_retrieval_jobs",
            side_effect=AssertionError("raw snapshot should be reused before running retrieval"),
        ):
            prepared = prepare_retrieval_source_results(jobs, current_data=current_data)

        self.assertEqual(len(prepared["source_results"]), 1)
        result = prepared["source_results"][0]
        self.assertTrue(result.get("reused_source_snapshot"))
        self.assertEqual([row["OPER_NAME"] for row in result["data"]], ["W/B1"])
        self.assertEqual(prepared["source_snapshots"][0]["required_params"], {"date": "20260415"})

    def test_followup_analysis_keeps_source_snapshots(self):
        current_data = {
            "tool_name": "get_production_data",
            "data": [{"OPER_NAME": "D/A3", "production": 2940}],
            "source_dataset_keys": ["production"],
            "current_datasets": {
                "production": {
                    "label": "생산",
                    "tool_name": "get_production_data",
                    "summary": "raw snapshot",
                    "row_count": 2,
                    "columns": ["OPER_NAME", "production"],
                    "data": [
                        {"OPER_NAME": "D/A3", "production": 2940},
                        {"OPER_NAME": "W/B1", "production": 1840},
                    ],
                }
            },
            "source_snapshots": [
                {
                    "dataset_key": "production",
                    "dataset_label": "생산",
                    "tool_name": "get_production_data",
                    "summary": "raw snapshot",
                    "required_params": {"date": "20260415"},
                    "data": [
                        {"OPER_NAME": "D/A3", "production": 2940},
                        {"OPER_NAME": "W/B1", "production": 1840},
                    ],
                }
            ],
        }

        with patch(
            "manufacturing_agent.services.runtime_service.execute_analysis_query",
            return_value={
                "success": True,
                "tool_name": "analysis_result",
                "data": [{"MODE": "DDR5", "production": 2940}],
                "summary": "grouped result",
            },
        ), patch(
            "manufacturing_agent.services.runtime_service.generate_response",
            return_value="grouped result",
        ):
            result = run_followup_analysis(
                user_input="그 결과를 MODE별로 정리해줘",
                chat_history=[],
                current_data=current_data,
                extracted_params={},
            )

        self.assertTrue(result["current_data"]["source_snapshots"])
        self.assertIn("production", result["current_data"]["current_datasets"])


if __name__ == "__main__":
    unittest.main()
