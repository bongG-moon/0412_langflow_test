from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
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


class _FallbackMessage:
    def __init__(self, text: str | None = None, **kwargs: Any):
        self.text = text or str(kwargs.get("content") or "")
        self.content = self.text


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
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)


MONGO_URI = "mongodb+srv://bonggeon:qhdrjs123@datagov.5qcxapn.mongodb.net/?retryWrites=true&w=majority&appName=datagov"
DB_NAME = "datagov"
TABLE_COLLECTION = "manufacturing_flow_tables"


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
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return {"text": content}
    return {}


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    payload = _payload_from_value(value)
    for key in ("response", "answer", "llm_text", "text", "output", "content", "result"):
        if isinstance(payload.get(key), str):
            return payload[key].strip()
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return text.strip()
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(value or "").strip()


def _analysis_result(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    result = payload.get("analysis_result")
    return result if isinstance(result, dict) else payload


def _truthy(value: Any, default: bool = True) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "사용", "저장"}


def _safe_int(value: Any, default: int) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return default


def _safe_rows(value: Any, limit: int = 200) -> list[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows = [row for row in value if isinstance(row, dict)]
    return deepcopy(rows[:limit])


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return str(value)


def _format_cell(value: Any, max_chars: int = 80) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, default=str)
    elif value is None:
        text = ""
    else:
        text = str(value)
    text = text.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def _markdown_table(rows: Any, columns: Any, row_limit: int) -> str:
    if row_limit <= 0 or not isinstance(rows, list):
        return ""
    preview_rows = [row for row in rows[:row_limit] if isinstance(row, dict)]
    if not preview_rows:
        return ""
    if isinstance(columns, list) and columns:
        selected_columns = [str(column) for column in columns[:8]]
    else:
        selected_columns = [str(column) for column in preview_rows[0].keys()][:8]
    if not selected_columns:
        return ""
    header = "| " + " | ".join(selected_columns) + " |"
    divider = "| " + " | ".join(["---"] * len(selected_columns)) + " |"
    body = [
        "| " + " | ".join(_format_cell(row.get(column)) for column in selected_columns) + " |"
        for row in preview_rows
    ]
    return "\n".join([header, divider, *body])


def _build_answer_display_text(final_result: Dict[str, Any], display_row_limit_value: Any = 10) -> str:
    response = str(final_result.get("response") or "").strip()
    analysis_result = final_result.get("analysis_result") if isinstance(final_result.get("analysis_result"), dict) else {}
    rows = analysis_result.get("data") if isinstance(analysis_result.get("data"), list) else []
    columns = analysis_result.get("columns") if isinstance(analysis_result.get("columns"), list) else []
    row_count = analysis_result.get("row_count", len(rows))
    table_ref_id = str(analysis_result.get("table_ref_id") or "").strip()
    data_is_preview = bool(analysis_result.get("data_is_preview"))
    storage_status = final_result.get("table_storage_status") if isinstance(final_result.get("table_storage_status"), dict) else {}
    try:
        display_row_limit = max(0, int(display_row_limit_value or 10))
    except Exception:
        display_row_limit = 10

    parts = [response] if response else []
    facts: list[str] = []
    if row_count not in (None, ""):
        facts.append(f"- Result rows: {row_count}")
    if columns:
        facts.append(f"- Columns: {', '.join([str(column) for column in columns[:12]])}")
    if table_ref_id:
        facts.append(f"- Full table ref: `{table_ref_id}`")
    if storage_status.get("errors"):
        facts.append(f"- Table storage warning: {'; '.join([str(item) for item in storage_status.get('errors', [])])}")
    if facts:
        parts.append("\n".join(facts))

    table = _markdown_table(rows, columns, display_row_limit)
    if table:
        preview_note = f"Preview rows shown: {min(display_row_limit, len(rows))}"
        if data_is_preview:
            preview_note += " (full result is stored by reference when table_ref_id is present)"
        parts.append(f"{preview_note}\n\n{table}")
    return "\n\n".join(parts).strip() or "No displayable answer was produced."


def _resolve_db_name(value: Any = None) -> str:
    return str(value or os.getenv("MONGO_DB_NAME") or DB_NAME).strip() or DB_NAME


def _resolve_collection_name(value: Any = None) -> str:
    return str(value or os.getenv("MONGO_FLOW_TABLE_COLLECTION") or TABLE_COLLECTION).strip() or TABLE_COLLECTION


def _get_collection(db_name_value: Any = None, collection_name_value: Any = None) -> Any:
    try:
        mongo_client_cls = getattr(import_module("pymongo"), "MongoClient")
    except Exception as exc:
        raise RuntimeError(f"pymongo import failed: {exc}") from exc
    mongo_uri = os.getenv("MONGO_URI") or MONGO_URI
    client = mongo_client_cls(mongo_uri, serverSelectionTimeoutMS=5000)
    return client[_resolve_db_name(db_name_value)][_resolve_collection_name(collection_name_value)]


def _table_columns(rows: list[Dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    first = rows[0] if isinstance(rows[0], dict) else {}
    return [str(column) for column in first.keys()]


def _store_table_rows(
    rows: Any,
    table_kind: str,
    metadata: Dict[str, Any],
    db_name: str,
    collection_name: str,
) -> Dict[str, Any]:
    safe_rows = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    if not safe_rows:
        return {"stored": False, "table_ref_id": "", "row_count": 0, "columns": []}
    table_ref_id = f"{table_kind}_{uuid.uuid4().hex}"
    document = {
        "table_ref_id": table_ref_id,
        "table_kind": table_kind,
        "status": "active",
        "row_count": len(safe_rows),
        "columns": _table_columns(safe_rows),
        "metadata": _json_safe(metadata),
        "rows": _json_safe(safe_rows),
        "created_at": datetime.now(timezone.utc),
    }
    collection = _get_collection(db_name, collection_name)
    collection.insert_one(document)
    return {
        "stored": True,
        "table_ref_id": table_ref_id,
        "row_count": document["row_count"],
        "columns": document["columns"],
    }


def _replace_rows_with_ref(
    table_payload: Dict[str, Any],
    table_kind: str,
    metadata: Dict[str, Any],
    storage: Dict[str, Any],
    keep_preview_rows: bool,
    output_row_limit: int,
) -> Dict[str, Any]:
    slim = deepcopy(table_payload)
    rows = slim.get("data") if isinstance(slim.get("data"), list) else []
    store_result: Dict[str, Any]
    if storage.get("enabled") and rows:
        try:
            store_result = _store_table_rows(
                rows,
                table_kind,
                metadata,
                str(storage.get("db_name") or DB_NAME),
                str(storage.get("collection_name") or TABLE_COLLECTION),
            )
            if store_result.get("stored"):
                storage.setdefault("table_refs", []).append(
                    {
                        "table_ref_id": store_result.get("table_ref_id", ""),
                        "table_kind": table_kind,
                        "row_count": store_result.get("row_count", 0),
                        "columns": store_result.get("columns", []),
                        "metadata": _json_safe(metadata),
                    }
                )
        except Exception as exc:
            store_result = {
                "stored": False,
                "table_ref_id": "",
                "row_count": len(rows),
                "columns": _table_columns(rows),
                "error": str(exc),
            }
            storage.setdefault("errors", []).append(f"{table_kind}: {exc}")
    else:
        store_result = {"stored": False, "table_ref_id": "", "row_count": len(rows), "columns": _table_columns(rows)}

    slim["row_count"] = len(rows)
    slim["columns"] = _table_columns(rows)
    slim["table_ref_id"] = store_result.get("table_ref_id", "")
    slim["data_stored_in_mongodb"] = bool(store_result.get("stored"))
    if store_result.get("error"):
        slim["table_storage_error"] = store_result["error"]
    if keep_preview_rows:
        slim["data"] = _safe_rows(rows, output_row_limit)
        slim["data_is_preview"] = len(rows) > output_row_limit
        slim["preview_row_limit"] = output_row_limit
    else:
        slim["data"] = []
        slim["data_is_omitted"] = True
    return slim


def _slim_current_datasets(current_datasets: Any, storage: Dict[str, Any], output_row_limit: int) -> Dict[str, Any]:
    if not isinstance(current_datasets, dict):
        return {}
    slim: Dict[str, Any] = {}
    for dataset_key, dataset in current_datasets.items():
        if not isinstance(dataset, dict):
            continue
        slim[str(dataset_key)] = _replace_rows_with_ref(
            dataset,
            "current_dataset",
            {"dataset_key": dataset_key, "label": dataset.get("label", "")},
            storage,
            keep_preview_rows=False,
            output_row_limit=output_row_limit,
        )
    return slim


def _slim_source_snapshots(source_snapshots: Any, storage: Dict[str, Any], output_row_limit: int) -> list[Dict[str, Any]]:
    snapshots = source_snapshots if isinstance(source_snapshots, list) else []
    slim: list[Dict[str, Any]] = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        slim.append(
            _replace_rows_with_ref(
                snapshot,
                "source_snapshot",
                {
                    "dataset_key": snapshot.get("dataset_key", ""),
                    "dataset_label": snapshot.get("dataset_label", ""),
                    "required_params": snapshot.get("required_params", {}),
                },
                storage,
                keep_preview_rows=False,
                output_row_limit=output_row_limit,
            )
        )
    return slim


def _slim_source_results(source_results: Any, storage: Dict[str, Any], output_row_limit: int) -> list[Dict[str, Any]]:
    sources = source_results if isinstance(source_results, list) else []
    slim: list[Dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        slim.append(
            _replace_rows_with_ref(
                source,
                "source_result",
                {
                    "dataset_key": source.get("dataset_key", ""),
                    "dataset_label": source.get("dataset_label", ""),
                    "tool_name": source.get("tool_name", ""),
                    "applied_params": source.get("applied_params", {}),
                },
                storage,
                keep_preview_rows=False,
                output_row_limit=output_row_limit,
            )
        )
    return slim


def _slim_state_for_output(agent_state: Any, output_row_limit: int) -> Dict[str, Any]:
    if not isinstance(agent_state, dict):
        return {}
    slim = deepcopy(agent_state)
    current_data = slim.get("current_data")
    if isinstance(current_data, dict):
        rows = current_data.get("data") if isinstance(current_data.get("data"), list) else []
        current_data["row_count"] = current_data.get("row_count", len(rows))
        current_data["data"] = _safe_rows(rows, output_row_limit)
        current_data["data_is_preview"] = len(rows) > output_row_limit
    snapshots = slim.get("source_snapshots")
    if isinstance(snapshots, dict):
        for key, snapshot in list(snapshots.items()):
            if isinstance(snapshot, dict):
                rows = snapshot.get("data") if isinstance(snapshot.get("data"), list) else []
                snapshot["row_count"] = snapshot.get("row_count", len(rows))
                snapshot["data"] = []
                snapshot["data_is_omitted"] = True
                snapshots[key] = snapshot
    elif isinstance(snapshots, list):
        for snapshot in snapshots:
            if isinstance(snapshot, dict):
                rows = snapshot.get("data") if isinstance(snapshot.get("data"), list) else []
                snapshot["row_count"] = snapshot.get("row_count", len(rows))
                snapshot["data"] = []
                snapshot["data_is_omitted"] = True
    return slim


def _slim_analysis_result(result: Dict[str, Any], storage: Dict[str, Any], output_row_limit: int) -> Dict[str, Any]:
    slim = deepcopy(result)
    slim["agent_state"] = _slim_state_for_output(result.get("agent_state", {}), output_row_limit)
    slim["source_results"] = _slim_source_results(result.get("source_results", []), storage, output_row_limit)
    slim["current_datasets"] = _slim_current_datasets(result.get("current_datasets", {}), storage, output_row_limit)
    slim["source_snapshots"] = _slim_source_snapshots(result.get("source_snapshots", []), storage, output_row_limit)
    slim = _replace_rows_with_ref(
        slim,
        "analysis_result",
        {
            "tool_name": result.get("tool_name", ""),
            "summary": result.get("summary", ""),
            "analysis_logic": result.get("analysis_logic", ""),
            "source_dataset_keys": result.get("source_dataset_keys", []),
        },
        storage,
        keep_preview_rows=True,
        output_row_limit=output_row_limit,
    )
    slim["table_storage_status"] = {
        "enabled": bool(storage.get("enabled")),
        "database": storage.get("db_name", DB_NAME),
        "collection": storage.get("collection_name", TABLE_COLLECTION),
        "table_refs": storage.get("table_refs", []),
        "errors": storage.get("errors", []),
    }
    return slim


def _build_tool_results(result: Dict[str, Any], output_row_limit: int) -> list[Dict[str, Any]]:
    source_results = result.get("source_results") if isinstance(result.get("source_results"), list) else []
    analysis_tool = {
        "success": result.get("success", False),
        "tool_name": result.get("tool_name", "analyze_current_data"),
        "data": _safe_rows(result.get("data", []), output_row_limit),
        "table_ref_id": result.get("table_ref_id", ""),
        "data_stored_in_mongodb": result.get("data_stored_in_mongodb", False),
        "row_count": result.get("row_count", len(result.get("data", [])) if isinstance(result.get("data"), list) else 0),
        "summary": result.get("summary", ""),
        "error_message": result.get("error_message", ""),
        "analysis_logic": result.get("analysis_logic", ""),
        "generated_code": result.get("generated_code", ""),
        "display_expanded": True,
    }
    output = []
    for item in source_results:
        if isinstance(item, dict):
            source = deepcopy(item)
            source["display_expanded"] = False
            output.append(source)
    output.append(analysis_tool)
    return output


def _next_current_data(result: Dict[str, Any], previous_current_data: Any, output_row_limit: int) -> Any:
    if not result.get("success"):
        return previous_current_data
    current_data = {
        "success": True,
        "tool_name": result.get("tool_name", "analyze_current_data"),
        "original_tool_name": result.get("tool_name", "analyze_current_data"),
        "data": _safe_rows(result.get("data", []), output_row_limit),
        "table_ref_id": result.get("table_ref_id", ""),
        "data_stored_in_mongodb": result.get("data_stored_in_mongodb", False),
        "row_count": result.get("row_count", len(result.get("data", [])) if isinstance(result.get("data"), list) else 0),
        "data_is_preview": result.get("data_is_preview", False),
        "preview_row_limit": output_row_limit,
        "summary": result.get("summary", ""),
        "analysis_plan": result.get("analysis_plan", {}),
        "analysis_logic": result.get("analysis_logic", ""),
        "generated_code": result.get("generated_code", ""),
        "retrieval_applied_params": result.get("retrieval_applied_params", {}),
        "followup_applied_params": result.get("followup_applied_params", {}),
        "source_dataset_keys": result.get("source_dataset_keys", []),
        "current_datasets": result.get("current_datasets", {}),
        "source_snapshots": result.get("source_snapshots", []),
        "merge_notes": result.get("merge_notes", []),
        "table_storage_status": result.get("table_storage_status", {}),
    }
    return current_data


def build_final_answer(
    answer_llm_output: Any,
    analysis_result_payload: Any,
    store_tables_value: Any = True,
    output_row_limit_value: Any = 200,
    db_name_value: Any = None,
    collection_name_value: Any = None,
) -> Dict[str, Any]:
    result = _analysis_result(analysis_result_payload)
    agent_state = result.get("agent_state") if isinstance(result.get("agent_state"), dict) else {}
    previous_current_data = agent_state.get("current_data")
    user_question = str(result.get("user_question") or agent_state.get("pending_user_question") or "")
    llm_response = _extract_text(answer_llm_output)
    fallback_response = result.get("summary") or result.get("error_message") or "결과를 생성하지 못했습니다."
    response = llm_response or fallback_response
    output_row_limit = _safe_int(output_row_limit_value, 200)
    storage = {
        "enabled": _truthy(store_tables_value, default=True),
        "db_name": _resolve_db_name(db_name_value),
        "collection_name": _resolve_collection_name(collection_name_value),
        "table_refs": [],
        "errors": [],
    }
    slim_result = _slim_analysis_result(result, storage, output_row_limit)
    tool_results = _build_tool_results(slim_result, output_row_limit)
    current_data = _next_current_data(slim_result, previous_current_data, output_row_limit)
    extracted_params = result.get("retrieval_applied_params") or result.get("followup_applied_params") or {}

    next_state = deepcopy(agent_state)
    next_state.pop("pending_user_question", None)
    chat_history = next_state.get("chat_history") if isinstance(next_state.get("chat_history"), list) else []
    chat_history = [*chat_history, {"role": "user", "content": user_question}, {"role": "assistant", "content": response}]
    next_state["chat_history"] = chat_history[-20:]
    context = next_state.get("context") if isinstance(next_state.get("context"), dict) else {}
    context.update(
        {
            "last_intent": result.get("intent", {}),
            "last_retrieval_plan": result.get("retrieval_plan", {}),
            "last_extracted_params": extracted_params,
            "last_analysis_summary": result.get("summary", ""),
            "last_table_storage_status": slim_result.get("table_storage_status", {}),
        }
    )
    next_state["context"] = context
    next_state["current_data"] = current_data
    if isinstance(current_data, dict) and isinstance(current_data.get("source_snapshots"), list):
        next_state["source_snapshots"] = {
            str(item.get("dataset_key") or index): item
            for index, item in enumerate(current_data["source_snapshots"], start=1)
            if isinstance(item, dict)
        }

    final_payload = {
        "response": response,
        "tool_results": tool_results,
        "current_data": current_data,
        "extracted_params": extracted_params,
        "awaiting_analysis_choice": bool(result.get("awaiting_analysis_choice", result.get("success", False))),
        "table_storage_status": slim_result.get("table_storage_status", {}),
        "state": next_state,
        "state_json": json.dumps(next_state, ensure_ascii=False),
        "analysis_result": slim_result,
    }
    return {"final_result": final_payload, "next_state": next_state, "state_json": final_payload["state_json"]}


class FinalAnswerBuilder(Component):
    display_name = "Final Answer Builder"
    description = "Combine final answer text with analysis result and update the session state for the next turn."
    icon = "CheckCircle2"
    name = "FinalAnswerBuilder"

    inputs = [
        DataInput(name="answer_llm_output", display_name="Answer LLM Output", info="Output from built-in LLM node connected after Build Answer Prompt.", input_types=["Data", "Message", "Text", "JSON"]),
        DataInput(name="analysis_result", display_name="Analysis Result", info="Output from Execute Pandas Analysis.", input_types=["Data", "JSON"]),
        MessageTextInput(name="store_tables", display_name="Store Tables In MongoDB", value="true", advanced=True),
        MessageTextInput(name="output_row_limit", display_name="Output Row Limit", value="200", advanced=True),
        MessageTextInput(name="display_row_limit", display_name="Display Row Limit", value="10", advanced=True),
        MessageTextInput(name="db_name", display_name="Mongo Database Name", value=DB_NAME, advanced=True),
        MessageTextInput(name="collection_name", display_name="Mongo Table Collection", value=TABLE_COLLECTION, advanced=True),
    ]

    outputs = [
        Output(name="answer_message", display_name="Answer Message", method="build_answer_message", group_outputs=True, types=["Message"]),
        Output(name="final_result", display_name="Final Result", method="build_final_result", group_outputs=True, types=["Data"]),
        Output(name="next_state", display_name="Next State", method="build_next_state", group_outputs=True, types=["Data"]),
    ]

    def _payload(self) -> Dict[str, Any]:
        cached = getattr(self, "_cached_final_answer_payload", None)
        if isinstance(cached, dict):
            return cached
        payload = build_final_answer(
            getattr(self, "answer_llm_output", None),
            getattr(self, "analysis_result", None),
            getattr(self, "store_tables", "true"),
            getattr(self, "output_row_limit", "200"),
            getattr(self, "db_name", DB_NAME),
            getattr(self, "collection_name", TABLE_COLLECTION),
        )
        self._cached_final_answer_payload = payload
        return payload

    def build_final_result(self) -> Data:
        payload = self._payload()
        final_result = payload.get("final_result", {})
        self.status = {
            "response_chars": len(str(final_result.get("response", ""))),
            "tool_result_count": len(final_result.get("tool_results", [])) if isinstance(final_result.get("tool_results"), list) else 0,
            "table_ref_count": len(final_result.get("table_storage_status", {}).get("table_refs", []))
            if isinstance(final_result.get("table_storage_status"), dict)
            else 0,
        }
        return _make_data(final_result)

    def build_answer_message(self) -> Message:
        payload = self._payload()
        final_result = payload.get("final_result", {})
        text = _build_answer_display_text(final_result, getattr(self, "display_row_limit", "10"))
        self.status = {
            "display_chars": len(text),
            "display_row_limit": getattr(self, "display_row_limit", "10"),
        }
        return _make_message(text)

    def build_next_state(self) -> Data:
        payload = self._payload()
        return _make_data({"state": payload.get("next_state", {}), "state_json": payload.get("state_json", "")})
