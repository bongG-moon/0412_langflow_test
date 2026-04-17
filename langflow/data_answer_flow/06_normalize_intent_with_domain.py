from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, Dict

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


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
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text


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


def _make_data(payload: Dict[str, Any], text: str | None = None) -> Any:
    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload, text=text)


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
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _unique(values: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for value in values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _contains_alias(question: str, alias: str) -> bool:
    alias = str(alias or "").strip()
    if not alias:
        return False
    if re.fullmatch(r"[A-Za-z0-9_]+", alias):
        return re.search(rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])", question, re.I) is not None
    return alias.lower() in question.lower()


def _today(reference_date: str = "") -> datetime:
    if reference_date:
        try:
            return datetime.strptime(reference_date, "%Y-%m-%d")
        except Exception:
            pass
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
    return datetime.now()


def _extract_date(question: str, reference_date: str = "") -> tuple[str | None, str | None]:
    base = _today(reference_date)
    lowered = question.lower()
    if any(token in question for token in ("오늘", "금일")) or "today" in lowered:
        return base.strftime("%Y-%m-%d"), "explicit"
    if any(token in question for token in ("어제", "전일")) or "yesterday" in lowered:
        return (base - timedelta(days=1)).strftime("%Y-%m-%d"), "explicit"
    match = re.search(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?([0-2]\d|3[01])", question)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}", "explicit"
    return None, None


def _get_intent(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    intent = payload.get("intent_raw")
    if isinstance(intent, dict):
        return dict(intent)
    if isinstance(payload, dict):
        return dict(payload)
    return {}


def _get_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else payload


def _get_index(domain_payload: Any, index_payload: Any) -> Dict[str, Any]:
    payload = _payload_from_value(index_payload)
    index = payload.get("domain_index")
    if isinstance(index, dict):
        return index
    domain_payload_dict = _payload_from_value(domain_payload)
    index = domain_payload_dict.get("domain_index")
    return index if isinstance(index, dict) else {}


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload


def normalize_intent_with_domain(
    intent_raw: Any,
    domain_payload: Any,
    domain_index_payload: Any,
    agent_state_payload: Any,
    user_question: str,
    reference_date: str = "",
) -> Dict[str, Any]:
    intent = _get_intent(intent_raw)
    domain = _get_domain(domain_payload)
    domain_index = _get_index(domain_payload, domain_index_payload)
    agent_state = _get_state(agent_state_payload)
    question = str(user_question or agent_state.get("pending_user_question") or "")
    notes: list[str] = []

    intent.setdefault("request_type", "unknown")
    intent.setdefault("dataset_hints", [])
    intent.setdefault("metric_hints", [])
    intent.setdefault("required_params", {})
    intent.setdefault("filters", {})
    intent.setdefault("group_by", [])
    intent.setdefault("calculation_hints", [])
    intent.setdefault("followup_cues", [])
    if not isinstance(intent["required_params"], dict):
        intent["required_params"] = {}
    if not isinstance(intent["filters"], dict):
        intent["filters"] = {}

    date_value, date_source = _extract_date(question, reference_date)
    if date_value:
        intent["required_params"]["date"] = date_value
        intent["date_source"] = date_source

    for alias_norm, product_key in domain_index.get("product_alias_to_key", {}).items():
        if _contains_alias(question, alias_norm):
            product = domain.get("products", {}).get(product_key, {})
            filters = product.get("filters") if isinstance(product, dict) else None
            if isinstance(filters, dict):
                intent["filters"].update(filters)
            else:
                intent["filters"]["product"] = product_key
            notes.append(f"product alias '{alias_norm}' -> {product_key}")

    for alias_norm, group_key in domain_index.get("process_alias_to_group", {}).items():
        if _contains_alias(question, alias_norm):
            group = domain.get("process_groups", {}).get(group_key, {})
            processes = group.get("processes") if isinstance(group, dict) else None
            if processes:
                intent["filters"]["process"] = list(processes)
            else:
                intent["filters"]["process"] = [group_key]
            notes.append(f"process alias '{alias_norm}' -> {group_key}")

    filter_expressions = list(intent.get("filter_expressions") or [])
    for alias_norm, term_key in domain_index.get("term_alias_to_key", {}).items():
        if _contains_alias(question, alias_norm):
            term = domain.get("terms", {}).get(term_key, {})
            filter_expr = term.get("filter") if isinstance(term, dict) else None
            if isinstance(filter_expr, dict):
                enriched = dict(filter_expr)
                enriched["term_key"] = term_key
                filter_expressions.append(enriched)
                notes.append(f"term alias '{alias_norm}' -> {term_key}")
    if filter_expressions:
        intent["filter_expressions"] = _unique(filter_expressions)

    dataset_hints = list(intent.get("dataset_hints") or [])
    for keyword_norm, dataset_key in domain_index.get("dataset_keyword_to_key", {}).items():
        if _contains_alias(question, keyword_norm):
            dataset_hints.append(dataset_key)
    intent["dataset_hints"] = _unique([str(item) for item in dataset_hints if str(item).strip()])

    metric_hints = list(intent.get("metric_hints") or [])
    for alias_norm, metric_key in domain_index.get("metric_alias_to_key", {}).items():
        if _contains_alias(question, alias_norm):
            metric_hints.append(metric_key)
    intent["metric_hints"] = _unique([str(item) for item in metric_hints if str(item).strip()])

    required_datasets: list[str] = []
    for dataset_key in intent["dataset_hints"]:
        if dataset_key in domain.get("datasets", {}):
            required_datasets.append(dataset_key)
    for metric_key in intent["metric_hints"]:
        metric = domain.get("metrics", {}).get(metric_key, {})
        if isinstance(metric, dict):
            required_datasets.extend([str(item) for item in _as_list(metric.get("required_datasets"))])
    intent["required_datasets"] = _unique([item for item in required_datasets if item])

    followup_tokens = ["이때", "그중", "위 결과", "현재 결과", "top", "상위", "하위", "공정별", "제품별", "라인별"]
    cues = list(intent.get("followup_cues") or [])
    for token in followup_tokens:
        if token.lower() in question.lower():
            cues.append(token)
    intent["followup_cues"] = _unique([str(item) for item in cues if str(item).strip()])

    if intent.get("request_type") == "unknown":
        if intent["dataset_hints"] or intent["metric_hints"] or intent["filters"] or intent.get("group_by"):
            intent["request_type"] = "data_question"
        elif any(word in question for word in ("실행", "프로세스", "process", "workflow", "end-to-end")):
            intent["request_type"] = "process_execution"

    intent["raw_terms"] = _unique(intent.get("raw_terms", []) + notes)
    intent["normalization_notes"] = notes
    return {"intent": intent}


class NormalizeIntentWithDomain(Component):
    display_name = "Normalize Intent With Domain"
    description = "Normalize intent fields with domain aliases, date expressions, metrics, and dataset hints."
    icon = "WandSparkles"
    name = "NormalizeIntentWithDomain"

    inputs = [
        DataInput(name="intent_raw", display_name="Intent Raw", info="Output from Parse Intent JSON.", input_types=["Data"]),
        DataInput(
            name="domain_payload",
            display_name="Domain Payload",
            info="Domain Payload output from Domain JSON Loader.",
            input_types=["Data"],
        ),
        DataInput(
            name="domain_index",
            display_name="Domain Index",
            info="Optional Domain Index output from Domain JSON Loader.",
            input_types=["Data"],
        ),
        DataInput(name="agent_state", display_name="Agent State", info="Output from Session State Loader.", input_types=["Data"]),
        MessageTextInput(name="user_question", display_name="User Question", info="Current user question."),
        MessageTextInput(
            name="reference_date",
            display_name="Reference Date",
            value="",
            info="Optional YYYY-MM-DD date used for today/yesterday resolution.",
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="intent", display_name="Intent", method="build_intent", types=["Data"]),
    ]

    def build_intent(self) -> Any:
        payload = normalize_intent_with_domain(
            getattr(self, "intent_raw", None),
            getattr(self, "domain_payload", None) or getattr(self, "domain", None),
            getattr(self, "domain_index", None),
            getattr(self, "agent_state", None),
            getattr(self, "user_question", ""),
            getattr(self, "reference_date", ""),
        )
        return _make_data(payload, text=json.dumps(payload["intent"], ensure_ascii=False))
