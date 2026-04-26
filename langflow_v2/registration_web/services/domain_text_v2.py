from __future__ import annotations

import json
from typing import Any, Callable, Dict

from .config import VALID_GBNS
from .domain_v2 import normalize_domain_input
from .llm_client import invoke_llm_json


LLMJsonFn = Callable[[str], Dict[str, Any]]


DOMAIN_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "products": {
        "gbn": "products",
        "key": "product_or_family_key",
        "payload": {
            "display_name": "display name",
            "aliases": ["user words"],
            "filters": {"column_name": ["value"]},
        },
    },
    "process_groups": {
        "gbn": "process_groups",
        "key": "process_group_key",
        "payload": {
            "display_name": "display name",
            "aliases": ["user words"],
            "processes": ["actual process values"],
        },
    },
    "terms": {
        "gbn": "terms",
        "key": "term_key",
        "payload": {
            "display_name": "display name",
            "aliases": ["user words"],
            "meaning": "meaning for the analyst",
            "filter": {"field": "column_name", "operator": "in|eq|not_null|custom", "values": ["value"]},
            "column_candidates": ["MODE", "OPER_NAME"],
        },
    },
    "datasets": {
        "gbn": "datasets",
        "key": "dataset_key",
        "payload": {
            "display_name": "display name",
            "aliases": ["user words"],
            "keywords": ["question keywords"],
            "primary_quantity_column": "quantity_column",
            "default_group_by": ["MODE", "OPER_NAME"],
            "required_params": ["date"],
            "tool_name": "get_dataset_key_data",
        },
    },
    "metrics": {
        "gbn": "metrics",
        "key": "metric_key",
        "payload": {
            "display_name": "display name",
            "aliases": ["user words"],
            "required_datasets": ["dataset_key"],
            "formula": "sum(numerator) / sum(denominator) * 100",
            "output_column": "metric_output_column",
            "source_columns": ["numerator", "denominator"],
            "grouping_hint": ["MODE", "OPER_NAME"],
            "pandas_hint": "optional pandas guidance",
        },
    },
    "join_rules": {
        "gbn": "join_rules",
        "key": "left_right_join",
        "payload": {
            "left_dataset": "dataset_key",
            "right_dataset": "dataset_key",
            "keys": ["WORK_DT", "OPER_NAME"],
            "join_type": "inner|left|right|outer",
            "description": "when to join these datasets",
        },
    },
}


def _compact_json(value: Any, limit: int = 7000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED..."


def _existing_summary(existing_items: list[Dict[str, Any]], routes: list[str]) -> list[Dict[str, Any]]:
    summary: list[Dict[str, Any]] = []
    route_set = set(routes)
    for item in existing_items:
        gbn = str(item.get("gbn") or "")
        if gbn not in route_set:
            continue
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        summary.append(
            {
                "gbn": gbn,
                "key": item.get("key", ""),
                "display_name": payload.get("display_name", ""),
                "aliases": payload.get("aliases", []),
                "keywords": payload.get("keywords", []),
                "required_datasets": payload.get("required_datasets", []),
                "tool_name": payload.get("tool_name", ""),
            }
        )
    return summary[:80]


def infer_domain_routes(raw_text: str) -> list[str]:
    text = str(raw_text or "").lower()
    routes: list[str] = []
    if any(token in text for token in ("공정", "oper", "process", "d/a", "da", "w/b", "wb", "wet", "pco")):
        routes.append("process_groups")
    if any(token in text for token in ("데이터", "dataset", "table", "테이블", "조회", "생산", "재공", "목표", "capa")):
        routes.append("datasets")
    if any(token in text for token in ("률", "율", "rate", "ratio", "/", "%", "대비", "계산", "달성", "효율")):
        routes.append("metrics")
    if any(token in text for token in ("join", "조인", "합쳐", "매핑", "연결")):
        routes.append("join_rules")
    if any(token in text for token in ("제품", "product", "pkg", "mode", "hbm", "ddr", "mcp")):
        routes.append("products")
    if any(token in text for token in ("의미", "뜻", "조건", "필터", "일 때", "말한다", "alias", "동의어")):
        routes.append("terms")

    if "metrics" in routes and "datasets" not in routes:
        routes.append("datasets")
    return list(dict.fromkeys(routes)) or list(VALID_GBNS)


def build_domain_prompt(raw_text: str, existing_items: list[Dict[str, Any]]) -> str:
    routes = infer_domain_routes(raw_text)
    schemas = {route: DOMAIN_SCHEMAS[route] for route in routes if route in DOMAIN_SCHEMAS}
    output_schema = {
        "items": [
            {
                "gbn": "one of products/process_groups/terms/datasets/metrics/join_rules",
                "key": "stable snake_case key",
                "status": "active",
                "payload": {},
                "warnings": [],
            }
        ],
        "unmapped_text": "",
    }
    return f"""당신은 제조 데이터 분석 Agent의 도메인 지식을 v2 MongoDB item document로 변환하는 전문가입니다.
반드시 JSON object만 반환하세요. markdown fence나 설명 문장은 반환하지 마세요.

사용자가 자연어로 적은 내용을 읽고 필요한 domain item을 자동 분류해 생성하세요.

가능성이 높은 분류:
{", ".join(routes)}

v2 item schema:
{_compact_json(schemas)}

이미 등록된 item 요약:
{_compact_json(_existing_summary(existing_items, routes))}

반환 schema:
{_compact_json(output_schema, 2200)}

작성 규칙:
- MongoDB 저장 단위는 반드시 {{gbn, key, status, payload}} item document입니다.
- 사용자가 분류명을 직접 쓰지 않아도 문맥으로 products/process_groups/terms/datasets/metrics/join_rules 중 하나 이상을 고르세요.
- metric은 모든 계산 항을 required_datasets와 source_columns에 반영하세요. 예: "생산달성율 = 생산량 / 재공"이면 production만 쓰지 말고 production과 wip 또는 target 같은 분모 dataset도 넣으세요.
- "달성율"과 "달성률"처럼 흔한 표기 차이는 aliases에 함께 넣으세요.
- "mode별", "공정별" 같은 표현은 grouping_hint에 넣으세요. mode는 MODE, 공정은 OPER_NAME을 우선 사용하세요.
- dataset item에는 질문 매칭에 필요한 keywords, required_params, tool_name, primary_quantity_column을 채우세요.
- SQL, Oracle TNS, DB 접속 정보는 domain item에 넣지 마세요.
- 모호한 내용은 warnings에 짧게 남기고, 확실한 내용만 구조화하세요.

사용자 입력:
{raw_text}
"""


def build_domain_preview_from_text(
    raw_text: str,
    llm_api_key: str,
    model_name: str,
    temperature: float,
    existing_items: list[Dict[str, Any]] | None = None,
    llm_func: LLMJsonFn | None = None,
) -> Dict[str, Any]:
    raw_text = str(raw_text or "").strip()
    if not raw_text:
        raise ValueError("도메인 설명을 입력해 주세요.")

    existing_items = existing_items or []
    prompt = build_domain_prompt(raw_text, existing_items)
    llm_json = llm_func(prompt) if llm_func is not None else invoke_llm_json(prompt, llm_api_key, model_name, temperature)
    llm_text = str(llm_json.get("_llm_text") or "")
    normalized = normalize_domain_input(llm_json)
    candidates = [item for item in llm_json.get("items", []) if isinstance(item, dict)] if isinstance(llm_json, dict) else []

    for item, candidate in zip(normalized["items"], candidates):
        warnings = candidate.get("warnings") if isinstance(candidate.get("warnings"), list) else []
        item["warnings"] = [str(warning) for warning in warnings if str(warning).strip()]
        if candidate.get("source_note_id"):
            item["source_note_id"] = str(candidate.get("source_note_id"))
        if not item.get("source_text"):
            item["source_text"] = raw_text

    return {
        "raw_text": raw_text,
        "routes": infer_domain_routes(raw_text),
        "prompt": prompt,
        "llm_json": llm_json,
        "llm_text": llm_text,
        "items": normalized["items"],
        "errors": normalized["errors"],
        "unmapped_text": llm_json.get("unmapped_text", "") if isinstance(llm_json, dict) else "",
    }
