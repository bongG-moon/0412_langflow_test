"""Runtime helpers shared by LangGraph nodes and Langflow components."""

from copy import deepcopy
from typing import Any, Dict, List

from ..analysis.engine import execute_analysis_query
from ..data.retrieval import (
    build_current_datasets,
    dataset_required_param_fields,
    dataset_requires_date,
    filter_rows_by_params,
    pick_retrieval_tools,
)
from .merge_service import build_analysis_base_table, build_multi_dataset_overview
from .query_mode import needs_post_processing, prune_followup_params
from .request_context import (
    attach_result_metadata,
    attach_source_dataset_metadata,
    build_unknown_retrieval_message,
    collect_current_source_dataset_keys,
    collect_source_snapshots,
    get_current_table_columns,
    has_current_data,
    normalize_filter_value,
    raw_dataset_key,
)
from .response_service import generate_response
from .retrieval_planner import (
    build_missing_date_message,
    build_retrieval_jobs,
    execute_retrieval_jobs,
    plan_retrieval_request,
    review_retrieval_sufficiency,
    should_retry_retrieval_plan,
)


def mark_primary_result(tool_results: List[Dict[str, Any]], primary_index: int) -> List[Dict[str, Any]]:
    """Mark the UI-default expanded result."""

    for index, result in enumerate(tool_results):
        result["display_expanded"] = index == primary_index
    return tool_results


def ensure_filtered_result_rows(result: Dict[str, Any], extracted_params: Dict[str, Any]) -> Dict[str, Any]:
    """Re-apply filters so the final visible table always matches the state filters."""

    if not result.get("success"):
        return result

    rows = result.get("data", [])
    if not isinstance(rows, list) or not rows:
        return result

    filtered_rows = filter_rows_by_params(rows, extracted_params)
    if len(filtered_rows) == len(rows):
        return result

    updated = dict(result)
    updated["data"] = filtered_rows

    summary = str(updated.get("summary", "")).strip()
    filter_note = f"Filtered rows: {len(filtered_rows)}"
    updated["summary"] = f"{summary} | {filter_note}" if summary else filter_note
    updated["available_columns"] = get_current_table_columns(updated)
    return updated


def build_source_snapshots(raw_source_results: List[Dict[str, Any]], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """raw source 결과를 다음 턴에 재사용할 수 있는 snapshot 목록으로 만든다."""

    snapshots: List[Dict[str, Any]] = []
    for raw_result, job in zip(raw_source_results, jobs):
        dataset_key = str(raw_result.get("dataset_key", "")).strip()
        if not dataset_key:
            continue

        rows = raw_result.get("data", [])
        first_row = rows[0] if isinstance(rows, list) and rows else {}
        required_params = {
            field_name: job["params"].get(field_name)
            for field_name in dataset_required_param_fields(raw_dataset_key(dataset_key))
            if job["params"].get(field_name) not in (None, "", [])
        }
        snapshots.append(
            {
                "dataset_key": dataset_key,
                "dataset_label": raw_result.get("dataset_label", dataset_key),
                "tool_name": raw_result.get("tool_name", ""),
                "summary": raw_result.get("summary", ""),
                "row_count": len(rows) if isinstance(rows, list) else 0,
                "columns": list(first_row.keys()) if isinstance(first_row, dict) else [],
                "required_params": required_params,
                "data": deepcopy(rows) if isinstance(rows, list) else [],
            }
        )
    return snapshots


def get_reusable_source_result(job: Dict[str, Any], current_data: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """현재 결과에 raw snapshot 이 남아 있으면 새 조회 대신 그 값을 재사용한다."""

    base_dataset_key = raw_dataset_key(job["dataset_key"])
    required_fields = dataset_required_param_fields(base_dataset_key)
    for snapshot in collect_source_snapshots(current_data):
        if raw_dataset_key(snapshot.get("dataset_key", "")) != base_dataset_key:
            continue

        required_params = snapshot.get("required_params", {}) or {}
        if any(
            normalize_filter_value(required_params.get(field_name))
            != normalize_filter_value(job["params"].get(field_name))
            for field_name in required_fields
        ):
            continue

        return {
            "success": True,
            "tool_name": str(snapshot.get("tool_name", "")),
            "data": deepcopy(snapshot.get("data", [])),
            "summary": str(snapshot.get("summary", "")),
            "dataset_key": job["dataset_key"],
            "dataset_label": snapshot.get("dataset_label", job["dataset_key"]),
            "reused_source_snapshot": True,
        }
    return None


def prepare_retrieval_source_results(
    jobs: List[Dict[str, Any]],
    current_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute jobs once and normalize the source results for downstream branches."""

    if not jobs:
        return {"source_results": [], "current_datasets": {}, "source_snapshots": []}

    raw_source_results: List[Dict[str, Any]] = []
    for job in jobs:
        reusable_result = get_reusable_source_result(job, current_data)
        raw_source_results.append(reusable_result or execute_retrieval_jobs([job])[0])

    source_results: List[Dict[str, Any]] = []
    for raw_result, job in zip(raw_source_results, jobs):
        result = deepcopy(raw_result)
        attach_result_metadata(result, job["params"], result.get("tool_name", ""))
        source_results.append(ensure_filtered_result_rows(result, job["params"]))

    return {
        "source_results": source_results,
        "current_datasets": build_current_datasets(raw_source_results),
        "source_snapshots": build_source_snapshots(raw_source_results, jobs),
    }


def build_single_retrieval_response(
    user_input: str,
    chat_history: List[Dict[str, str]],
    source_results: List[Dict[str, Any]],
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
    current_datasets: Dict[str, Any] | None = None,
    source_snapshots: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build the direct-response payload for a single retrieval result."""

    if not source_results:
        return {
            "response": "No retrieval result is available.",
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "failure_type": "missing_source_results",
            "awaiting_analysis_choice": False,
        }

    primary_source = source_results[-1]
    tool_results = mark_primary_result([primary_source], primary_index=0)
    final_params = primary_source.get("applied_params", {}) or extracted_params
    next_current_data = primary_source if primary_source.get("success") else current_data
    if isinstance(next_current_data, dict):
        next_current_data["retrieval_applied_params"] = dict(final_params or {})
        if current_datasets:
            next_current_data["current_datasets"] = current_datasets
        if source_snapshots:
            next_current_data["source_snapshots"] = source_snapshots
    return {
        "response": generate_response(user_input, primary_source, chat_history)
        if primary_source.get("success")
        else primary_source.get("error_message", "Failed to process retrieval result."),
        "tool_results": tool_results,
        "current_data": next_current_data,
        "extracted_params": final_params,
        "awaiting_analysis_choice": bool(primary_source.get("success")),
    }


def validate_retrieval_jobs(
    retrieval_keys: List[str],
    jobs: List[Dict[str, Any]],
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
) -> Dict[str, Any] | None:
    """조회 전에 공통 실패 케이스를 한 번에 검사한다."""

    if not retrieval_keys or not jobs:
        return {
            "response": build_unknown_retrieval_message(),
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "failure_type": "unknown_dataset",
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    missing_date_jobs = [job for job in jobs if dataset_requires_date(job["dataset_key"]) and not job["params"].get("date")]
    if missing_date_jobs:
        return {
            "response": build_missing_date_message([job["dataset_key"] for job in missing_date_jobs]),
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "failure_type": "missing_date",
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    return None


def route_single_post_processing(
    user_input: str,
    source_results: List[Dict[str, Any]],
    extracted_params: Dict[str, Any],
    retrieval_plan: Dict[str, Any] | None = None,
) -> str:
    """Return the next branch for a single retrieval path."""

    if not source_results:
        return "direct_response"
    primary_source = source_results[-1]
    if not primary_source.get("success"):
        return "direct_response"
    if needs_post_processing(user_input, extracted_params, retrieval_plan):
        return "post_analysis"
    return "direct_response"


def run_analysis_after_retrieval(
    user_input: str,
    chat_history: List[Dict[str, str]],
    source_results: List[Dict[str, Any]],
    extracted_params: Dict[str, Any],
    retrieval_plan: Dict[str, Any] | None = None,
    current_datasets: Dict[str, Any] | None = None,
    source_snapshots: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any] | None:
    """Run post-processing analysis after a single retrieval when needed."""

    if not source_results:
        return None
    if not needs_post_processing(user_input, extracted_params, retrieval_plan):
        return None

    primary_source = source_results[-1]
    if not primary_source.get("success"):
        return None

    if retrieval_plan and retrieval_plan.get("needs_post_processing") and len(source_results) == 1:
        sufficiency_review = review_retrieval_sufficiency(user_input, source_results, retrieval_plan)
        if not sufficiency_review.get("is_sufficient", True):
            existing_keys = [str(result.get("dataset_key", "")) for result in source_results if result.get("dataset_key")]
            retry_keys = list(dict.fromkeys([*existing_keys, *sufficiency_review.get("missing_dataset_keys", [])]))
            if retry_keys and set(retry_keys) != set(existing_keys):
                retry_jobs = build_retrieval_jobs(user_input, extracted_params, retry_keys)
                return run_multi_retrieval_jobs(
                    user_input=user_input,
                    chat_history=chat_history,
                    current_data=None,
                    jobs=retry_jobs,
                    retrieval_plan=retrieval_plan,
                )

    analysis_result = execute_analysis_query(
        query_text=user_input,
        data=primary_source.get("data", []),
        source_tool_name=primary_source.get("tool_name", ""),
    )
    analysis_result = attach_result_metadata(analysis_result, extracted_params, primary_source.get("tool_name", ""))

    if should_retry_retrieval_plan(retrieval_plan, source_results, analysis_result):
        retry_plan = plan_retrieval_request(
            user_input,
            chat_history,
            primary_source,
            retry_context={
                "selected_dataset_keys": [str(result.get("dataset_key", "")) for result in source_results if result.get("dataset_key")],
                "available_columns": get_current_table_columns(primary_source),
                "analysis_outcome": str(analysis_result.get("analysis_logic", "") or analysis_result.get("error_message", "")),
                "analysis_goal": str(retrieval_plan.get("analysis_goal", "")) if retrieval_plan else "",
            },
        )
        retry_keys = retry_plan.get("dataset_keys") or []
        existing_keys = [str(result.get("dataset_key", "")) for result in source_results if result.get("dataset_key")]
        if retry_keys and set(retry_keys) != set(existing_keys):
            retry_jobs = build_retrieval_jobs(user_input, extracted_params, retry_keys)
            return run_multi_retrieval_jobs(
                user_input=user_input,
                chat_history=chat_history,
                current_data=None,
                jobs=retry_jobs,
                retrieval_plan=retry_plan,
            )

    if analysis_result.get("success"):
        analysis_result["retrieval_applied_params"] = dict(
            analysis_result.get("applied_params", {}) or extracted_params
        )
        analysis_result["current_datasets"] = current_datasets or build_current_datasets(source_results)
        if source_snapshots:
            analysis_result["source_snapshots"] = source_snapshots
        attach_source_dataset_metadata(analysis_result, source_results)
        tool_results = mark_primary_result([*source_results, analysis_result], primary_index=len(source_results))
        return {
            "response": generate_response(user_input, analysis_result, chat_history),
            "tool_results": tool_results,
            "current_data": analysis_result,
            "extracted_params": extracted_params,
            "awaiting_analysis_choice": True,
        }

    source_summary = generate_response(user_input, primary_source, chat_history)
    response = (
        f"{analysis_result.get('error_message', 'Failed to finish post analysis.')}\n\n"
        f"Raw retrieval result summary:\n\n{source_summary}"
    )
    fallback_current_data = primary_source
    if isinstance(fallback_current_data, dict):
        fallback_current_data["retrieval_applied_params"] = dict(
            fallback_current_data.get("applied_params", {}) or extracted_params
        )
        if current_datasets:
            fallback_current_data["current_datasets"] = current_datasets
        if source_snapshots:
            fallback_current_data["source_snapshots"] = source_snapshots
    tool_results = mark_primary_result([*source_results, analysis_result], primary_index=len(source_results) - 1)
    return {
        "response": response,
        "tool_results": tool_results,
        "current_data": fallback_current_data,
        "extracted_params": extracted_params,
        "failure_type": "post_analysis_failed",
        "awaiting_analysis_choice": True,
    }


def build_multi_retrieval_response(
    user_input: str,
    chat_history: List[Dict[str, str]],
    source_results: List[Dict[str, Any]],
    current_data: Dict[str, Any] | None,
    jobs: List[Dict[str, Any]],
    current_datasets: Dict[str, Any] | None = None,
    source_snapshots: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build the overview response for multi retrieval without analysis."""

    failed_results = [result for result in source_results if not result.get("success")]
    if failed_results:
        first_error = failed_results[0]
        return {
            "response": first_error.get("error_message", "Multi retrieval failed."),
            "tool_results": source_results,
            "current_data": current_data,
            "extracted_params": jobs[0]["params"] if jobs else {},
            "failure_type": "retrieval_failed",
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    overview_result = build_multi_dataset_overview(source_results)
    overview_result = attach_result_metadata(
        overview_result,
        jobs[0]["params"] if jobs else {},
        "+".join(job["dataset_key"] for job in jobs),
    )
    overview_result["retrieval_applied_params"] = dict(overview_result.get("applied_params", {}) or {})
    overview_result["current_datasets"] = current_datasets or build_current_datasets(source_results)
    if source_snapshots:
        overview_result["source_snapshots"] = source_snapshots
    attach_source_dataset_metadata(overview_result, source_results)
    return {
        "response": generate_response(user_input, overview_result, chat_history),
        "tool_results": mark_primary_result([*source_results, overview_result], primary_index=len(source_results)),
        "current_data": overview_result,
        "extracted_params": jobs[0]["params"] if jobs else {},
        "awaiting_analysis_choice": True,
    }


def route_multi_post_processing(
    user_input: str,
    source_results: List[Dict[str, Any]],
    extracted_params: Dict[str, Any],
    retrieval_plan: Dict[str, Any] | None = None,
) -> str:
    """Return the next branch for a multi retrieval path."""

    if not source_results:
        return "overview_response"
    if any(not result.get("success") for result in source_results):
        return "overview_response"
    if needs_post_processing(user_input, extracted_params, retrieval_plan):
        return "post_analysis"
    return "overview_response"


def run_multi_retrieval_analysis(
    user_input: str,
    chat_history: List[Dict[str, str]],
    source_results: List[Dict[str, Any]],
    jobs: List[Dict[str, Any]],
    retrieval_plan: Dict[str, Any] | None = None,
    current_datasets: Dict[str, Any] | None = None,
    source_snapshots: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Run merge/analysis on already prepared multi-retrieval source results."""

    failed_results = [result for result in source_results if not result.get("success")]
    if failed_results:
        first_error = failed_results[0]
        return {
            "response": first_error.get("error_message", "Multi retrieval failed."),
            "tool_results": source_results,
            "current_data": None,
            "extracted_params": jobs[0]["params"] if jobs else {},
            "failure_type": "retrieval_failed",
            "awaiting_analysis_choice": False,
        }

    current_datasets = current_datasets or build_current_datasets(source_results)
    analysis_base = build_analysis_base_table(source_results, user_input, retrieval_plan=retrieval_plan)
    if not analysis_base.get("success"):
        overview_result = build_multi_dataset_overview(source_results)
        overview_result = attach_result_metadata(
            overview_result,
            jobs[0]["params"] if jobs else {},
            "+".join(job["dataset_key"] for job in jobs),
        )
        overview_result["retrieval_applied_params"] = dict(overview_result.get("applied_params", {}) or {})
        overview_result["current_datasets"] = current_datasets
        if source_snapshots:
            overview_result["source_snapshots"] = source_snapshots
        attach_source_dataset_metadata(overview_result, source_results)
        return {
            "response": analysis_base.get("error_message", "Failed to build a merged analysis table."),
            "tool_results": mark_primary_result([*source_results, overview_result], primary_index=len(source_results)),
            "current_data": overview_result,
            "extracted_params": jobs[0]["params"] if jobs else {},
            "failure_type": "merge_or_analysis_base_failed",
            "awaiting_analysis_choice": True,
        }

    analysis_result = execute_analysis_query(
        query_text=user_input,
        data=analysis_base.get("data", []),
        source_tool_name=analysis_base.get("tool_name", ""),
    )
    analysis_result = attach_result_metadata(
        analysis_result,
        jobs[0]["params"] if jobs else {},
        "+".join(job["dataset_key"] for job in jobs),
    )

    if analysis_result.get("success"):
        analysis_result["retrieval_applied_params"] = dict(analysis_result.get("applied_params", {}) or {})
        analysis_result["current_datasets"] = current_datasets
        if source_snapshots:
            analysis_result["source_snapshots"] = source_snapshots
        attach_source_dataset_metadata(analysis_result, source_results)
        analysis_result["analysis_base_info"] = {
            "join_columns": analysis_base.get("join_columns", []),
            "source_tool_names": analysis_base.get("source_tool_names", []),
            "merge_notes": analysis_base.get("merge_notes", []),
            "requested_dimensions": analysis_base.get("requested_dimensions", []),
        }
        return {
            "response": generate_response(user_input, analysis_result, chat_history),
            "tool_results": mark_primary_result([*source_results, analysis_result], primary_index=len(source_results)),
            "current_data": analysis_result,
            "extracted_params": jobs[0]["params"] if jobs else {},
            "awaiting_analysis_choice": True,
        }

    overview_result = build_multi_dataset_overview(source_results)
    overview_result = attach_result_metadata(
        overview_result,
        jobs[0]["params"] if jobs else {},
        "+".join(job["dataset_key"] for job in jobs),
    )
    overview_result["retrieval_applied_params"] = dict(overview_result.get("applied_params", {}) or {})
    overview_result["current_datasets"] = current_datasets
    if source_snapshots:
        overview_result["source_snapshots"] = source_snapshots
    attach_source_dataset_metadata(overview_result, source_results)
    return {
        "response": analysis_result.get("error_message", "Failed to finish multi-dataset analysis."),
        "tool_results": mark_primary_result([*source_results, overview_result], primary_index=len(source_results)),
        "current_data": overview_result,
        "extracted_params": jobs[0]["params"] if jobs else {},
        "failure_type": "post_analysis_failed",
        "awaiting_analysis_choice": True,
    }


def run_multi_retrieval_jobs(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any] | None,
    jobs: List[Dict[str, Any]],
    retrieval_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute multi retrieval jobs and continue to the correct next branch."""

    prepared = prepare_retrieval_source_results(jobs, current_data=current_data)
    source_results = prepared["source_results"]
    current_datasets = prepared["current_datasets"]
    source_snapshots = prepared["source_snapshots"]

    branch = route_multi_post_processing(
        user_input=user_input,
        source_results=source_results,
        extracted_params=jobs[0]["params"] if jobs else {},
        retrieval_plan=retrieval_plan,
    )
    if branch == "post_analysis":
        return run_multi_retrieval_analysis(
            user_input=user_input,
            chat_history=chat_history,
            source_results=source_results,
            jobs=jobs,
            retrieval_plan=retrieval_plan,
            current_datasets=current_datasets,
            source_snapshots=source_snapshots,
        )

    return build_multi_retrieval_response(
        user_input=user_input,
        chat_history=chat_history,
        source_results=source_results,
        current_data=current_data,
        jobs=jobs,
        current_datasets=current_datasets,
        source_snapshots=source_snapshots,
    )


def _build_source_results_from_snapshots(current_data: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """Rebuild source-like results from stored raw snapshots for follow-up retries."""

    source_results: List[Dict[str, Any]] = []
    for snapshot in collect_source_snapshots(current_data):
        dataset_key = str(snapshot.get("dataset_key", "")).strip()
        if not dataset_key:
            continue
        source_results.append(
            {
                "success": True,
                "dataset_key": dataset_key,
                "dataset_label": snapshot.get("dataset_label", dataset_key),
                "tool_name": snapshot.get("tool_name", ""),
                "summary": snapshot.get("summary", ""),
                "data": deepcopy(snapshot.get("data", [])) if isinstance(snapshot.get("data"), list) else [],
            }
        )
    return source_results


def _retry_followup_with_source_snapshots(
    user_input: str,
    current_data: Dict[str, Any],
    cleaned_params: Dict[str, Any],
) -> Dict[str, Any] | None:
    """Retry follow-up analysis from raw source snapshots when the current table is too summarized."""

    source_results = _build_source_results_from_snapshots(current_data)
    if not source_results:
        return None

    if len(source_results) == 1:
        retry_source = source_results[0]
        retry_result = execute_analysis_query(
            query_text=user_input,
            data=retry_source.get("data", []),
            source_tool_name=retry_source.get("tool_name", ""),
        )
        retry_result = attach_result_metadata(retry_result, cleaned_params, retry_source.get("tool_name", ""))
        if retry_result.get("success"):
            attach_source_dataset_metadata(retry_result, source_results)
        return retry_result

    analysis_base = build_analysis_base_table(source_results, user_input)
    if not analysis_base.get("success"):
        return None

    retry_result = execute_analysis_query(
        query_text=user_input,
        data=analysis_base.get("data", []),
        source_tool_name=analysis_base.get("tool_name", ""),
    )
    retry_result = attach_result_metadata(
        retry_result,
        cleaned_params,
        analysis_base.get("tool_name", ""),
    )
    if retry_result.get("success"):
        attach_source_dataset_metadata(retry_result, source_results)
        retry_result["analysis_base_info"] = {
            "join_columns": analysis_base.get("join_columns", []),
            "source_tool_names": analysis_base.get("source_tool_names", []),
            "merge_notes": analysis_base.get("merge_notes", []),
            "requested_dimensions": analysis_base.get("requested_dimensions", []),
        }
        retry_result["followup_used_source_snapshots"] = True
    return retry_result


def run_followup_analysis(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any],
    extracted_params: Dict[str, Any],
) -> Dict[str, Any]:
    """Run follow-up analysis on the current table."""

    cleaned_params = prune_followup_params(user_input, extracted_params)
    result = execute_analysis_query(
        query_text=user_input,
        data=current_data.get("data", []),
        source_tool_name=current_data.get("original_tool_name") or current_data.get("tool_name", ""),
    )
    result = attach_result_metadata(
        result,
        cleaned_params,
        current_data.get("original_tool_name") or current_data.get("tool_name", ""),
    )
    if (
        not result.get("success")
        and result.get("missing_columns")
        and collect_source_snapshots(current_data)
    ):
        retried_result = _retry_followup_with_source_snapshots(
            user_input=user_input,
            current_data=current_data,
            cleaned_params=cleaned_params,
        )
        if retried_result and retried_result.get("success"):
            result = retried_result

    if result.get("success"):
        result["retrieval_applied_params"] = dict(
            current_data.get("retrieval_applied_params")
            or current_data.get("applied_params", {})
            or {}
        )
        result["followup_applied_params"] = dict(cleaned_params or {})
        result["source_dataset_keys"] = collect_current_source_dataset_keys(current_data)
        if current_data.get("current_datasets"):
            result["current_datasets"] = current_data.get("current_datasets")
        source_snapshots = collect_source_snapshots(current_data)
        if source_snapshots:
            result["source_snapshots"] = source_snapshots
    tool_results = mark_primary_result([result], primary_index=0)
    return {
        "response": generate_response(user_input, result, chat_history)
        if result.get("success")
        else result.get("error_message", "Failed to finish follow-up analysis."),
        "tool_results": tool_results,
        "current_data": result if result.get("success") else current_data,
        "extracted_params": cleaned_params,
        "awaiting_analysis_choice": bool(result.get("success")),
    }


def run_retrieval(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
) -> Dict[str, Any]:
    """Main entry for the retrieval flow."""

    retrieval_plan = plan_retrieval_request(user_input, chat_history, current_data)
    retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(user_input)
    if not retrieval_keys:
        return {
            "response": build_unknown_retrieval_message(),
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "failure_type": "unknown_dataset",
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    jobs = build_retrieval_jobs(user_input, extracted_params, retrieval_keys)
    validation_error = validate_retrieval_jobs(
        retrieval_keys=retrieval_keys,
        jobs=jobs,
        current_data=current_data,
        extracted_params=extracted_params,
    )
    if validation_error is not None:
        return validation_error

    if len(jobs) > 1:
        return run_multi_retrieval_jobs(user_input, chat_history, current_data, jobs, retrieval_plan)

    single_job = jobs[0]
    prepared = prepare_retrieval_source_results([single_job], current_data=current_data)
    source_results = prepared["source_results"]
    current_datasets = prepared["current_datasets"]
    source_snapshots = prepared["source_snapshots"]

    if route_single_post_processing(
        user_input=user_input,
        source_results=source_results,
        extracted_params=single_job["params"],
        retrieval_plan=retrieval_plan,
    ) == "post_analysis":
        post_processed = run_analysis_after_retrieval(
            user_input=user_input,
            chat_history=chat_history,
            source_results=source_results,
            extracted_params=single_job["params"],
            retrieval_plan=retrieval_plan,
            current_datasets=current_datasets,
            source_snapshots=source_snapshots,
        )
        if post_processed is not None:
            return post_processed

    return build_single_retrieval_response(
        user_input=user_input,
        chat_history=chat_history,
        source_results=source_results,
        current_data=current_data,
        extracted_params=single_job["params"],
        current_datasets=current_datasets,
        source_snapshots=source_snapshots,
    )
