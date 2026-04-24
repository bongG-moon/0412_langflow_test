from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
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


class _FallbackMessage:
    def __init__(self, text: str | None = None, **kwargs: Any):
        self.text = text or str(kwargs.get("content") or "")
        self.content = self.text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"], "Component", _FallbackComponent)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _make_message(text: str) -> Any:
    try:
        return Message(text=text)
    except TypeError:
        try:
            return Message(content=text)
        except TypeError:
            try:
                return Message(text)
            except Exception:
                return _FallbackMessage(text=text)


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
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("response", "answer", "text", "content", "message"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None) or getattr(value, "content", None)
    return str(text or "").strip()


def _analysis_result(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("analysis_result") if isinstance(payload.get("analysis_result"), dict) else payload


def _safe_rows(rows: Any, limit: int) -> list[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return deepcopy([row for row in rows if isinstance(row, dict)][:limit])


def _rows_columns(rows: list[Dict[str, Any]]) -> list[str]:
    return [str(key) for key in rows[0].keys()] if rows and isinstance(rows[0], dict) else []


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return str(value)


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


def _fallback_response(result: Dict[str, Any], row_limit: int) -> str:
    if not result.get("success"):
        return str(result.get("error_message") or result.get("summary") or "No final result was produced.")
    rows = result.get("data") if isinstance(result.get("data"), list) else []
    lines = [str(result.get("summary") or f"analysis result rows: {len(rows)}")]
    if rows:
        lines.append(f"Result rows: {len(rows)}")
        lines.append(f"Columns: {', '.join(_rows_columns(rows)[:12])}")
        table = _preview_table(rows, row_limit)
        if table:
            lines.append(table)
    return "\n\n".join(lines)


def build_final_answer(analysis_result_value: Any, answer_text_value: Any = "", output_row_limit_value: Any = "200", display_row_limit_value: Any = "5") -> Dict[str, Any]:
    result = _analysis_result(analysis_result_value)
    state = result.get("state") if isinstance(result.get("state"), dict) else {}
    plan = result.get("intent_plan") if isinstance(result.get("intent_plan"), dict) else {}
    user_question = str(result.get("user_question") or state.get("pending_user_question") or "")
    try:
        output_row_limit = max(0, int(output_row_limit_value or 200))
    except Exception:
        output_row_limit = 200
    try:
        display_row_limit = max(0, int(display_row_limit_value or 5))
    except Exception:
        display_row_limit = 5

    response = _text_from_value(answer_text_value) or _fallback_response(result, display_row_limit)
    rows = result.get("data") if isinstance(result.get("data"), list) else []
    slim_rows = _safe_rows(rows, output_row_limit)

    current_data = state.get("current_data")
    if result.get("success"):
        current_data = {
            "success": True,
            "tool_name": result.get("tool_name", "analyze_current_data"),
            "original_tool_name": result.get("tool_name", "analyze_current_data"),
            "data": slim_rows,
            "row_count": len(rows),
            "data_is_preview": len(rows) > output_row_limit,
            "preview_row_limit": output_row_limit,
            "summary": result.get("summary", ""),
            "analysis_logic": result.get("analysis_logic", ""),
            "generated_code": result.get("generated_code", ""),
            "retrieval_applied_params": result.get("retrieval_applied_params", {}),
            "followup_applied_params": result.get("followup_applied_params", {}),
            "source_dataset_keys": result.get("source_dataset_keys", []),
            "current_datasets": result.get("current_datasets", {}),
            "source_snapshots": result.get("source_snapshots", []),
            "merge_notes": result.get("merge_notes", []),
        }

    next_state = deepcopy(state)
    next_state.pop("pending_user_question", None)
    chat_history = next_state.get("chat_history") if isinstance(next_state.get("chat_history"), list) else []
    if user_question:
        chat_history = [*chat_history, {"role": "user", "content": user_question}, {"role": "assistant", "content": response}]
    next_state["chat_history"] = chat_history[-20:]

    extracted_params = result.get("retrieval_applied_params") or result.get("followup_applied_params") or plan.get("required_params", {})
    context = next_state.get("context") if isinstance(next_state.get("context"), dict) else {}
    context.update({"last_intent": plan, "last_retrieval_plan": {"route": plan.get("route"), "jobs": plan.get("retrieval_jobs", [])}, "last_extracted_params": extracted_params, "last_analysis_summary": result.get("summary", "")})
    next_state["context"] = context
    next_state["last_intent"] = plan
    next_state["last_retrieval_plan"] = {"route": plan.get("route"), "jobs": plan.get("retrieval_jobs", [])}
    next_state["current_data"] = current_data
    if isinstance(current_data, dict):
        next_state["source_snapshots"] = current_data.get("source_snapshots", [])

    analysis_result = deepcopy(result)
    analysis_result["data"] = slim_rows
    analysis_result["row_count"] = len(rows)
    analysis_result["data_is_preview"] = len(rows) > output_row_limit

    tool_results = []
    for source in result.get("source_results", []):
        if isinstance(source, dict):
            copied = deepcopy(source)
            copied["display_expanded"] = False
            tool_results.append(copied)
    tool_results.append({"success": result.get("success", False), "tool_name": result.get("tool_name", "analyze_current_data"), "data": slim_rows, "row_count": len(rows), "summary": result.get("summary", ""), "error_message": result.get("error_message", ""), "analysis_logic": result.get("analysis_logic", ""), "generated_code": result.get("generated_code", ""), "display_expanded": True})

    final_result = {
        "response": response,
        "tool_results": tool_results,
        "current_data": current_data,
        "extracted_params": extracted_params,
        "awaiting_analysis_choice": bool(result.get("awaiting_analysis_choice", result.get("success", False))),
        "analysis_result": _json_safe(analysis_result),
        "state": _json_safe(next_state),
        "state_json": json.dumps(_json_safe(next_state), ensure_ascii=False),
    }
    return {"final_result": final_result, "next_state": next_state, "state_json": final_result["state_json"], "answer_message": response}


class FinalAnswerBuilder(Component):
    display_name = "V2 Final Answer Builder"
    description = "Standalone final payload and next-state builder."
    icon = "CheckCircle2"
    name = "V2FinalAnswerBuilder"

    inputs = [
        DataInput(name="analysis_result", display_name="Analysis Result", info="Output from V2 Pandas Analysis Executor.", input_types=["Data", "JSON"]),
        DataInput(name="answer_text", display_name="Optional Answer Text", info="Optional LLM/text answer. If empty, a deterministic summary is used.", input_types=["Data", "Message", "Text", "JSON"], advanced=True),
        MessageTextInput(name="output_row_limit", display_name="Output Row Limit", value="200", advanced=True),
        MessageTextInput(name="display_row_limit", display_name="Display Row Limit", value="5", advanced=True),
    ]

    outputs = [
        Output(name="answer_message", display_name="Answer Message", method="build_answer_message", group_outputs=True, types=["Message"]),
        Output(name="final_result", display_name="Final Result", method="build_final_result", group_outputs=True, types=["Data"]),
        Output(name="next_state", display_name="Next State", method="build_next_state", group_outputs=True, types=["Data"]),
    ]

    def _payload(self) -> Dict[str, Any]:
        cached = getattr(self, "_cached_payload", None)
        if isinstance(cached, dict):
            return cached
        payload = build_final_answer(getattr(self, "analysis_result", None), getattr(self, "answer_text", ""), getattr(self, "output_row_limit", "200"), getattr(self, "display_row_limit", "5"))
        self._cached_payload = payload
        return payload

    def build_answer_message(self):
        return _make_message(str(self._payload().get("answer_message", "")))

    def build_final_result(self):
        payload = self._payload()
        final_result = payload.get("final_result", {})
        self.status = {"response_chars": len(str(final_result.get("response", ""))), "tool_result_count": len(final_result.get("tool_results", [])) if isinstance(final_result.get("tool_results"), list) else 0}
        return _make_data(final_result)

    def build_next_state(self):
        payload = self._payload()
        return _make_data({"state": payload.get("next_state", {}), "state_json": payload.get("state_json", "")})
