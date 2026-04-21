from __future__ import annotations

import json
import re
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
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


VALID_GBNS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
ROUTE_KEYWORDS = {
    "products": ["제품", "product", "pkg", "package", "hbm", "auto", "전장"],
    "process_groups": ["공정", "공정군", "process", "라인"],
    "terms": ["용어", "뜻", "조건", "필터", "filter", "term", "means"],
    "datasets": ["데이터셋", "dataset", "table", "테이블", "컬럼", "column", "query", "조회", "필수", "parameter"],
    "metrics": ["계산", "수식", "비율", "율", "rate", "ratio", "metric", "kpi", "/", "달성", "포화"],
    "join_rules": ["join", "조인", "결합", "merge", "키", "key", "기준으로", "연결"],
}


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    text = getattr(value, "text", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"raw_text": text}
        except Exception:
            return {"raw_text": text}
    return {}


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _parse_route_override(value: Any) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    if raw.lower() == "auto":
        return []
    parts = re.split(r"[,/| ]+", raw)
    return [part for part in parts if part in VALID_GBNS or part == "mixed"]


def route_domain_item(raw_payload: Any, route_override: Any = None) -> Dict[str, Any]:
    payload = _payload_from_value(raw_payload)
    raw_notes = payload.get("raw_notes") if isinstance(payload.get("raw_notes"), list) else []
    raw_text = str(payload.get("combined_raw_text") or payload.get("raw_text") or payload.get("text") or "").strip()
    normalized = _normalize_text(raw_text)
    override_routes = _parse_route_override(route_override)
    scores: Dict[str, int] = {}
    for gbn, keywords in ROUTE_KEYWORDS.items():
        scores[gbn] = sum(1 for keyword in keywords if _normalize_text(keyword) in normalized)

    routes = override_routes or [gbn for gbn, score in scores.items() if score > 0]
    if not routes:
        routes = ["mixed"]
    routes = _dedupe(routes)
    primary_gbn = routes[0] if len(routes) == 1 else "mixed"
    confidence = 0.45
    if override_routes:
        confidence = 1.0
    elif routes != ["mixed"]:
        top_score = max(scores.get(route, 0) for route in routes)
        confidence = min(0.95, 0.55 + 0.1 * top_score)

    return {
        "raw_text": raw_text,
        "raw_notes": raw_notes,
        "note_count": len(raw_notes),
        "routes": routes,
        "primary_gbn": primary_gbn,
        "route_scores": scores,
        "confidence": confidence,
        "router": "rule_based_domain_item_router",
        "route_note": "Use Langflow Smart Router here if you want model-based branch routing; this node is a deterministic fallback.",
    }


class DomainItemRouter(Component):
    display_name = "Domain Item Router"
    description = "Classify one raw domain note into item categories. Can be replaced by Langflow Smart Router."
    icon = "Route"
    name = "DomainItemRouter"

    inputs = [
        DataInput(
            name="raw_domain_payload",
            display_name="Raw Domain Payload",
            info="Output from Raw Domain Text Input.",
            input_types=["Data", "JSON"],
        ),
        MessageTextInput(
            name="route_override",
            display_name="Route Override",
            info="Optional: products, process_groups, terms, datasets, metrics, join_rules, mixed, or auto.",
            value="auto",
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="route_payload", display_name="Route Payload", method="build_route", types=["Data"]),
    ]

    def build_route(self) -> Data:
        return _make_data(route_domain_item(getattr(self, "raw_domain_payload", None), getattr(self, "route_override", "")))
