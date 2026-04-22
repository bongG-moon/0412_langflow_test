from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any, Dict

from .config import VALID_CALCULATION_MODES, VALID_COLUMN_TYPES, VALID_GBNS, VALID_JOIN_TYPES
from .llm_client import invoke_llm_json


ITEM_SCHEMAS = {
    "products": {
        "gbn": "products",
        "key": "short_unique_product_or_family_key",
        "payload": {
            "display_name": "제품 또는 제품군 이름",
            "aliases": ["동의어"],
            "filters": {"column_name": ["value"]},
        },
    },
    "process_groups": {
        "gbn": "process_groups",
        "key": "short_unique_process_group_key",
        "payload": {
            "display_name": "공정 그룹명",
            "aliases": ["동의어"],
            "processes": ["실제 공정값"],
        },
    },
    "terms": {
        "gbn": "terms",
        "key": "short_unique_term_key",
        "payload": {
            "display_name": "용어명",
            "aliases": ["동의어"],
            "meaning": "의미 설명",
            "filter": {"field": "column_name", "operator": "in|eq|not_null|custom", "values": ["value"]},
        },
    },
    "datasets": {
        "gbn": "datasets",
        "key": "dataset_key",
        "payload": {
            "display_name": "데이터셋 표시명",
            "keywords": ["질문 키워드"],
            "required_params": ["date"],
            "query_template_id": "query template id",
            "tool_name": "query tool name",
            "columns": [{"name": "column_name", "type": "string|number|date|datetime|boolean"}],
        },
    },
    "metrics": {
        "gbn": "metrics",
        "key": "metric_key",
        "payload": {
            "display_name": "지표명",
            "aliases": ["지표 동의어"],
            "required_datasets": ["dataset_key"],
            "required_columns": ["column_name"],
            "source_columns": [{"dataset_key": "dataset_key", "column": "column_name", "role": "numerator"}],
            "calculation_mode": "ratio|difference|sum|mean|count|condition_flag|threshold_flag|custom",
            "formula": "calculation expression",
            "condition": "",
            "output_column": "result column",
            "default_group_by": ["OPER_NAME"],
            "pandas_hint": "pandas 처리 힌트",
        },
    },
    "join_rules": {
        "gbn": "join_rules",
        "key": "base_join_dataset_join",
        "payload": {
            "base_dataset": "dataset_key",
            "join_dataset": "dataset_key",
            "join_type": "left|inner|right|outer",
            "join_keys": ["WORK_DT", "OPER_NAME"],
            "description": "조인 사용 조건",
        },
    },
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string_list(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _norm_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", "", text)


def _slug(value: Any, fallback: str = "domain_item") -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def _clean_note(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned)
    cleaned = re.sub(r"^\s*\d+[\).\-\s]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def split_domain_text(raw_text: str) -> list[Dict[str, str]]:
    normalized = str(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    notes = [_clean_note(line) for line in normalized.split("\n")]
    notes = [line for line in notes if line]
    if len(notes) <= 1:
        pieces = re.split(r"(?<=[.!?。])\s+", normalized)
        notes = [_clean_note(piece) for piece in pieces if _clean_note(piece)]
    return [{"note_id": f"note_{idx}", "raw_text": note} for idx, note in enumerate(notes, start=1)]


def infer_routes(raw_text: str, manual_gbn: str = "auto") -> list[str]:
    if manual_gbn in VALID_GBNS:
        return [manual_gbn]
    text = str(raw_text or "").lower()
    routes: list[str] = []
    if any(token in text for token in ["공정", "oper", "process", "wet", "d/a", "d/p", "pco", "w/b"]):
        routes.append("process_groups")
    if any(token in text for token in ["데이터", "dataset", "table", "테이블", "컬럼", "sql", "필수"]):
        routes.append("datasets")
    if any(token in text for token in ["율", "rate", "ratio", "/", "계산", "목표 대비", "달성"]):
        routes.append("metrics")
    if any(token in text for token in ["join", "조인", "연결", "매핑", "키"]):
        routes.append("join_rules")
    if any(token in text for token in ["제품", "product", "device", "자재", "hbm", "mobile", "pop", "auto"]):
        routes.append("products")
    if any(token in text for token in ["의미", "말함", "동의어", "조건", "구분", "경우", "뜻"]):
        routes.append("terms")
    return list(dict.fromkeys(routes)) or list(VALID_GBNS)


def _compact_json(value: Any, limit: int = 7000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED..."


def _existing_by_route(existing_items: list[Dict[str, Any]], routes: list[str]) -> Dict[str, list[Dict[str, Any]]]:
    grouped: Dict[str, list[Dict[str, Any]]] = {route: [] for route in routes}
    for item in existing_items:
        gbn = str(item.get("gbn") or "")
        if gbn in grouped:
            grouped[gbn].append(
                {
                    "gbn": gbn,
                    "key": item.get("key"),
                    "payload": item.get("payload", {}),
                    "normalized_aliases": item.get("normalized_aliases", []),
                    "normalized_keywords": item.get("normalized_keywords", []),
                }
            )
    return grouped


def build_domain_prompt(
    raw_text: str,
    raw_notes: list[Dict[str, str]],
    routes: list[str],
    existing_items: list[Dict[str, Any]],
) -> str:
    schemas = {route: ITEM_SCHEMAS[route] for route in routes if route in ITEM_SCHEMAS}
    output_schema = {
        "items": [
            {
                "gbn": "one of selected categories",
                "source_note_id": "note id from raw_notes",
                "key": "stable snake_case key",
                "payload": {},
                "warnings": [],
            }
        ],
        "unmapped_text": "",
    }
    return f"""당신은 제조 데이터 분석 Agent에 사용할 도메인 지식을 구조화하는 전문가입니다.
반드시 JSON object만 반환하세요. markdown fence는 쓰지 마세요.

선택된 분류:
{", ".join(routes)}

허용 스키마:
{_compact_json(schemas)}

이미 등록된 항목:
{_compact_json(_existing_by_route(existing_items, routes))}

분리된 원문 note:
{_compact_json(raw_notes)}

반환 스키마:
{_compact_json(output_schema, limit=2000)}

작성 규칙:
- RAW_TEXT에 명시된 사실만 추출하세요.
- 설명문, 로그, 화면 문구를 payload에 넣지 마세요.
- 한 문장에 여러 항목이 있으면 items를 여러 개 반환하세요.
- key는 안정적인 snake_case로 작성하세요.
- 제품/용어 조건은 가능하면 payload.filter 또는 payload.filters에 컬럼/조건을 명시하세요.
- 지표는 required_datasets, source_columns, formula, output_column을 최대한 채우세요.
- dataset은 table/sql보다 질문 의도 매핑에 필요한 keywords, required_params, tool_name, columns 위주로 작성하세요.
- 확실하지 않은 내용은 warnings 또는 unmapped_text에 넣으세요.

RAW_TEXT:
{raw_text}
"""


def _payload(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload")
    return deepcopy(payload) if isinstance(payload, dict) else {}


def _base_key(item: Dict[str, Any], payload: Dict[str, Any], gbn: str) -> str:
    for key in ("key", "name"):
        if str(item.get(key) or "").strip():
            return _slug(item[key], gbn)
    if gbn == "join_rules" and payload.get("base_dataset") and payload.get("join_dataset"):
        return _slug(f"{payload.get('base_dataset')}_{payload.get('join_dataset')}_join", gbn)
    for key in ("display_name", "canonical", "base_dataset"):
        if str(payload.get(key) or "").strip():
            return _slug(payload[key], gbn)
    return gbn.rstrip("s")


def _normalize_payload(gbn: str, payload: Dict[str, Any], warnings: list[str]) -> Dict[str, Any]:
    if gbn == "products":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "filters": payload.get("filters") if isinstance(payload.get("filters"), dict) else {},
        }
    if gbn == "process_groups":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "processes": _string_list(payload.get("processes")),
        }
    if gbn == "terms":
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "meaning": str(payload.get("meaning") or payload.get("description") or "").strip(),
            "filter": payload.get("filter") if isinstance(payload.get("filter"), dict) else {},
        }
    if gbn == "datasets":
        columns = []
        for column in _as_list(payload.get("columns")):
            if not isinstance(column, dict) or not column.get("name"):
                continue
            item = {"name": str(column.get("name")).strip(), "type": str(column.get("type") or "string").strip()}
            if item["type"] not in VALID_COLUMN_TYPES:
                warnings.append(f"Unknown column type '{item['type']}' for column '{item['name']}'.")
                item["type"] = "string"
            columns.append(item)
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "keywords": _string_list(payload.get("keywords")),
            "required_params": _string_list(payload.get("required_params")),
            "query_template_id": str(payload.get("query_template_id") or "").strip(),
            "tool_name": str(payload.get("tool_name") or "").strip(),
            "columns": columns,
        }
    if gbn == "metrics":
        mode = str(payload.get("calculation_mode") or "").strip()
        if mode not in VALID_CALCULATION_MODES:
            warnings.append(f"Unknown calculation_mode '{mode}'.")
            mode = "custom"
        return {
            "display_name": str(payload.get("display_name") or "").strip(),
            "aliases": _string_list(payload.get("aliases")),
            "required_datasets": _string_list(payload.get("required_datasets")),
            "required_columns": _string_list(payload.get("required_columns")),
            "source_columns": [item for item in _as_list(payload.get("source_columns")) if isinstance(item, dict)],
            "calculation_mode": mode,
            "formula": str(payload.get("formula") or "").strip(),
            "condition": str(payload.get("condition") or "").strip(),
            "output_column": str(payload.get("output_column") or "").strip(),
            "default_group_by": _string_list(payload.get("default_group_by")),
            "pandas_hint": str(payload.get("pandas_hint") or "").strip(),
        }
    if gbn == "join_rules":
        join_type = str(payload.get("join_type") or "left").strip().lower()
        if join_type not in VALID_JOIN_TYPES:
            warnings.append(f"Unknown join_type '{join_type}'.")
            join_type = "left"
        return {
            "base_dataset": str(payload.get("base_dataset") or "").strip(),
            "join_dataset": str(payload.get("join_dataset") or "").strip(),
            "join_type": join_type,
            "join_keys": _string_list(payload.get("join_keys") or payload.get("keys")),
            "description": str(payload.get("description") or "").strip(),
        }
    return payload


def _aliases_for(gbn: str, key: str, payload: Dict[str, Any]) -> list[str]:
    aliases = [key]
    if payload.get("display_name"):
        aliases.append(str(payload["display_name"]))
    aliases.extend(_string_list(payload.get("aliases")))
    if gbn == "process_groups":
        aliases.extend(_string_list(payload.get("processes")))
    return list(dict.fromkeys(_norm_token(item) for item in aliases if _norm_token(item)))


def _keywords_for(gbn: str, payload: Dict[str, Any]) -> list[str]:
    if gbn != "datasets":
        return []
    return list(dict.fromkeys(_norm_token(item) for item in _string_list(payload.get("keywords")) if _norm_token(item)))


def normalize_domain_items(
    llm_json: Dict[str, Any],
    raw_text: str,
    raw_notes: list[Dict[str, str]],
) -> Dict[str, Any]:
    note_text_by_id = {str(note.get("note_id")): str(note.get("raw_text") or "") for note in raw_notes}
    candidates = llm_json.get("items") if isinstance(llm_json.get("items"), list) else []
    normalized: list[Dict[str, Any]] = []
    errors: list[str] = []

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        gbn = str(candidate.get("gbn") or "").strip()
        if gbn not in VALID_GBNS:
            errors.append(f"Unsupported gbn '{gbn}' skipped.")
            continue
        warnings = [str(item) for item in _as_list(candidate.get("warnings")) if str(item).strip()]
        payload = _normalize_payload(gbn, _payload(candidate), warnings)
        key = _base_key(candidate, payload, gbn)
        source_note_id = str(candidate.get("source_note_id") or "").strip()
        source_text = note_text_by_id.get(source_note_id) or str(raw_text or "").strip()
        normalized.append(
            {
                "gbn": gbn,
                "key": key,
                "status": "active",
                "payload": payload,
                "normalized_aliases": _aliases_for(gbn, key, payload),
                "normalized_keywords": _keywords_for(gbn, payload),
                "source_note_id": source_note_id,
                "source_text": source_text,
                "warnings": warnings,
            }
        )

    if not normalized and not errors:
        errors.append("No valid domain items were extracted.")
    return {
        "normalized_domain_items": normalized,
        "normalization_errors": errors,
        "unmapped_text": llm_json.get("unmapped_text", ""),
        "llm_text": llm_json.get("_llm_text", ""),
    }


def build_domain_preview(
    raw_text: str,
    api_key: str,
    model_name: str,
    temperature: float,
    existing_items: list[Dict[str, Any]],
    manual_gbn: str = "auto",
) -> Dict[str, Any]:
    raw_notes = split_domain_text(raw_text)
    routes = infer_routes(raw_text, manual_gbn)
    prompt = build_domain_prompt(raw_text, raw_notes, routes, existing_items)
    llm_json = invoke_llm_json(prompt, api_key, model_name, temperature)
    normalized = normalize_domain_items(llm_json, raw_text, raw_notes)
    return {
        "raw_text": raw_text,
        "raw_notes": raw_notes,
        "routes": routes,
        "prompt": prompt,
        **normalized,
    }
