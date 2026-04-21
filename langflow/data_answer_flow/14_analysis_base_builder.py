from __future__ import annotations

import json
from copy import deepcopy
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
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


PREFERRED_JOIN_COLUMNS = [
    "WORK_DT",
    "OPER_NAME",
    "OPER_NUM",
    "MODE",
    "DEN",
    "TECH",
    "MCP_NO",
    "PKG_TYPE1",
    "PKG_TYPE2",
    "TSV_DIE_TYP",
    "LINE",
    "라인",
]


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
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _main_context_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    main_context = payload.get("main_context")
    return main_context if isinstance(main_context, dict) else {}


def _get_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else payload


def _get_state(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    state = payload.get("agent_state") or payload.get("state")
    return state if isinstance(state, dict) else payload


def _as_source_results(retrieval_payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    result = retrieval_payload.get("retrieval_result")
    if isinstance(result, dict) and isinstance(result.get("source_results"), list):
        return [item for item in result["source_results"] if isinstance(item, dict)]
    if isinstance(retrieval_payload.get("source_results"), list):
        return [item for item in retrieval_payload["source_results"] if isinstance(item, dict)]
    return []


def _load_pandas() -> Any:
    try:
        return import_module("pandas")
    except Exception as exc:
        raise RuntimeError(f"pandas import failed: {exc}") from exc


def _find_join_rule(domain: Dict[str, Any], left_dataset: str, right_dataset: str) -> Dict[str, Any] | None:
    for rule in domain.get("join_rules", []) if isinstance(domain.get("join_rules"), list) else []:
        if not isinstance(rule, dict):
            continue
        base = str(rule.get("base_dataset") or "").strip()
        join = str(rule.get("join_dataset") or "").strip()
        if base == left_dataset and join == right_dataset:
            return rule
        if base == right_dataset and join == left_dataset:
            reversed_rule = deepcopy(rule)
            reversed_rule["base_dataset"] = left_dataset
            reversed_rule["join_dataset"] = right_dataset
            return reversed_rule
    return None


def _common_join_columns(left_columns: list[str], right_columns: list[str]) -> list[str]:
    shared = set(left_columns) & set(right_columns)
    preferred = [column for column in PREFERRED_JOIN_COLUMNS if column in shared]
    return preferred or sorted(shared)[:3]


def _records_from_frame(frame: Any) -> list[Dict[str, Any]]:
    frame = frame.where(frame.notnull(), None)
    return frame.to_dict(orient="records")


def _merge_source_results(source_results: list[Dict[str, Any]], domain: Dict[str, Any]) -> Dict[str, Any]:
    if not source_results:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "summary": "분석할 원천 데이터가 없습니다.",
            "merge_notes": [],
        }
    valid_results = [item for item in source_results if item.get("success") and isinstance(item.get("data"), list)]
    failed_results = [item for item in source_results if not item.get("success")]
    if failed_results:
        first = failed_results[0]
        return {
            "success": False,
            "data": [],
            "columns": [],
            "summary": first.get("error_message", "원천 데이터 조회에 실패했습니다."),
            "merge_notes": [],
            "failed_source_results": failed_results,
        }
    if not valid_results:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "summary": "성공한 원천 데이터가 없습니다.",
            "merge_notes": [],
        }
    if len(valid_results) == 1:
        rows = deepcopy(valid_results[0].get("data", []))
        first = rows[0] if rows and isinstance(rows[0], dict) else {}
        return {
            "success": True,
            "data": rows,
            "columns": list(first.keys()),
            "summary": valid_results[0].get("summary", f"단일 데이터셋 {len(rows)}건"),
            "merge_notes": ["single_source"],
        }

    pd = _load_pandas()
    frames = []
    dataset_keys = []
    for result in valid_results:
        rows = result.get("data", [])
        if not rows:
            continue
        frame = pd.DataFrame(rows)
        if frame.empty:
            continue
        frames.append(frame)
        dataset_keys.append(str(result.get("dataset_key") or result.get("tool_name") or f"source_{len(frames)}"))

    if not frames:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "summary": "병합할 수 있는 원천 데이터가 없습니다.",
            "merge_notes": [],
        }

    merged = frames[0]
    merge_notes: list[str] = []
    current_dataset = dataset_keys[0]
    for index in range(1, len(frames)):
        right = frames[index]
        right_dataset = dataset_keys[index]
        rule = _find_join_rule(domain, current_dataset, right_dataset)
        if rule:
            join_columns = [str(item) for item in rule.get("join_keys", []) if str(item) in merged.columns and str(item) in right.columns]
            how = str(rule.get("join_type") or "left").lower()
            rule_name = str(rule.get("name") or "")
        else:
            join_columns = _common_join_columns([str(c) for c in merged.columns], [str(c) for c in right.columns])
            how = "inner"
            rule_name = ""
        if how not in {"left", "right", "inner", "outer"}:
            how = "left"
        if not join_columns:
            return {
                "success": False,
                "data": [],
                "columns": [],
                "summary": f"{current_dataset}와 {right_dataset} 사이의 공통 join key를 찾지 못했습니다.",
                "merge_notes": merge_notes,
            }
        merged = merged.merge(right, how=how, on=join_columns, suffixes=("", f"_{right_dataset}"))
        note = f"{current_dataset} + {right_dataset}: how={how}, keys={', '.join(join_columns)}"
        if rule_name:
            note += f", rule={rule_name}"
        merge_notes.append(note)
        current_dataset = f"{current_dataset}+{right_dataset}"

    return {
        "success": True,
        "data": _records_from_frame(merged),
        "columns": [str(column) for column in merged.columns],
        "summary": f"다중 데이터셋 병합 완료: {len(merged)}건",
        "merge_notes": merge_notes,
    }


def build_analysis_context(
    retrieval_result_payload: Any,
    domain_payload: Any,
    agent_state_payload: Any = None,
    main_context_payload: Any = None,
) -> Dict[str, Any]:
    retrieval_payload = _payload_from_value(retrieval_result_payload)
    main_context = _main_context_from_value(main_context_payload) or _main_context_from_value(retrieval_payload)
    retrieval_result = retrieval_payload.get("retrieval_result") if isinstance(retrieval_payload.get("retrieval_result"), dict) else retrieval_payload
    if domain_payload is None and main_context:
        domain_payload = main_context.get("domain_payload") or {"domain": main_context.get("domain", {})}
    domain = _get_domain(domain_payload)
    agent_state = _get_state(agent_state_payload) or retrieval_payload.get("agent_state") or {}
    if not agent_state and isinstance(main_context.get("agent_state"), dict):
        agent_state = main_context["agent_state"]
    intent = retrieval_payload.get("intent") if isinstance(retrieval_payload.get("intent"), dict) else {}
    plan = retrieval_payload.get("retrieval_plan") if isinstance(retrieval_payload.get("retrieval_plan"), dict) else retrieval_result.get("retrieval_plan", {})
    user_question = str(agent_state.get("pending_user_question") or intent.get("query_summary") or "")

    if isinstance(retrieval_result.get("early_result"), dict):
        return {
            "analysis_context": {
                "route": "finish",
                "early_result": retrieval_result["early_result"],
                "analysis_table": {"success": False, "data": [], "columns": [], "summary": retrieval_result["early_result"].get("response", "")},
                "retrieval_plan": plan,
                "intent": intent,
                "agent_state": agent_state,
                "user_question": user_question,
                "main_context": main_context,
            }
        }

    source_results = _as_source_results(retrieval_payload)
    merged = _merge_source_results(source_results, domain)
    return {
        "analysis_context": {
            "route": retrieval_result.get("route") or plan.get("route", ""),
            "analysis_table": merged,
            "source_results": source_results,
            "current_datasets": retrieval_result.get("current_datasets", {}),
            "source_snapshots": retrieval_result.get("source_snapshots", []),
            "retrieval_plan": plan,
            "intent": intent,
            "agent_state": agent_state,
            "user_question": user_question,
            "merge_notes": merged.get("merge_notes", []),
            "main_context": main_context,
        }
    }


class AnalysisBaseBuilder(Component):
    display_name = "Analysis Base Builder"
    description = "Build the dataframe-ready analysis context from dummy or Oracle retrieval results."
    icon = "Table2"
    name = "AnalysisBaseBuilder"

    inputs = [
        DataInput(name="retrieval_result", display_name="Retrieval Result", info="Output from Dummy Data Retriever or OracleDB Data Retriever.", input_types=["Data", "JSON"]),
        DataInput(name="main_context", display_name="Main Context", info="Optional direct output from Main Flow Context Builder. Usually propagated by Retrieval Result.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Legacy direct domain input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="agent_state", display_name="Agent State", info="Legacy direct state input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
    ]

    outputs = [
        Output(name="analysis_context", display_name="Analysis Context", method="build_context", types=["Data"]),
    ]

    def build_context(self) -> Data:
        payload = build_analysis_context(
            getattr(self, "retrieval_result", None),
            getattr(self, "domain_payload", None),
            getattr(self, "agent_state", None),
            getattr(self, "main_context", None),
        )
        context = payload.get("analysis_context", {})
        table = context.get("analysis_table", {}) if isinstance(context.get("analysis_table"), dict) else {}
        self.status = {
            "route": context.get("route", ""),
            "success": table.get("success", False),
            "row_count": len(table.get("data", [])) if isinstance(table.get("data"), list) else 0,
        }
        return _make_data(payload)
