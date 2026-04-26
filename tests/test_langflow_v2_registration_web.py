import importlib
import json


domain_v2 = importlib.import_module("langflow_v2.registration_web.services.domain_v2")
domain_text_v2 = importlib.import_module("langflow_v2.registration_web.services.domain_text_v2")
table_v2 = importlib.import_module("langflow_v2.registration_web.services.table_catalog_v2")
table_text_v2 = importlib.import_module("langflow_v2.registration_web.services.table_text_v2")


def test_domain_metric_form_item_matches_v2_metric_contract():
    item = domain_v2.make_item(
        "metrics",
        "achievement_rate",
        {
            "display_name": "Achievement Rate",
            "aliases": "달성률\n달성율\n목표 대비\nachievement",
            "required_datasets": "production, target",
            "formula": "sum(production) / sum(target) * 100",
            "output_column": "achievement_rate",
            "source_columns": "production, target",
            "grouping_hint": "MODE, OPER_NAME",
        },
    )

    assert item["gbn"] == "metrics"
    assert item["key"] == "achievement_rate"
    assert item["payload"]["required_datasets"] == ["production", "target"]
    assert item["payload"]["source_columns"] == ["production", "target"]
    assert item["payload"]["grouping_hint"] == ["MODE", "OPER_NAME"]
    assert "달성율" in item["payload"]["aliases"]


def test_domain_json_import_accepts_aggregate_and_exports_items():
    raw = {
        "domain": {
            "process_groups": {
                "WB": {
                    "display_name": "Wire Bond",
                    "aliases": ["WB", "W/B", "WB공정"],
                    "processes": ["W/B1", "W/B2"],
                }
            },
            "metrics": {
                "achievement_rate": {
                    "display_name": "Achievement Rate",
                    "aliases": ["달성률", "달성율"],
                    "required_datasets": ["production", "target"],
                    "formula": "sum(production) / sum(target) * 100",
                    "output_column": "achievement_rate",
                }
            },
            "join_rules": [],
        }
    }

    normalized = domain_v2.normalize_domain_input(json.dumps(raw, ensure_ascii=False))
    items = normalized["items"]
    aggregate = domain_v2.aggregate_domain(items)

    assert normalized["errors"] == []
    assert {item["gbn"] for item in items} == {"process_groups", "metrics"}
    assert aggregate["process_groups"]["WB"]["processes"] == ["W/B1", "W/B2"]
    assert aggregate["metrics"]["achievement_rate"]["required_datasets"] == ["production", "target"]


def test_domain_text_preview_uses_llm_items_without_manual_category_selection():
    def fake_llm(_prompt):
        return {
            "items": [
                {
                    "gbn": "metrics",
                    "key": "achievement_rate",
                    "status": "active",
                    "payload": {
                        "display_name": "생산달성율",
                        "aliases": ["생산달성율", "생산달성률", "달성율", "달성률"],
                        "required_datasets": ["production", "wip"],
                        "formula": "sum(production) / sum(wip_qty) * 100",
                        "output_column": "achievement_rate",
                        "source_columns": ["production", "wip_qty"],
                        "grouping_hint": ["MODE"],
                    },
                    "warnings": [],
                }
            ],
            "unmapped_text": "",
        }

    preview = domain_text_v2.build_domain_preview_from_text(
        "생산달성율은 생산량 / 재공 * 100이고 mode별로 본다.",
        llm_api_key="unused",
        model_name="unused",
        temperature=0.0,
        existing_items=[],
        llm_func=fake_llm,
    )

    assert preview["items"][0]["gbn"] == "metrics"
    assert preview["items"][0]["payload"]["required_datasets"] == ["production", "wip"]
    assert preview["items"][0]["payload"]["grouping_hint"] == ["MODE"]
    assert preview["items"][0]["source_text"].startswith("생산달성율")


def test_table_catalog_form_item_drops_sql_and_exports_loader_json():
    item = table_v2.normalize_dataset(
        "production",
        {
            "display_name": "Production",
            "source_type": "oracle",
            "tool_name": "get_production_data",
            "required_params": "date",
            "keywords": "생산\nproduction",
            "columns": "WORK_DT | date | work date\nproduction | number | production quantity",
            "filter_mappings": {"process_name": ["OPER_NAME"], "mode": ["MODE"]},
            "sql": "select * from hidden",
        },
    )
    catalog = table_v2.table_catalog([item])

    assert item["dataset_key"] == "production"
    assert "sql" not in item
    assert catalog["datasets"]["production"]["tool_name"] == "get_production_data"
    assert catalog["datasets"]["production"]["columns"][1]["name"] == "production"
    assert catalog["datasets"]["production"]["filter_mappings"]["process_name"] == ["OPER_NAME"]


def test_table_text_preview_uses_llm_items_and_still_drops_sql():
    def fake_llm(_prompt):
        return {
            "items": [
                {
                    "dataset_key": "production",
                    "status": "active",
                    "display_name": "Production",
                    "source_type": "oracle",
                    "db_key": "PKG_RPT",
                    "tool_name": "get_production_data",
                    "required_params": ["date"],
                    "format_params": ["date"],
                    "keywords": ["생산", "production"],
                    "columns": [{"name": "production", "type": "number", "description": "production quantity"}],
                    "sql": "select * from hidden",
                }
            ]
        }

    preview = table_text_v2.build_table_preview_from_text(
        "production 데이터셋은 Oracle에서 조회한다.",
        llm_api_key="unused",
        model_name="unused",
        temperature=0.0,
        existing_items=[],
        llm_func=fake_llm,
    )

    item = preview["items"][0]
    assert item["dataset_key"] == "production"
    assert item["source_type"] == "oracle"
    assert "sql" not in item
