from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, Dict


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


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _normalize_triple_quoted_json(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return json.dumps(match.group(2))

    return re.sub(r'("""|\'\'\')(.*?)(\1)', replace, str(text or ""), flags=re.DOTALL)


def _strip_code_fence(text: str) -> str:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json|JSON)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _parse_jsonish(value: Any) -> tuple[Any, list[str]]:
    if value is None:
        return {}, []
    if isinstance(value, (dict, list)):
        return deepcopy(value), []
    text = _strip_code_fence(str(value or ""))
    if not text:
        return {}, []
    errors: list[str] = []
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text), []
        except Exception as exc:
            errors.append(str(exc))
    normalized = _normalize_triple_quoted_json(text)
    if normalized != text:
        for parser in (json.loads, ast.literal_eval):
            try:
                return parser(normalized), []
            except Exception as exc:
                errors.append(str(exc))
    return {}, errors


def _extract_json_object(text: str) -> Dict[str, Any]:
    parsed, errors = _parse_jsonish(text)
    if isinstance(parsed, dict) and parsed:
        return parsed
    match = re.search(r"\{.*\}", str(text or ""), flags=re.DOTALL)
    if match:
        parsed, errors = _parse_jsonish(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    return {"_parse_errors": errors}


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return deepcopy(data)
    text = getattr(value, "text", None) or getattr(value, "content", None)
    if isinstance(text, str):
        parsed, _errors = _parse_jsonish(text)
        return parsed if isinstance(parsed, dict) else {"text": text}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _runtime_today(reference_date: str = "") -> datetime:
    if reference_date:
        for fmt in ("%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(reference_date, fmt)
            except Exception:
                pass
    try:
        zoneinfo = import_module("zoneinfo")
        return datetime.now(zoneinfo.ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
    except Exception:
        return datetime.now()


def _extract_date(question: str, reference_date: str = "") -> str | None:
    base = _runtime_today(reference_date)
    lowered = str(question or "").lower()
    if any(token in lowered for token in ("today", "금일", "오늘")):
        return base.strftime("%Y%m%d")
    if any(token in lowered for token in ("yesterday", "어제", "전일")):
        return (base - timedelta(days=1)).strftime("%Y%m%d")
    match = re.search(r"\b(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?([0-2]\d|3[01])\b", str(question or ""))
    if match:
        return f"{match.group(1)}{match.group(2)}{match.group(3)}"
    return None


def _dataset_configs(table_catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    return {str(key): value for key, value in datasets.items() if isinstance(value, dict)}


def _contains_any(question: str, tokens: list[str]) -> bool:
    lowered = str(question or "").lower()
    return any(str(token).lower() in lowered for token in tokens)


def _dataset_hints(question: str, table_catalog: Dict[str, Any], domain: Dict[str, Any]) -> list[str]:
    normalized_question = _normalize_text(question)
    found: list[str] = []
    for dataset_key, dataset in _dataset_configs(table_catalog).items():
        candidates = [
            dataset_key,
            dataset.get("display_name", ""),
            dataset.get("description", ""),
            *_as_list(dataset.get("keywords")),
            *_as_list(dataset.get("aliases")),
            *_as_list(dataset.get("question_examples")),
        ]
        if any(_normalize_text(item) and _normalize_text(item) in normalized_question for item in candidates):
            found.append(dataset_key)

    metrics = domain.get("metrics") if isinstance(domain.get("metrics"), dict) else {}
    for metric_key, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        aliases = [metric_key, metric.get("display_name", ""), *_as_list(metric.get("aliases"))]
        if any(_normalize_text(item) and _normalize_text(item) in normalized_question for item in aliases):
            found.extend(str(item) for item in _as_list(metric.get("required_datasets")))

    if _contains_any(question, ["achievement", "achievement rate", "target 대비", "목표 대비", "달성률"]):
        found.extend(["production", "target"])
    return _unique_strings(found)


def _filters_from_question(question: str, domain: Dict[str, Any] | None = None) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    process_matches = re.findall(r"\b(?:D/A|DA|W/B|WB)\s*-?\s*\d+\b", question, flags=re.IGNORECASE)
    normalized_processes: list[str] = []
    for item in process_matches:
        text = re.sub(r"\s+", "", item.upper())
        if text.startswith("DA"):
            text = text.replace("DA", "D/A", 1)
        if text.startswith("WB"):
            text = text.replace("WB", "W/B", 1)
        normalized_processes.append(text)
    if normalized_processes:
        filters["process_name"] = _unique_strings(normalized_processes)
    elif _contains_any(question, ["DA공정", "D/A공정", "DA process"]):
        filters["process_name"] = ["D/A1", "D/A2", "D/A3"]
    elif _contains_any(question, ["WB공정", "W/B공정", "WB process"]):
        filters["process_name"] = ["W/B1", "W/B2"]

    groups = (domain or {}).get("process_groups") if isinstance((domain or {}).get("process_groups"), dict) else {}
    for _group_key, group in groups.items():
        if not isinstance(group, dict):
            continue
        aliases = [group.get("display_name", ""), *_as_list(group.get("aliases"))]
        if any(_normalize_text(item) and _normalize_text(item) in _normalize_text(question) for item in aliases):
            processes = [str(item) for item in _as_list(group.get("processes")) if str(item).strip()]
            if processes and not filters.get("process_name"):
                filters["process_name"] = processes

    modes = [token for token in ("DDR5", "LPDDR5", "HBM3", "HBM") if token.lower() in question.lower()]
    if modes:
        filters["mode"] = _unique_strings(modes)
    return filters


def _group_by_from_question(question: str) -> list[str]:
    mapping = {
        "MODE": ["mode별", "모드별", "by mode", "group by mode"],
        "OPER_NAME": ["공정별", "process별", "by process", "group by process"],
        "LINE": ["라인별", "line별", "by line", "group by line"],
        "MCP_NO": ["제품별", "mcp별", "product별", "by product", "group by product"],
    }
    lowered = question.lower()
    return _unique_strings([column for column, tokens in mapping.items() if any(token.lower() in lowered for token in tokens)])


def _required_params(question: str, state: Dict[str, Any], reference_date: str = "") -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    date = _extract_date(question, reference_date)
    if date:
        params["date"] = date
    else:
        context = state.get("context") if isinstance(state.get("context"), dict) else {}
        last_params = context.get("last_extracted_params") if isinstance(context.get("last_extracted_params"), dict) else {}
        if last_params.get("date"):
            params["date"] = last_params["date"]

    lot_match = re.search(r"\bLOT[-_A-Z0-9]+\b", str(question or ""), flags=re.IGNORECASE)
    if lot_match:
        params["lot_id"] = lot_match.group(0)
    return params


def _has_current_data(state: Dict[str, Any]) -> bool:
    current = state.get("current_data")
    return isinstance(current, dict) and isinstance(current.get("data"), list) and bool(current.get("data"))


def _build_job(dataset_key: str, dataset: Dict[str, Any], params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dataset_key": dataset_key,
        "dataset_label": dataset.get("display_name", dataset_key),
        "tool_name": dataset.get("tool_name", f"get_{dataset_key}_data"),
        "db_key": dataset.get("db_key", "PKG_RPT"),
        "source_type": dataset.get("source_type", "auto"),
        "required_params": [str(item) for item in _as_list(dataset.get("required_params"))],
        "params": deepcopy(params),
        "filters": deepcopy(filters),
    }


def _normalize_param_values(params: Dict[str, Any]) -> Dict[str, Any]:
    normalized = deepcopy(params)
    if normalized.get("date"):
        digits = "".join(ch for ch in str(normalized["date"]) if ch.isdigit())
        normalized["date"] = digits[:8] or normalized["date"]
    return normalized


def _normalize_plan(raw_plan: Dict[str, Any], question: str, state: Dict[str, Any], table_catalog: Dict[str, Any], domain: Dict[str, Any], reference_date: str = "") -> Dict[str, Any]:
    configs = _dataset_configs(table_catalog)
    needed_datasets = _unique_strings([*_as_list(raw_plan.get("needed_datasets")), *_as_list(raw_plan.get("dataset_keys")), *_as_list(raw_plan.get("datasets"))])
    if not needed_datasets:
        needed_datasets = _dataset_hints(question, table_catalog, domain)
    needed_datasets = [key for key in needed_datasets if key in configs]

    raw_filters = raw_plan.get("filters") if isinstance(raw_plan.get("filters"), dict) else {}
    filters = {**_filters_from_question(question, domain), **raw_filters}

    raw_params: Dict[str, Any] = {}
    if isinstance(raw_plan.get("required_params"), dict):
        raw_params.update(raw_plan["required_params"])
    if isinstance(raw_plan.get("params"), dict):
        raw_params.update(raw_plan["params"])
    params = _normalize_param_values({**_required_params(question, state, reference_date), **raw_params})

    explicit_fresh = _contains_any(question, ["새로", "다시 조회", "신규", "fresh", "reload", "new data"])
    followup_like = _contains_any(question, ["그 결과", "이 결과", "현재 결과", "그중", "여기서", "방금", "앞 결과", "that result", "current result"])
    query_mode = str(raw_plan.get("query_mode") or "").strip()
    if query_mode not in {"retrieval", "followup_transform", "finish", "clarification"}:
        query_mode = "followup_transform" if _has_current_data(state) and followup_like and not explicit_fresh and not needed_datasets else "retrieval"
    if query_mode == "followup_transform" and not _has_current_data(state):
        query_mode = "retrieval"

    group_by = _unique_strings([*_as_list(raw_plan.get("group_by")), *_group_by_from_question(question)])
    needs_pandas = bool(raw_plan.get("needs_pandas") or raw_plan.get("needs_post_processing") or group_by)
    if _contains_any(question, ["별", "기준", "top", "상위", "하위", "정렬", "비교", "달성률", "비율", "rate", "ratio", "group", "by"]) or query_mode == "followup_transform" or len(needed_datasets) > 1:
        needs_pandas = True

    jobs = []
    missing: list[Dict[str, str]] = []
    if query_mode == "retrieval":
        for dataset_key in needed_datasets:
            job = _build_job(dataset_key, configs.get(dataset_key, {}), params, filters)
            for required in job["required_params"]:
                if params.get(required) in (None, "", []):
                    missing.append({"dataset_key": dataset_key, "param": required})
            jobs.append(job)

    if query_mode == "retrieval" and not needed_datasets:
        return {
            "request_type": "clarification",
            "query_mode": "finish",
            "route": "finish",
            "needed_datasets": [],
            "retrieval_jobs": [],
            "required_params": params,
            "filters": filters,
            "group_by": group_by,
            "needs_pandas": False,
            "analysis_goal": raw_plan.get("analysis_goal") or question,
            "response": "질문에 맞는 조회 데이터셋을 찾지 못했습니다. 생산, 목표, WIP처럼 조회할 데이터를 조금 더 구체적으로 적어주세요.",
            "failure_type": "unknown_dataset",
        }
    if missing:
        labels = ", ".join(f"{item['dataset_key']}.{item['param']}" for item in missing)
        return {
            "request_type": "clarification",
            "query_mode": "finish",
            "route": "finish",
            "needed_datasets": needed_datasets,
            "retrieval_jobs": jobs,
            "required_params": params,
            "filters": filters,
            "group_by": group_by,
            "needs_pandas": False,
            "analysis_goal": raw_plan.get("analysis_goal") or question,
            "response": f"데이터 조회에 필요한 필수 조건이 부족합니다: {labels}",
            "failure_type": "missing_required_params",
            "missing_required_params": missing,
        }

    route = "followup_transform" if query_mode == "followup_transform" else ("multi_retrieval" if len(jobs) > 1 else "single_retrieval")
    return {
        "request_type": str(raw_plan.get("request_type") or "data_question"),
        "query_mode": query_mode,
        "route": route,
        "needed_datasets": needed_datasets,
        "retrieval_jobs": jobs,
        "required_params": params,
        "filters": filters,
        "group_by": group_by,
        "sort": raw_plan.get("sort"),
        "top_n": raw_plan.get("top_n"),
        "needs_pandas": needs_pandas,
        "analysis_goal": str(raw_plan.get("analysis_goal") or question),
        "reason": str(raw_plan.get("reason") or ""),
    }


def normalize_intent_plan(llm_result_value: Any, reference_date_value: Any = "") -> Dict[str, Any]:
    payload = _payload_from_value(llm_result_value)
    llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
    prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
    state = prompt_payload.get("state") if isinstance(prompt_payload.get("state"), dict) else {}
    domain = prompt_payload.get("domain") if isinstance(prompt_payload.get("domain"), dict) else {}
    table_catalog = prompt_payload.get("table_catalog") if isinstance(prompt_payload.get("table_catalog"), dict) else {}
    question = str(prompt_payload.get("user_question") or state.get("pending_user_question") or "").strip()
    reference_date = str(reference_date_value or prompt_payload.get("reference_date") or "").strip()

    warnings = [str(item) for item in _as_list(llm_result.get("errors")) if str(item).strip()]
    raw_plan = _extract_json_object(str(llm_result.get("llm_text") or ""))
    if not raw_plan or raw_plan.get("_parse_errors"):
        if raw_plan.get("_parse_errors"):
            warnings.extend(str(item) for item in _as_list(raw_plan.get("_parse_errors")) if str(item).strip())
        raw_plan = {
            "needed_datasets": _dataset_hints(question, table_catalog, domain),
            "required_params": _required_params(question, state, reference_date),
            "filters": _filters_from_question(question, domain),
            "group_by": _group_by_from_question(question),
            "analysis_goal": question,
        }
        source = "heuristic_fallback"
    else:
        source = "llm"

    plan = _normalize_plan(raw_plan, question, state, table_catalog, domain, reference_date)
    plan["planner_source"] = source
    if warnings:
        plan["planner_warnings"] = _unique_strings(warnings)
    return {
        "intent_plan": plan,
        "retrieval_jobs": plan.get("retrieval_jobs", []),
        "state": state,
        "domain": domain,
        "table_catalog": table_catalog,
        "user_question": question,
    }


class NormalizeIntentPlan(Component):
    display_name = "V2 Normalize Intent Plan"
    description = "Parse and normalize the LLM intent JSON into retrieval jobs and routing fields."
    icon = "ListChecks"
    name = "V2NormalizeIntentPlan"

    inputs = [
        DataInput(name="llm_result", display_name="LLM Result", info="Output from V2 LLM JSON Caller.", input_types=["Data", "JSON"]),
        MessageTextInput(name="reference_date", display_name="Reference Date Override", value="", advanced=True),
    ]
    outputs = [Output(name="intent_plan", display_name="Intent Plan", method="build_plan", types=["Data"])]

    def build_plan(self):
        payload = normalize_intent_plan(getattr(self, "llm_result", None), getattr(self, "reference_date", ""))
        plan = payload.get("intent_plan", {})
        self.status = {
            "route": plan.get("route"),
            "query_mode": plan.get("query_mode"),
            "datasets": plan.get("needed_datasets", []),
            "planner_source": plan.get("planner_source"),
        }
        return _make_data(payload)
