from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


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


def _preview_table(rows: list[Dict[str, Any]], limit: int = 5) -> str:
    preview = rows[:limit]
    if not preview:
        return ""
    columns = list(preview[0].keys())[:8]
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in preview:
        values = []
        for column in columns:
            text = str(row.get(column, "")).replace("\n", " ").replace("|", "\\|")
            values.append(text[:80])
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, divider, *body])


METRIC_LABELS = {
    "production": "생산량",
    "target": "목표",
    "achievement_rate": "달성률",
    "wip_qty": "WIP",
    "hold_qty": "홀드 수량",
    "scrap_qty": "스크랩 수량",
    "defect_qty": "불량 수량",
    "yield_rate": "수율",
    "utilization_rate": "가동률",
}


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def _format_number(value: Any) -> str:
    number = _number(value)
    if number is None:
        return str(value)
    if abs(number - int(number)) < 0.000001:
        return f"{int(number):,}"
    return f"{number:,.2f}"


def _metric_column(rows: list[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    columns = set(str(column) for row in rows for column in row.keys())
    for column in ("production", "target", "achievement_rate", "wip_qty", "hold_qty", "scrap_qty", "defect_qty", "yield_rate", "utilization_rate"):
        if column in columns:
            return column
    return ""


def _dimension_text(row: Dict[str, Any]) -> str:
    parts = []
    for column, label in (("MODE", "MODE"), ("OPER_NAME", "공정"), ("LINE", "라인"), ("MCP_NO", "제품")):
        if row.get(column) not in (None, ""):
            parts.append(f"{label} {row[column]}")
    return ", ".join(parts)


def _fallback_success_answer(analysis_result: Dict[str, Any]) -> str:
    rows = analysis_result.get("data") if isinstance(analysis_result.get("data"), list) else []
    rows = [row for row in rows if isinstance(row, dict)]
    if not rows:
        return str(analysis_result.get("summary") or "조회 결과가 없습니다.")

    metric = _metric_column(rows)
    label = METRIC_LABELS.get(metric, metric or "값")
    plan = analysis_result.get("intent_plan") if isinstance(analysis_result.get("intent_plan"), dict) else {}
    top_n = plan.get("top_n")
    group_by = [str(item) for item in _as_list(plan.get("group_by")) if str(item).strip()]

    if metric:
        values = [_number(row.get(metric)) for row in rows]
        numeric_values = [value for value in values if value is not None]
        if len(rows) == 1:
            dim = _dimension_text(rows[0])
            prefix = f"{dim}의 " if dim else ""
            if top_n:
                if dim:
                    return f"가장 {label}이 큰 항목은 {dim}이며 {label}은 {_format_number(rows[0].get(metric))}입니다."
                return f"가장 {label}이 큰 값은 {_format_number(rows[0].get(metric))}입니다."
            return f"{prefix}{label}은 {_format_number(rows[0].get(metric))}입니다."
        if numeric_values:
            total = sum(numeric_values)
            best = max(rows, key=lambda row: _number(row.get(metric)) if _number(row.get(metric)) is not None else float("-inf"))
            best_dim = _dimension_text(best)
            if group_by or top_n:
                detail = f" 가장 큰 항목은 {best_dim}이며 {label}은 {_format_number(best.get(metric))}입니다." if best_dim else ""
                return f"조회 결과 {len(rows)}건 기준 {label} 합계는 {_format_number(total)}입니다.{detail}"
            return f"조회 결과 {len(rows)}건의 총 {label}은 {_format_number(total)}입니다."

    return f"조회 결과 {len(rows)}건을 확인했습니다. {analysis_result.get('summary', '')}".strip()


def _fallback_answer(analysis_result: Dict[str, Any]) -> str:
    if not analysis_result.get("success"):
        return str(analysis_result.get("error_message") or analysis_result.get("summary") or "결과를 생성하지 못했습니다.")
    return _fallback_success_answer(analysis_result)


def normalize_answer_text(llm_result_value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(llm_result_value)
    llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
    prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
    analysis_result = prompt_payload.get("analysis_result") if isinstance(prompt_payload.get("analysis_result"), dict) else {}
    warnings = [str(item) for item in _as_list(llm_result.get("errors")) if str(item).strip()]

    raw_answer = _extract_json_object(str(llm_result.get("llm_text") or ""))
    source = "llm"
    answer = ""
    if isinstance(raw_answer, dict) and raw_answer and not raw_answer.get("_parse_errors"):
        answer = str(raw_answer.get("answer") or raw_answer.get("response") or raw_answer.get("text") or "").strip()
    else:
        if raw_answer.get("_parse_errors"):
            warnings.extend(str(item) for item in _as_list(raw_answer.get("_parse_errors")) if str(item).strip())
        raw_answer = {}

    if not answer:
        answer = _fallback_answer(analysis_result)
        source = "fallback"

    answer_text = {
        "response": answer,
        "answer_source": source,
        "highlights": _as_list(raw_answer.get("highlights")) if isinstance(raw_answer, dict) else [],
        "warnings": [*_as_list(raw_answer.get("warnings") if isinstance(raw_answer, dict) else []), *warnings],
        "analysis_result": analysis_result,
    }
    return {"answer_text": answer_text}


class NormalizeAnswerText(Component):
    display_name = "Normalize Answer Text"
    description = "Parse final-answer LLM JSON and emit answer_text for the final answer builder."
    icon = "MessageSquareText"
    name = "NormalizeAnswerText"

    inputs = [
        DataInput(name="llm_result", display_name="LLM Result", info="Output from LLM JSON Caller (Answer).", input_types=["Data", "JSON"])
    ]
    outputs = [Output(name="answer_text", display_name="Answer Text", method="build_answer", types=["Data"])]

    def build_answer(self):
        payload = normalize_answer_text(getattr(self, "llm_result", None))
        answer_text = payload.get("answer_text", {})
        self.status = {"source": answer_text.get("answer_source"), "chars": len(str(answer_text.get("response", ""))), "warnings": len(answer_text.get("warnings", []))}
        return _make_data(payload)

