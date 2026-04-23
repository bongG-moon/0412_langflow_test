from __future__ import annotations

import json
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
    required: bool = False


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
PromptInput = _load_attr(["lfx.io", "langflow.io"], "PromptInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)


DEFAULT_TEMPLATE = """You generate safe pandas transformation code for manufacturing data.
Return JSON only. Do not include markdown fences.

User question:
{user_question}

Normalized intent:
{intent}

Retrieval plan:
{retrieval_plan}

Relevant domain metrics:
{metrics}

Relevant domain datasets:
{datasets}

Join and merge notes:
{merge_notes}

Available dataframe profile:
{data_profile}

Allowed dataframe columns:
{allowed_columns}

Sample rows:
{sample_rows}

Rules:
- Work only on dataframe `df`.
- Always assign the final pandas DataFrame to `result`.
- Do not import anything.
- Do not use files, network, shell, eval, exec, open, OS APIs, plotting, or database access.
- Use only existing columns from the allowed dataframe columns list.
- Treat allowed dataframe columns as authoritative. Ignore domain/catalog columns that are not in that list.
- Apply the user's filters, grouping, summary, sorting, top_n, and metric calculation intent.
- If the user asks for a metric formula listed in domain metrics, use that formula as a strong hint.
- If a requested column is missing, return an empty code string and explain the missing column in warnings.
- Keep code concise and readable.

Return exactly this schema:
{{
  "intent": "short summary",
  "operations": ["filter", "groupby", "agg", "sort_values"],
  "output_columns": [],
  "group_by_columns": [],
  "filters": [],
  "sort_by": "",
  "sort_order": "desc",
  "top_n": null,
  "metric_column": "",
  "warnings": [],
  "code": "result = df.copy()"
}}
"""


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
    return {}


def _main_context_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    main_context = payload.get("main_context")
    return main_context if isinstance(main_context, dict) else {}


def _compact_json(value: Any, limit: int = 6000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... truncated ..."


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _get_domain(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    domain = payload.get("domain")
    return domain if isinstance(domain, dict) else payload


def _analysis_context(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    context = payload.get("analysis_context")
    return context if isinstance(context, dict) else payload


def _column_names_from_defs(value: Any) -> list[str]:
    columns: list[str] = []
    for column in _as_list(value):
        if isinstance(column, dict):
            name = str(column.get("name") or "").strip()
        else:
            name = str(column or "").strip()
        if name:
            columns.append(name)
    return columns


def _relevant_domain_slice(domain: Dict[str, Any], context: Dict[str, Any], available_columns: list[str]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    intent = context.get("intent") if isinstance(context.get("intent"), dict) else {}
    plan = context.get("retrieval_plan") if isinstance(context.get("retrieval_plan"), dict) else {}
    dataset_keys: list[str] = []
    dataset_keys.extend(str(item) for item in _as_list(plan.get("dataset_keys")) if str(item).strip())
    for job in _as_list(plan.get("jobs")):
        if isinstance(job, dict) and str(job.get("dataset_key") or "").strip():
            dataset_keys.append(str(job["dataset_key"]).strip())
    dataset_keys.extend(str(item) for item in _as_list(intent.get("dataset_hints")) if str(item).strip())

    all_metrics = domain.get("metrics") if isinstance(domain.get("metrics"), dict) else {}
    metric_keys = [str(item).strip() for item in _as_list(intent.get("metric_hints")) if str(item).strip()]
    for metric_key in metric_keys:
        metric = all_metrics.get(metric_key)
        if isinstance(metric, dict):
            dataset_keys.extend(str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip())

    seen: set[str] = set()
    dataset_keys = [key for key in dataset_keys if not (key in seen or seen.add(key))]

    all_datasets = domain.get("datasets") if isinstance(domain.get("datasets"), dict) else {}
    available_column_set = set(available_columns)
    datasets: Dict[str, Any] = {}
    for key in dataset_keys:
        dataset = all_datasets.get(key)
        if not isinstance(dataset, dict):
            continue
        dataset_columns = _column_names_from_defs(dataset.get("columns"))
        if available_column_set:
            dataset_columns = [column for column in dataset_columns if column in available_column_set]
        datasets[key] = {
            "display_name": dataset.get("display_name", key),
            "description": dataset.get("description", ""),
            "required_params": dataset.get("required_params", []),
            "columns": dataset_columns,
        }

    metrics: Dict[str, Any] = {}
    for key, metric in all_metrics.items():
        if not isinstance(metric, dict):
            continue
        required_datasets = [str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip()]
        if key in metric_keys or any(dataset_key in dataset_keys for dataset_key in required_datasets):
            metrics[key] = {
                "display_name": metric.get("display_name", key),
                "aliases": metric.get("aliases", []),
                "required_datasets": required_datasets,
                "formula": metric.get("formula", ""),
                "description": metric.get("description", ""),
            }
    return metrics, datasets


def _profile_rows(rows: list[Dict[str, Any]], columns: list[str]) -> Dict[str, Any]:
    numeric_columns: list[str] = []
    text_columns: list[str] = []
    null_counts: Dict[str, int] = {}
    for column in columns:
        values = [row.get(column) for row in rows if isinstance(row, dict)]
        null_counts[column] = sum(1 for value in values if value in (None, ""))
        non_null = [value for value in values if value not in (None, "")]
        if non_null and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in non_null[:20]):
            numeric_columns.append(column)
        else:
            text_columns.append(column)
    return {
        "row_count": len(rows),
        "columns": columns,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
        "null_counts": null_counts,
    }


def build_pandas_analysis_prompt(
    analysis_context_payload: Any,
    domain_payload: Any,
    template_value: Any = None,
    main_context_payload: Any = None,
) -> str:
    context = _analysis_context(analysis_context_payload)
    main_context = _main_context_from_value(main_context_payload) or (
        context.get("main_context") if isinstance(context.get("main_context"), dict) else {}
    )
    table = context.get("analysis_table") if isinstance(context.get("analysis_table"), dict) else {}
    rows = table.get("data") if isinstance(table.get("data"), list) else []
    columns = [str(column) for column in (table.get("columns") if isinstance(table.get("columns"), list) else (list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []))]
    if domain_payload is None and main_context:
        domain_payload = main_context.get("domain_payload") or {"domain": main_context.get("domain", {})}
    domain = _get_domain(domain_payload)
    relevant_metrics, relevant_datasets = _relevant_domain_slice(domain, context, columns)
    template = str(template_value or DEFAULT_TEMPLATE).strip()
    template_vars = {
        "user_question": context.get("user_question", ""),
        "intent": _compact_json(context.get("intent", {}), limit=5000),
        "retrieval_plan": _compact_json(context.get("retrieval_plan", {}), limit=5000),
        "metrics": _compact_json(relevant_metrics, limit=5000),
        "datasets": _compact_json(relevant_datasets, limit=5000),
        "merge_notes": _compact_json(context.get("merge_notes", []), limit=2000),
        "data_profile": _compact_json(_profile_rows(rows, columns), limit=8000),
        "allowed_columns": _compact_json(columns, limit=4000),
        "sample_rows": _compact_json(rows[:8], limit=8000),
    }
    try:
        return template.format(**template_vars)
    except KeyError as exc:
        raise ValueError(f"Template placeholder error: {exc}") from exc


class BuildPandasAnalysisPrompt(Component):
    display_name = "Build Pandas Analysis Prompt"
    description = "Build the prompt payload for the LLM API Caller to generate safe pandas transformation JSON."
    icon = "MessageSquareCode"
    name = "BuildPandasAnalysisPrompt"

    inputs = [
        PromptInput(
            name="template",
            display_name="Template",
            value=DEFAULT_TEMPLATE,
            required=True,
            info="Use {user_question}, {intent}, {retrieval_plan}, {metrics}, {datasets}, {merge_notes}, {data_profile}, {allowed_columns}, and {sample_rows}.",
        ),
        DataInput(name="analysis_context", display_name="Analysis Context", info="Output from Analysis Base Builder.", input_types=["Data", "JSON"]),
        DataInput(name="main_context", display_name="Main Context", info="Optional direct output from Main Flow Context Builder. Usually propagated by Analysis Context.", input_types=["Data", "JSON"], advanced=True),
        DataInput(name="domain_payload", display_name="Domain Payload", info="Legacy direct domain input. Prefer propagated Main Context.", input_types=["Data", "JSON"], advanced=True),
    ]

    outputs = [
        Output(name="prompt", display_name="Prompt Message", method="build_prompt", group_outputs=True, types=["Message"]),
        Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt_payload", group_outputs=True, types=["Data"]),
    ]

    def build_prompt_text(self) -> str:
        prompt = build_pandas_analysis_prompt(
            getattr(self, "analysis_context", None),
            getattr(self, "domain_payload", None),
            getattr(self, "template", "") or DEFAULT_TEMPLATE,
            getattr(self, "main_context", None),
        )
        self.status = {"prompt_chars": len(prompt)}
        return prompt

    def build_prompt(self) -> Message:
        return _make_message(self.build_prompt_text())

    def build_prompt_payload(self) -> Data:
        return _make_data({"prompt": self.build_prompt_text(), "prompt_type": "pandas_analysis"})
