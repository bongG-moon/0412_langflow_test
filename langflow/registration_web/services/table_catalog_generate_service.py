from __future__ import annotations

import json
import re
from typing import Any, Dict

from .llm_client import invoke_llm_json


SQL_TEXT_KEYS = ("sql_template", "query_template", "sql", "sql_text", "query", "oracle_sql")
TRIPLE_DOUBLE_SQL_BLOCK_RE = re.compile(
    r'(?P<prefix>"(?:sql_template|query_template|sql|sql_text|query|oracle_sql)"\s*:\s*)"""(?P<body>.*?)"""',
    re.DOTALL,
)
TRIPLE_SINGLE_SQL_BLOCK_RE = re.compile(
    r"(?P<prefix>\"(?:sql_template|query_template|sql|sql_text|query|oracle_sql)\"\s*:\s*)'''(?P<body>.*?)'''",
    re.DOTALL,
)


def _replace_sql_block(match: re.Match[str]) -> str:
    sql_text = match.group("body").strip("\r\n")
    return f"{match.group('prefix')}{json.dumps(sql_text, ensure_ascii=False)}"


def normalize_relaxed_json_text(text: str) -> str:
    text = TRIPLE_DOUBLE_SQL_BLOCK_RE.sub(_replace_sql_block, str(text or ""))
    text = TRIPLE_SINGLE_SQL_BLOCK_RE.sub(_replace_sql_block, text)
    return text


def try_parse_table_catalog_text(raw_text: str) -> Dict[str, Any] | None:
    cleaned = str(raw_text or "").strip()
    if not cleaned:
        return None
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    if not cleaned.startswith("{"):
        return None
    return json.loads(normalize_relaxed_json_text(cleaned))


def build_table_catalog_prompt(raw_text: str, existing_table_items: list[Dict[str, Any]]) -> str:
    existing_summary = [
        {
            "dataset_key": item.get("dataset_key"),
            "display_name": item.get("display_name"),
            "keywords": item.get("keywords", []),
            "tool_name": item.get("tool_name", ""),
        }
        for item in existing_table_items
    ]
    output_schema = {
        "catalog_id": "manufacturing_table_catalog",
        "status": "active",
        "datasets": {
            "dataset_key": {
                "display_name": "데이터 표시명",
                "description": "질문 라우팅과 분석에 필요한 설명",
                "keywords": ["질문 키워드"],
                "question_examples": ["이 데이터가 필요한 질문 예시"],
                "tool_name": "get_dataset_key_data",
                "source_type": "oracle",
                "required_params": ["date"],
                "db_key": "MES|PLAN|...",
                "table_name": "ORACLE_TABLE_NAME",
                "sql_template": "SELECT ... WHERE WORK_DT = :date",
                "bind_params": {"date": "date"},
                "columns": [
                    {"name": "WORK_DT", "type": "date", "description": "컬럼 설명"},
                    {"name": "production", "type": "number", "description": "생산량"},
                ],
            }
        },
    }
    return f"""당신은 제조 데이터 분석 Agent의 Table Catalog JSON을 작성하는 전문가입니다.
반드시 JSON object만 반환하세요. markdown fence는 쓰지 마세요.

목표:
- 사용자가 붙여넣은 SQL, DDL, 컬럼 설명, 자연어 설명을 Main Flow Table Catalog 형식으로 변환합니다.
- sql_template은 줄바꿈이 보존된 하나의 문자열로 작성합니다.
- SQL bind 변수는 Oracle 형식의 :date, :product 같은 이름을 사용합니다.
- required_params는 사용자 질문에서 반드시 추출되어야 하는 파라미터입니다.
- bind_params는 SQL bind 변수명을 Agent 파라미터명으로 매핑합니다.
- 질문 의도 매핑에 필요한 keywords와 question_examples를 충분히 작성합니다.

이미 등록된 테이블 정의 요약:
{json.dumps(existing_summary, ensure_ascii=False, indent=2)}

반환 스키마:
{json.dumps(output_schema, ensure_ascii=False, indent=2)}

컬럼 타입은 string, number, date, datetime, boolean 중 하나만 사용하세요.
source_type은 기본 oracle로 두세요.
dataset_key와 tool_name은 안정적인 snake_case로 작성하세요.

사용자 입력:
{raw_text}
"""


def generate_table_catalog(
    raw_text: str,
    api_key: str,
    model_name: str,
    temperature: float,
    existing_table_items: list[Dict[str, Any]],
    force_llm: bool = False,
) -> Dict[str, Any]:
    parsed = None if force_llm else try_parse_table_catalog_text(raw_text)
    if parsed is not None:
        return {"table_catalog_raw": parsed, "used_llm": False, "prompt": "", "llm_text": ""}

    prompt = build_table_catalog_prompt(raw_text, existing_table_items)
    llm_json = invoke_llm_json(prompt, api_key, model_name, temperature)
    llm_text = str(llm_json.pop("_llm_text", ""))
    return {"table_catalog_raw": llm_json, "used_llm": True, "prompt": prompt, "llm_text": llm_text}
