"""사용자 질문에서 조회 파라미터를 추출하는 서비스."""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..analysis.contracts import RequiredParams
from ..domain.knowledge import PARAMETER_FIELD_SPECS, build_domain_knowledge_prompt
from ..domain.registry import build_registered_domain_prompt, detect_registered_values, expand_registered_values
from ..shared.config import SYSTEM_PROMPT
from ..shared.filter_utils import normalize_text
from .request_context import extract_text_from_response, get_llm_for_task, normalize_filter_value, parse_json_block


INHERITABLE_CONTEXT_FIELDS = [
    "date",
    "process_name",
    "oper_num",
    "pkg_type1",
    "pkg_type2",
    "product_name",
    "line_name",
    "mode",
    "den",
    "tech",
    "lead",
    "mcp_no",
]

INHERITED_FLAG_BY_FIELD = {
    "process_name": "process_inherited",
    "product_name": "product_inherited",
    "line_name": "line_inherited",
}

RETRIEVAL_CONTEXT_RESET_TRIGGERS = {"process_name", "oper_num", "line_name"}
RETRIEVAL_CONTEXT_RESET_FIELDS = [
    "oper_num",
    "pkg_type1",
    "pkg_type2",
    "product_name",
    "line_name",
    "mode",
    "den",
    "tech",
    "lead",
    "mcp_no",
]


def get_inherited_flag_name(field_name: str) -> str:
    """Return the flag name used when a value is inherited from context."""

    return INHERITED_FLAG_BY_FIELD.get(field_name, f"{field_name}_inherited")


def _merge_unique_values(*values: Any) -> List[str] | None:
    """단일 값, 리스트, None 을 모두 받아 순서를 유지한 고유 리스트로 합친다."""

    merged: List[str] = []
    for value in values:
        if value is None:
            continue
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            cleaned = str(candidate).strip()
            if cleaned and cleaned not in merged:
                merged.append(cleaned)
    return merged or None


def _contains_alias(text: str, alias: str) -> bool:
    """별칭이 다른 단어에 붙어 있는 오탐을 줄이기 위해 토큰 경계를 확인한다."""

    normalized_text = normalize_text(text)
    normalized_alias = normalize_text(alias)
    if not normalized_text or not normalized_alias:
        return False

    pattern = rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])"
    return bool(re.search(pattern, normalized_text, flags=re.IGNORECASE))


def _match_keyword_rules(text: Any, keyword_rules: List[Dict[str, Any]] | None) -> List[str] | None:
    """도메인 키워드 규칙에서 목표 값을 찾는다."""

    matched_targets: List[str] = []
    for rule in keyword_rules or []:
        aliases = rule.get("aliases", [])
        if any(_contains_alias(str(text or ""), alias) for alias in aliases):
            matched_targets.append(str(rule.get("target_value", "")).strip())
    return _merge_unique_values(matched_targets)


def _expand_group_values(
    raw_values: Any,
    groups: Dict[str, Dict[str, Any]] | None,
    literal_values: List[str] | None = None,
) -> List[str] | None:
    """LLM이 뽑아낸 그룹형 값을 실제 조회 값 목록으로 확장한다."""

    if not groups:
        return _merge_unique_values(raw_values)

    expanded_values: List[str] = []
    for raw_value in _merge_unique_values(raw_values) or []:
        matched = False
        for group in groups.values():
            aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
            if any(normalize_text(raw_value) == normalize_text(alias) for alias in aliases):
                expanded_values.extend(group.get("actual_values", []))
                matched = True
                break

        if matched:
            continue

        for literal_value in literal_values or []:
            if normalize_text(raw_value) == normalize_text(literal_value):
                expanded_values.append(literal_value)
                matched = True
                break

        if not matched:
            expanded_values.append(raw_value)

    return _merge_unique_values(expanded_values)


def _detect_multi_values_from_text(text: str, field_spec: Dict[str, Any]) -> List[str] | None:
    """텍스트 fallback으로 group/literal/pattern 기반 값을 모아 찾는다."""

    detected_values: List[str] = []

    for group in (field_spec.get("groups") or {}).values():
        aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
        if any(_contains_alias(text, alias) for alias in aliases):
            detected_values.extend(group.get("actual_values", []))

    for literal_value in field_spec.get("literal_values", []) or []:
        if _contains_alias(text, literal_value):
            detected_values.append(literal_value)

    for candidate in field_spec.get("candidate_values", []) or []:
        if _contains_alias(text, candidate):
            detected_values.append(candidate)

    for pattern in field_spec.get("patterns", []) or []:
        matches = re.findall(pattern, str(text or ""), flags=re.IGNORECASE)
        for match in matches:
            value = match if isinstance(match, str) else match[0]
            cleaned = str(value).strip()
            if cleaned:
                detected_values.append(cleaned)

    return _merge_unique_values(detected_values)


def _normalize_field_value(field_spec: Dict[str, Any], extracted_params: RequiredParams, user_input: str) -> None:
    """도메인 스펙 하나를 기준으로 필드 값을 정규화한다."""

    field_name = field_spec["field_name"]
    current_value = extracted_params.get(field_name)

    if field_spec.get("value_kind") == "single":
        keyword_value = _match_keyword_rules(current_value, field_spec.get("keyword_rules"))
        if not keyword_value and field_spec.get("allow_text_detection"):
            keyword_value = _match_keyword_rules(user_input, field_spec.get("keyword_rules"))
        normalized_single_value = keyword_value[0] if keyword_value else current_value
        expanded_value = expand_registered_values(field_name, normalized_single_value)
        if expanded_value:
            extracted_params[field_name] = expanded_value[0]
            return
        if normalized_single_value:
            cleaned_value = str(normalized_single_value).strip()
            extracted_params[field_name] = cleaned_value or None
            return
        detected_value = detect_registered_values(field_name, user_input)
        extracted_params[field_name] = detected_value[0] if detected_value else None
        return

    normalized_multi_value = _match_keyword_rules(current_value, field_spec.get("keyword_rules"))
    normalized_multi_value = _merge_unique_values(normalized_multi_value, current_value)
    normalized_multi_value = _expand_group_values(
        normalized_multi_value,
        field_spec.get("groups"),
        literal_values=field_spec.get("literal_values"),
    )
    normalized_multi_value = _merge_unique_values(
        normalized_multi_value,
        expand_registered_values(field_name, normalized_multi_value),
    )

    if not normalized_multi_value and field_spec.get("allow_text_detection"):
        normalized_multi_value = _match_keyword_rules(user_input, field_spec.get("keyword_rules"))
        normalized_multi_value = _merge_unique_values(
            normalized_multi_value,
            _detect_multi_values_from_text(user_input, field_spec),
        )

    extracted_params[field_name] = _merge_unique_values(
        normalized_multi_value,
        detect_registered_values(field_name, user_input),
    )


def _inherit_from_context(extracted_params: RequiredParams, context: Dict[str, Any] | None) -> RequiredParams:
    """이번 질문에서 비어 있는 조건은 직전 문맥에서 이어받는다."""

    if not isinstance(context, dict):
        return extracted_params

    for field in INHERITABLE_CONTEXT_FIELDS:
        if extracted_params.get(field) or not context.get(field):
            continue

        extracted_params[field] = context[field]
        extracted_params[get_inherited_flag_name(field)] = True

    return extracted_params


def apply_context_inheritance(extracted_params: RequiredParams, context: Dict[str, Any] | None) -> RequiredParams:
    """이미 추출된 파라미터에 직전 문맥을 덧씌운다.

    query mode 판정에서는 상속 전 값이 더 중요하고,
    실제 조회 실행에서는 상속 후 값이 더 편하다.
    두 흐름을 나눠 쓰기 위해 public helper 로 꺼내 둔다.
    """

    copied_params: RequiredParams = dict(extracted_params or {})
    return _inherit_from_context(copied_params, context)


def adjust_retrieval_params_for_context_reset(
    raw_extracted_params: RequiredParams,
    extracted_params: RequiredParams,
    current_data: Dict[str, Any] | None,
) -> RequiredParams:
    """새 raw scope를 명확히 바꾼 질문이면 이전 세부 필터 상속을 끊는다."""

    if not isinstance(current_data, dict):
        return extracted_params

    current_filters = current_data.get("retrieval_applied_params") or current_data.get("applied_params", {}) or {}
    has_scope_change = any(
        raw_extracted_params.get(field) not in (None, "", [])
        and normalize_filter_value(raw_extracted_params.get(field)) != normalize_filter_value(current_filters.get(field))
        for field in RETRIEVAL_CONTEXT_RESET_TRIGGERS
    )
    if not has_scope_change:
        return extracted_params

    adjusted_params: RequiredParams = dict(extracted_params or {})
    for field_name in RETRIEVAL_CONTEXT_RESET_FIELDS:
        if raw_extracted_params.get(field_name) not in (None, "", []):
            continue
        adjusted_params[field_name] = None
        adjusted_params.pop(get_inherited_flag_name(field_name), None)
    return adjusted_params


def _fallback_date(text: str) -> str | None:
    """LLM이 날짜를 놓쳤을 때 오늘, 어제 같은 기본 표현을 보정한다."""

    lower = str(text or "").lower()
    now = datetime.now()
    if "오늘" in lower or "today" in lower:
        return now.strftime("%Y%m%d")
    if "어제" in lower or "yesterday" in lower:
        return (now - timedelta(days=1)).strftime("%Y%m%d")
    return None


def _build_and_normalize_params(parsed: Dict[str, Any], user_input: str) -> RequiredParams:
    """LLM JSON 초안을 기본 파라미터 구조로 바꾸고 도메인 규칙으로 정리한다."""

    extracted_params: RequiredParams = {
        "date": parsed.get("date") or _fallback_date(user_input),
        "group_by": parsed.get("group_by"),
        "metrics": [],
        "lead": parsed.get("lead"),
    }

    for field_spec in PARAMETER_FIELD_SPECS:
        extracted_params[field_spec["field_name"]] = parsed.get(field_spec["response_key"])

    for field_spec in PARAMETER_FIELD_SPECS:
        _normalize_field_value(field_spec, extracted_params, user_input)
    return extracted_params


def resolve_required_params(
    user_input: str,
    chat_history_text: str,
    current_data_columns: List[str],
    context: Dict[str, Any] | None = None,
    inherit_context: bool = True,
) -> RequiredParams:
    """질문에서 조회에 필요한 파라미터를 추출해 반환한다.

    처리 순서는 아래와 같다.
    1. LLM이 질문과 도메인 텍스트를 보고 JSON 초안을 만든다.
    2. 코드는 도메인 스펙을 읽어 값을 정규화한다.
    3. 비어 있는 값은 이전 문맥에서 이어받는다.
    """

    today = datetime.now().strftime("%Y%m%d")
    domain_prompt = build_domain_knowledge_prompt()
    custom_domain_prompt = build_registered_domain_prompt()
    prompt = f"""You are extracting retrieval parameters for a manufacturing data assistant.
Return JSON only.

Rules:
- Extract only retrieval-safe fields and grouping hints.
- Normalize today/yesterday into YYYYMMDD.
- Use domain knowledge to expand process groups and interpret aliases.
- If a value is not explicit, return null.

Domain knowledge:
{domain_prompt}

Custom domain registry:
{custom_domain_prompt}

Recent chat:
{chat_history_text}

Available current-data columns:
{", ".join(current_data_columns) if current_data_columns else "(none)"}

Today's date:
{today}

User question:
{user_input}

Return only:
{{
  "date": "YYYYMMDD or null",
  "process": ["value"] or null,
  "oper_num": ["value"] or null,
  "pkg_type1": ["value"] or null,
  "pkg_type2": ["value"] or null,
  "product_name": "string or null",
  "line_name": "string or null",
  "mode": ["value"] or null,
  "den": ["value"] or null,
  "tech": ["value"] or null,
  "lead": "string or null",
  "mcp_no": "string or null",
  "group_by": "column or null"
}}"""

    parsed: Dict[str, Any] = {}
    try:
        llm = get_llm_for_task("parameter_extract")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = parse_json_block(extract_text_from_response(response.content))
    except Exception:
        parsed = {}

    # 1) LLM JSON 초안 -> 2) 기본 파라미터 생성 -> 3) 도메인 규칙 정규화
    extracted_params = _build_and_normalize_params(parsed, user_input)

    # 4) 필요하면 이전 대화 문맥에서 비어 있는 값을 이어받는다.
    if not inherit_context:
        return extracted_params
    return apply_context_inheritance(extracted_params, context)
