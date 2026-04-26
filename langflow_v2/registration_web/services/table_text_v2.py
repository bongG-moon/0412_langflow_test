from __future__ import annotations

import json
from typing import Any, Callable, Dict

from .llm_client import invoke_llm_json
from .table_catalog_v2 import normalize_table_input


LLMJsonFn = Callable[[str], Dict[str, Any]]


def _compact_json(value: Any, limit: int = 7000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED..."


def _existing_summary(existing_items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [
        {
            "dataset_key": item.get("dataset_key", ""),
            "display_name": item.get("display_name", ""),
            "source_type": item.get("source_type", ""),
            "tool_name": item.get("tool_name", ""),
            "keywords": item.get("keywords", []),
        }
        for item in existing_items[:80]
    ]


def build_table_prompt(raw_text: str, existing_items: list[Dict[str, Any]]) -> str:
    output_schema = {
        "items": [
            {
                "dataset_key": "production",
                "status": "active",
                "display_name": "Production",
                "description": "daily production dataset",
                "source_type": "oracle|dummy|mongodb|api|file|manual|auto",
                "db_key": "PKG_RPT",
                "table_name": "optional physical table name",
                "tool_name": "get_production_data",
                "required_params": ["date"],
                "format_params": ["date"],
                "keywords": ["생산", "production"],
                "aliases": ["생산량"],
                "question_examples": ["오늘 생산량 알려줘"],
                "columns": [
                    {"name": "WORK_DT", "type": "date", "description": "work date"},
                    {"name": "production", "type": "number", "description": "production quantity"},
                ],
            }
        ]
    }
    return f"""당신은 제조 데이터 분석 Agent의 Table Catalog를 v2 MongoDB item document로 변환하는 전문가입니다.
반드시 JSON object만 반환하세요. markdown fence나 설명 문장은 반환하지 마세요.

사용자가 자연어, 컬럼 설명, DDL, SQL 일부를 붙여 넣으면 dataset metadata만 추출하세요.
SQL 본문, Oracle TNS, 계정, 비밀번호, 쿼리 템플릿은 반환하지 마세요.

이미 등록된 table catalog 요약:
{_compact_json(_existing_summary(existing_items))}

반환 schema:
{_compact_json(output_schema, 3000)}

작성 규칙:
- dataset_key는 안정적인 snake_case로 만드세요.
- source_type을 모르면 auto, Oracle 조회용이면 oracle을 사용하세요.
- required_params는 사용자가 질문에서 반드시 제공해야 하는 조건입니다. 날짜 조회 데이터는 ["date"]를 우선 사용하세요.
- format_params는 retriever 함수 내부 SQL format slot에 들어갈 파라미터 순서입니다. 모르면 required_params와 동일하게 두세요.
- tool_name은 get_<dataset_key>_data 형태를 우선 사용하세요.
- 컬럼 type은 string, number, date, datetime, boolean 중 하나만 사용하세요.
- 질문 매칭용 keywords와 question_examples를 충분히 작성하세요.

사용자 입력:
{raw_text}
"""


def build_table_preview_from_text(
    raw_text: str,
    llm_api_key: str,
    model_name: str,
    temperature: float,
    existing_items: list[Dict[str, Any]] | None = None,
    llm_func: LLMJsonFn | None = None,
) -> Dict[str, Any]:
    raw_text = str(raw_text or "").strip()
    if not raw_text:
        raise ValueError("테이블 설명을 입력해 주세요.")

    existing_items = existing_items or []
    prompt = build_table_prompt(raw_text, existing_items)
    llm_json = llm_func(prompt) if llm_func is not None else invoke_llm_json(prompt, llm_api_key, model_name, temperature)
    llm_text = str(llm_json.get("_llm_text") or "")
    normalized = normalize_table_input(llm_json)
    for item in normalized["items"]:
        item.setdefault("source_text", raw_text)
    return {
        "raw_text": raw_text,
        "prompt": prompt,
        "llm_json": llm_json,
        "llm_text": llm_text,
        "items": normalized["items"],
        "errors": normalized["errors"],
    }
