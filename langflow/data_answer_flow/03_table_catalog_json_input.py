from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# Compatibility scaffolding for local tests. In lfx Langflow this can be
# replaced with direct imports from lfx.custom, lfx.io, and lfx.schema.
def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback


class _FallbackComponent:
    display_name = ""
    description = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""


@dataclass
class _FallbackInput:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    advanced: bool = False
    tool_mode: bool = False
    input_types: list[str] | None = None


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


DEFAULT_TABLE_CATALOG_JSON = '''{
  "catalog_id": "manufacturing_table_catalog",
  "datasets": {
    "production": {
      "display_name": "생산 데이터",
      "description": "일자/공정/제품별 생산 실적 raw data",
      "keywords": ["생산량", "실적", "생산 실적"],
      "question_examples": ["오늘 A제품 생산량 알려줘"],
      "tool_name": "get_production_data",
      "source_type": "oracle",
      "required_params": ["date"],
      "db_key": "MES",
      "table_name": "PROD_TABLE",
      "sql_template": """
SELECT
    WORK_DT,
    OPER_NAME,
    MODE,
    DEN,
    TECH,
    MCP_NO,
    PKG_TYPE1,
    PKG_TYPE2,
    LINE,
    QTY AS production
FROM PROD_TABLE
WHERE WORK_DT = :date
  AND NVL(DELETE_FLAG, 'N') = 'N'
  AND SITE_CODE = "K1"
""",
      "bind_params": {
        "date": "date"
      },
      "columns": [
        {"name": "WORK_DT", "type": "date", "description": "작업일"},
        {"name": "OPER_NAME", "type": "string", "description": "공정명"},
        {"name": "production", "type": "number", "description": "생산량"}
      ]
    }
  }
}'''


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


class TableCatalogJsonInput(Component):
    display_name = "Table Catalog JSON Input"
    description = "Input table catalog text used by the data answer flow."
    icon = "TableProperties"
    name = "TableCatalogJsonInput"

    inputs = [
        MultilineInput(
            name="table_catalog_json",
            display_name="Table Catalog JSON",
            info='Paste table catalog text. For copy-paste SQL, use "sql_template": """...""".',
            value=DEFAULT_TABLE_CATALOG_JSON,
        ),
    ]

    outputs = [
        Output(name="table_catalog_json_payload", display_name="Table Catalog JSON Payload", method="build_payload", types=["Data"]),
    ]

    def build_payload(self) -> Data:
        text = str(getattr(self, "table_catalog_json", "") or "").strip()
        self.status = {"chars": len(text)}
        return _make_data({"table_catalog_json": text})
