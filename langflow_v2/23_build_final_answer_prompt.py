from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output
from lfx.schema.data import Data


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            raise


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


def _analysis_result(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("analysis_result") if isinstance(payload.get("analysis_result"), dict) else payload


def _safe_rows(rows: Any, limit: int) -> list[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return deepcopy([row for row in rows if isinstance(row, dict)][:limit])


def _row_count_from_result(result: Dict[str, Any], rows: list[Dict[str, Any]]) -> int:
    for key in ("row_count", "total_row_count"):
        try:
            if result.get(key) is not None:
                return int(result[key])
        except Exception:
            pass
    data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
    try:
        if data_ref.get("row_count") is not None:
            return int(data_ref["row_count"])
    except Exception:
        pass
    return len(rows)


def _source_summaries(result: Dict[str, Any]) -> list[Dict[str, Any]]:
    summaries = []
    for item in result.get("source_results", []):
        if not isinstance(item, dict):
            continue
        rows = item.get("data") if isinstance(item.get("data"), list) else []
        data_ref = item.get("data_ref") if isinstance(item.get("data_ref"), dict) else {}
        summaries.append(
            {
                "dataset_key": item.get("dataset_key"),
                "tool_name": item.get("tool_name"),
                "success": item.get("success"),
                "summary": item.get("summary") or item.get("error_message", ""),
                "row_count": item.get("row_count") or data_ref.get("row_count") or len(rows),
                "has_data_ref": bool(data_ref),
            }
        )
    return summaries


def build_final_answer_prompt(analysis_result_value: Any, preview_row_limit_value: Any = "20") -> Dict[str, Any]:
    result = _analysis_result(analysis_result_value)
    try:
        preview_row_limit = max(0, int(preview_row_limit_value or 20))
    except Exception:
        preview_row_limit = 20
    rows = result.get("data") if isinstance(result.get("data"), list) else []
    state = result.get("state") if isinstance(result.get("state"), dict) else {}
    plan = result.get("intent_plan") if isinstance(result.get("intent_plan"), dict) else {}
    user_question = str(result.get("user_question") or state.get("pending_user_question") or "")
    preview_rows = _safe_rows(rows, preview_row_limit)
    data_ref = result.get("data_ref") if isinstance(result.get("data_ref"), dict) else {}
    prompt_context = {
        "user_question": user_question,
        "success": bool(result.get("success")),
        "summary": result.get("summary", ""),
        "error_message": result.get("error_message", ""),
        "analysis_logic": result.get("analysis_logic", ""),
        "merged_from": result.get("merged_from", ""),
        "intent_plan": plan,
        "source_summaries": _source_summaries(result),
        "result_row_count": _row_count_from_result(result, rows),
        "result_preview_rows": preview_rows,
        "result_has_data_ref": bool(data_ref),
        "columns": list(preview_rows[0].keys()) if preview_rows else [],
        "filter_notes": result.get("filter_notes", []),
        "merge_notes": result.get("merge_notes", []),
    }
    prompt = f"""You are the final response writer for a manufacturing data-analysis assistant.
Return JSON only.

Write a concise Korean answer for the user.

Rules:
- Answer from the provided analysis result only.
- Mention the key result numbers or groups that matter.
- If the result failed or needs clarification, clearly explain what is missing.
- Do not invent rows, columns, filters, or business facts.
- Keep the answer practical and short.

Analysis result context:
{json.dumps(prompt_context, ensure_ascii=False, default=str, indent=2)}

Return only:
{{
  "answer": "Korean final answer",
  "highlights": ["optional short bullet"],
  "warnings": []
}}"""
    return {
        "prompt_payload": {
            "prompt_type": "final_answer",
            "prompt": prompt,
            "analysis_result": result,
            "prompt_context": prompt_context,
            "preview_row_limit": preview_row_limit,
        }
    }


class BuildFinalAnswerPrompt(Component):
    display_name = "Build Final Answer Prompt"
    description = "Build the final natural-language answer prompt from the merged analysis result."
    icon = "FileText"
    name = "BuildFinalAnswerPrompt"

    inputs = [
        DataInput(name="analysis_result", display_name="Analysis Result", info="Output from Analysis Result Merger.", input_types=["Data", "JSON"]),
        MessageTextInput(name="preview_row_limit", display_name="Preview Row Limit", value="20", info="Number of result rows to include in the answer prompt.", advanced=True),
    ]
    outputs = [Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt", types=["Data"])]

    def build_prompt(self):
        payload = build_final_answer_prompt(getattr(self, "analysis_result", None), getattr(self, "preview_row_limit", "20"))
        prompt_payload = payload.get("prompt_payload", {})
        self.status = {"prompt_type": "final_answer", "chars": len(prompt_payload.get("prompt", "")), "rows": len(prompt_payload.get("prompt_context", {}).get("result_preview_rows", []))}
        return _make_data(payload)

