"""분석 결과를 사람이 읽기 쉬운 자연어 응답으로 바꾸는 서비스."""

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..shared.config import SYSTEM_PROMPT
from ..shared.number_format import format_rows_for_display
from ..shared.text_sanitizer import sanitize_markdown_text
from .request_context import build_recent_chat_text, get_llm_for_task


def format_result_preview(result: Dict[str, Any], max_rows: int = 5) -> str:
    """결과 테이블 일부를 JSON 미리보기 형태로 만든다."""

    rows = result.get("data", [])
    if not isinstance(rows, list) or not rows:
        return "결과 없음"

    preview_rows, _ = format_rows_for_display([row for row in rows[:max_rows] if isinstance(row, dict)])
    return json.dumps(preview_rows, ensure_ascii=False, indent=2)


def build_response_scope_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """응답 모델이 결과 해석에 필요한 조회 범위 정보를 작게 정리한다."""

    analysis_base_info = result.get("analysis_base_info", {}) if isinstance(result.get("analysis_base_info"), dict) else {}
    return {
        "source_dataset_keys": result.get("source_dataset_keys", []),
        "applied_filters": result.get("retrieval_applied_params") or result.get("applied_params", {}) or {},
        "available_result_columns": result.get("available_columns", []),
        "analysis_base_info": {
            "join_columns": analysis_base_info.get("join_columns", []),
            "requested_dimensions": analysis_base_info.get("requested_dimensions", []),
        },
    }


def build_response_prompt(user_input: str, result: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    """최종 설명문을 만들기 위한 LLM 프롬프트를 조립한다."""

    scope_info = build_response_scope_info(result)

    return f"""당신은 제조 데이터 분석 결과를 한국어로 간결하게 설명하는 어시스턴트입니다.

사용자 질문:
{user_input}

최근 대화:
{build_recent_chat_text(chat_history)}

결과 요약:
{result.get('summary', '')}

결과 행 수:
{len(result.get('data', []))}

결과 미리보기:
{format_result_preview(result)}

조회 범위 정보:
{json.dumps(scope_info, ensure_ascii=False)}

분석 계획:
{json.dumps(result.get('analysis_plan', {}), ensure_ascii=False)}

작성 규칙:
1. 현재 결과에서 확인되는 사실만 설명한다.
2. `조회 범위 정보.applied_filters`에 값이 있으면 그 필터가 이미 원본 데이터에 적용된 것으로 간주한다.
3. 그룹핑/집계 후 `MODE`, `WORK_DT` 같은 컬럼이 최종 표에 없어도 그 이유만으로 필터가 반영되지 않았다고 쓰지 않는다.
4. 필요하면 "최종 표에 해당 컬럼이 남아 있지 않을 뿐, 조회 범위에는 이미 반영되었다"는 식으로 설명한다.
5. 중요한 수치와 기준을 함께 언급한다.
6. 표 전체를 반복하지 말고 핵심만 3~5문장으로 요약한다.
7. 수치 단위나 비교 기준이 있으면 함께 적는다.
8. 한국어로 자연스럽게 작성한다.
"""


def generate_response(user_input: str, result: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    """최종 사용자 응답을 생성한다.

    마지막에 `sanitize_markdown_text` 를 한 번 더 거쳐서,
    `~~` 같은 마크다운 특수문자 때문에 화면이 깨지지 않도록 방어한다.
    """

    prompt = build_response_prompt(user_input, result, chat_history)
    try:
        llm = get_llm_for_task("response_summary")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        if isinstance(response.content, str):
            return sanitize_markdown_text(response.content)
        if isinstance(response.content, list):
            joined = "\n".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in response.content)
            return sanitize_markdown_text(joined)
        return sanitize_markdown_text(str(response.content))
    except Exception:
        fallback = f"{result.get('summary', '결과 요약을 생성하지 못했습니다.')} 결과 미리보기만 먼저 제공합니다."
        return sanitize_markdown_text(fallback)
