from __future__ import annotations

import json
from copy import deepcopy
from importlib import import_module
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


def _pd():
    return import_module("pandas")


PREFERRED_JOIN_COLUMNS = ["WORK_DT", "WORK_DATE", "OPER_NAME", "OPER_NUM", "MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2", "LINE", "line"]


def _rows_columns(rows: list[Dict[str, Any]]) -> list[str]:
    return [str(key) for key in rows[0].keys()] if rows and isinstance(rows[0], dict) else []


def _retrieval_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("retrieval_payload") if isinstance(payload.get("retrieval_payload"), dict) else payload


def _domain_from_payload(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    if isinstance(payload.get("domain_payload"), dict):
        payload = payload["domain_payload"]
    if isinstance(payload.get("domain"), dict):
        return deepcopy(payload["domain"])
    if any(key in payload for key in ("products", "process_groups", "terms", "metrics", "join_rules")):
        return deepcopy(payload)
    return {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}


def _source_results(retrieval: Dict[str, Any]) -> list[Dict[str, Any]]:
    results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
    return [item for item in results if isinstance(item, dict)]


def _merge_sources(source_results: list[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [item for item in source_results if item.get("success") and isinstance(item.get("data"), list)]
    failed = [item for item in source_results if not item.get("success")]
    if failed:
        first = failed[0]
        return {"success": False, "data": [], "columns": [], "summary": first.get("error_message", "Retrieval failed."), "merge_notes": [], "failed_source_results": failed}
    if not valid:
        return {"success": False, "data": [], "columns": [], "summary": "No source data is available.", "merge_notes": []}
    if len(valid) == 1:
        rows = deepcopy(valid[0].get("data", []))
        return {"success": True, "data": rows, "columns": _rows_columns(rows), "summary": valid[0].get("summary", f"{len(rows)} rows"), "merge_notes": ["single_source"]}

    pd = _pd()
    frames = []
    dataset_keys = []
    for result in valid:
        rows = [row for row in result.get("data", []) if isinstance(row, dict)]
        if rows:
            frames.append(pd.DataFrame(rows))
            dataset_keys.append(str(result.get("dataset_key") or result.get("tool_name") or f"source_{len(frames)}"))
    if not frames:
        return {"success": False, "data": [], "columns": [], "summary": "No mergeable source data is available.", "merge_notes": []}

    merged = frames[0]
    notes: list[str] = []
    current_name = dataset_keys[0]
    for index in range(1, len(frames)):
        right = frames[index]
        right_name = dataset_keys[index]
        shared = set(str(column) for column in merged.columns) & set(str(column) for column in right.columns)
        join_columns = [column for column in PREFERRED_JOIN_COLUMNS if column in shared] or sorted(shared)[:3]
        if not join_columns:
            return {"success": False, "data": [], "columns": [], "summary": f"No common join key between {current_name} and {right_name}.", "merge_notes": notes}
        merged = merged.merge(right, how="inner", on=join_columns, suffixes=("", f"_{right_name}"))
        notes.append(f"{current_name}+{right_name}: keys={', '.join(join_columns)}")
        current_name = f"{current_name}+{right_name}"
    merged = merged.where(pd.notnull(merged), None)
    rows = merged.to_dict(orient="records")
    return {"success": True, "data": rows, "columns": [str(column) for column in merged.columns], "summary": f"merged rows {len(rows)}", "merge_notes": notes}


def _domain_prompt(domain: Dict[str, Any]) -> str:
    return json.dumps(
        {
            "products": domain.get("products", {}),
            "process_groups": domain.get("process_groups", {}),
            "terms": domain.get("terms", {}),
            "metrics": domain.get("metrics", {}),
            "join_rules": domain.get("join_rules", []),
        },
        ensure_ascii=False,
        default=str,
        indent=2,
    )


def _build_prompt(plan: Dict[str, Any], rows: list[Dict[str, Any]], columns: list[str], domain: Dict[str, Any]) -> str:
    return f"""You are writing safe pandas code for a manufacturing data assistant.
Return JSON only.

Rules:
- A pandas DataFrame named df already exists.
- Use only existing columns.
- Assign the final DataFrame to a variable named result.
- Do not import modules, read files, open sockets, or use eval/exec.
- Keep code short.

Intent plan:
{json.dumps(plan, ensure_ascii=False, default=str, indent=2)}

Available columns:
{json.dumps(columns, ensure_ascii=False)}

Domain/metric hints:
{_domain_prompt(domain)}

Data preview:
{json.dumps(rows[:5], ensure_ascii=False, default=str, indent=2)}

Return only:
{{
  "code": "result = df.copy()",
  "operations": ["short operation list"],
  "warnings": []
}}"""


def build_pandas_prompt(retrieval_payload_value: Any, domain_payload_value: Any = None) -> Dict[str, Any]:
    retrieval = _retrieval_payload(retrieval_payload_value)
    if retrieval.get("skipped"):
        return {"prompt_payload": {"skipped": True, "skip_reason": retrieval.get("skip_reason", "route skipped"), "prompt_type": "pandas_analysis", "retrieval_payload": retrieval, "table": {}, "intent_plan": retrieval.get("intent_plan", {}), "domain": {}, "columns": [], "row_count": 0, "prompt": ""}}
    plan = retrieval.get("intent_plan") if isinstance(retrieval.get("intent_plan"), dict) else {}
    source_results = _source_results(retrieval)
    table = _merge_sources(source_results)
    rows = table.get("data") if isinstance(table.get("data"), list) else []
    columns = table.get("columns") if isinstance(table.get("columns"), list) else _rows_columns(rows)
    domain = _domain_from_payload(domain_payload_value)
    prompt = _build_prompt(plan, rows, [str(column) for column in columns], domain)
    return {
        "prompt_payload": {
            "prompt_type": "pandas_analysis",
            "prompt": prompt,
            "retrieval_payload": retrieval,
            "table": table,
            "intent_plan": plan,
            "domain": domain,
            "columns": [str(column) for column in columns],
            "row_count": len(rows),
        }
    }


class BuildPandasPrompt(Component):
    display_name = "Build Pandas Prompt"
    description = "Build the pandas-code prompt from retrieved rows and domain hints."
    icon = "FileCode"
    name = "BuildPandasPrompt"

    inputs = [
        DataInput(name="retrieval_payload", display_name="Retrieval Payload", info="Output from Dummy or Oracle Retriever.", input_types=["Data", "JSON"]),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Domain/metric hints for pandas code.", input_types=["Data", "JSON"]),
    ]
    outputs = [Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt", types=["Data"])]

    def build_prompt(self):
        payload = build_pandas_prompt(getattr(self, "retrieval_payload", None), getattr(self, "domain_payload", None))
        prompt_payload = payload["prompt_payload"]
        self.status = {"rows": prompt_payload.get("row_count", 0), "columns": len(prompt_payload.get("columns", [])), "chars": len(prompt_payload.get("prompt", ""))}
        return _make_data(payload)

