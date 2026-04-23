import json
import unittest
from pathlib import Path

from langflow.registration_web.services.table_catalog_generate_service import build_table_catalog_prompt
from langflow.registration_web.services.table_catalog_validation_service import normalize_and_validate_table_catalog


ROOT = Path(__file__).resolve().parents[1]
REG_WEB_DIR = ROOT / "langflow" / "registration_web"


class RegistrationWebTableCatalogTests(unittest.TestCase):
    def test_generation_prompt_uses_metadata_only_schema(self):
        prompt = build_table_catalog_prompt("production table info", [])

        self.assertIn('"format_params"', prompt)
        self.assertIn("SQL은 Table Catalog에 저장하지 않습니다", prompt)
        self.assertNotIn('"sql_template":', prompt)
        self.assertNotIn('"bind_params":', prompt)

    def test_validation_strips_legacy_sql_and_bind_fields(self):
        raw_catalog = {
            "catalog_id": "manufacturing_table_catalog",
            "datasets": {
                "production": {
                    "display_name": "생산 실적",
                    "description": "생산 실적 데이터",
                    "keywords": ["생산"],
                    "tool_name": "get_production_data",
                    "source_type": "oracle",
                    "required_params": ["date"],
                    "db_key": "MES",
                    "table_name": "PROD_TABLE",
                    "sql_template": "SELECT WORK_DT FROM PROD_TABLE WHERE WORK_DT = :date",
                    "bind_params": {"date": "date"},
                    "columns": [{"name": "WORK_DT", "type": "date", "description": "작업일자"}],
                }
            },
        }

        result = normalize_and_validate_table_catalog(raw_catalog, [])
        dataset = result["table_catalog"]["datasets"]["production"]
        issue_types = {issue["type"] for issue in result["issues"]}

        self.assertTrue(result["can_save"])
        self.assertNotIn("sql_template", dataset)
        self.assertNotIn("bind_params", dataset)
        self.assertEqual(dataset["format_params"], ["date"])
        self.assertIn("sql_fields_ignored", issue_types)
        self.assertIn("legacy_bind_params_ignored", issue_types)

    def test_streamlit_table_input_example_matches_metadata_contract(self):
        example = (REG_WEB_DIR / "examples" / "table_input_example.txt").read_text(encoding="utf-8")

        self.assertIn("format_params", example)
        self.assertNotIn("sql_template", example)
        self.assertNotIn("bind_params", example)
        self.assertNotIn(":date", example)


if __name__ == "__main__":
    unittest.main()
