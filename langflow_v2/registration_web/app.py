from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st

try:
    from services.config import (
        DEFAULT_DB_NAME,
        DOMAIN_ITEMS_COLLECTION,
        LLM_API_KEY,
        LLM_MODEL_NAME,
        LLM_TEMPERATURE,
        MONGO_URI,
        TABLE_CATALOG_ITEMS_COLLECTION,
        VALID_GBNS,
        VALID_STATUSES,
    )
    from services.domain_text_v2 import build_domain_preview_from_text
    from services.domain_v2 import aggregate_domain, normalize_domain_input, split_lines, validate_items as validate_domain_items
    from services.mongo import (
        list_domain_items,
        list_table_items,
        ping,
        save_domain_items,
        save_table_items,
        soft_delete_domain_item,
        soft_delete_table_item,
    )
    from services.table_catalog_v2 import normalize_table_input, table_catalog, validate_items as validate_table_items
    from services.table_text_v2 import build_table_preview_from_text
except ModuleNotFoundError:
    from .services.config import (
        DEFAULT_DB_NAME,
        DOMAIN_ITEMS_COLLECTION,
        LLM_API_KEY,
        LLM_MODEL_NAME,
        LLM_TEMPERATURE,
        MONGO_URI,
        TABLE_CATALOG_ITEMS_COLLECTION,
        VALID_GBNS,
        VALID_STATUSES,
    )
    from .services.domain_text_v2 import build_domain_preview_from_text
    from .services.domain_v2 import aggregate_domain, normalize_domain_input, split_lines, validate_items as validate_domain_items
    from .services.mongo import (
        list_domain_items,
        list_table_items,
        ping,
        save_domain_items,
        save_table_items,
        soft_delete_domain_item,
        soft_delete_table_item,
    )
    from .services.table_catalog_v2 import normalize_table_input, table_catalog, validate_items as validate_table_items
    from .services.table_text_v2 import build_table_preview_from_text


APP_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = APP_DIR.parent / "examples"


DOMAIN_EXAMPLE = """WB, W/B는 W/B1, W/B2 공정 그룹을 의미한다.
DA, D/A는 D/A1, D/A2, D/A3, D/A4 공정 그룹을 의미한다.

생산 데이터셋은 production이고 생산량 컬럼은 production이다. 날짜 조건이 필요하고 mode별, 공정별 분석을 자주 한다.
재공 데이터셋은 wip이고 재공 수량 컬럼은 wip_qty이다. 날짜 조건이 필요하다.

생산달성율 또는 생산달성률은 생산량 / 재공 * 100으로 계산한다.
이 지표는 production 데이터와 wip 데이터를 같이 사용하며 결과 컬럼명은 achievement_rate로 둔다.
mode별로 자주 확인한다."""

TABLE_EXAMPLE = """production 데이터셋을 등록한다.
Oracle 조회용이고 db_key는 PKG_RPT, tool_name은 get_production_data이다.
필수 조건은 date이고 SQL format에 들어가는 값도 date 하나이다.
주요 컬럼은 WORK_DT(date), OPER_NAME(string), OPER_NUM(string), MODE(string), production(number)이다.
사용자 질문에서는 생산, 생산량, 실적, production 같은 단어로 찾을 수 있어야 한다.

wip 데이터셋을 등록한다.
Oracle 조회용이고 db_key는 PKG_RPT, tool_name은 get_wip_data이다.
필수 조건은 date이다.
주요 컬럼은 WORK_DT(date), OPER_NAME(string), MODE(string), wip_qty(number)이다.
사용자 질문에서는 재공, 재공량, wip 같은 단어로 찾을 수 있어야 한다."""


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def load_example(filename: str, fallback: str) -> str:
    path = EXAMPLES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def example_placeholder(text: str) -> str:
    return f"예시)\n{str(text or '').strip()}"


def inject_style() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1440px; }
        [data-testid="stSidebar"] { background: #f7f8fb; border-right: 1px solid #e4e7ec; }
        h1, h2, h3 { letter-spacing: 0; }
        .small-note { color: #667085; font-size: 0.88rem; line-height: 1.55; }
        div[data-testid="stTextArea"] textarea { font-size: 0.88rem !important; line-height: 1.45 !important; }
        div[data-testid="stTextArea"] textarea::placeholder { color: #98a2b3 !important; opacity: 1 !important; }
        div[data-testid="stTextInput"] input { font-size: 0.9rem !important; }
        code, pre { font-size: 0.8rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def settings_sidebar() -> Dict[str, Any]:
    st.sidebar.title("PKG Domain Registry")
    page = st.sidebar.radio(
        "Menu",
        ["도메인 자동 등록", "테이블 자동 등록", "JSON 가져오기", "조회/내보내기"],
        label_visibility="collapsed",
    )

    with st.sidebar.expander("MongoDB 설정", expanded=True):
        mongo_uri = st.text_input("Mongo URI", value=st.session_state.get("mongo_uri", MONGO_URI), type="password")
        db_name = st.text_input("Database", value=st.session_state.get("db_name", DEFAULT_DB_NAME))
        domain_collection = st.text_input("Domain Collection", value=st.session_state.get("domain_collection", DOMAIN_ITEMS_COLLECTION))
        table_collection = st.text_input("Table Catalog Collection", value=st.session_state.get("table_collection", TABLE_CATALOG_ITEMS_COLLECTION))
        st.session_state.mongo_uri = mongo_uri
        st.session_state.db_name = db_name
        st.session_state.domain_collection = domain_collection
        st.session_state.table_collection = table_collection
        if st.button("MongoDB 연결 확인", use_container_width=True):
            result = ping(mongo_uri, db_name)
            if result["ok"]:
                st.success(result["message"])
            else:
                st.error(result["message"])

    with st.sidebar.expander("LLM 설정", expanded=True):
        llm_api_key = st.text_input("LLM API Key", value=st.session_state.get("llm_api_key", LLM_API_KEY), type="password")
        model_name = st.text_input("Model", value=st.session_state.get("llm_model_name", LLM_MODEL_NAME))
        temperature = st.number_input("Temperature", value=float(st.session_state.get("llm_temperature", LLM_TEMPERATURE)), min_value=0.0, max_value=1.0, step=0.05)
        st.session_state.llm_api_key = llm_api_key
        st.session_state.llm_model_name = model_name
        st.session_state.llm_temperature = temperature

    st.sidebar.markdown(
        """
        <div class="small-note">
        자연어 설명을 LLM이 v2 MongoDB item document로 변환합니다.
        변환 결과는 저장 전에 JSON으로 직접 검토하고 수정할 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
    return {
        "page": page,
        "mongo_uri": mongo_uri,
        "db_name": db_name,
        "domain_collection": domain_collection,
        "table_collection": table_collection,
        "llm_api_key": llm_api_key,
        "model_name": model_name,
        "temperature": temperature,
    }


def existing_domain(settings: Dict[str, Any]) -> list[Dict[str, Any]]:
    try:
        return list_domain_items(settings["db_name"], settings["domain_collection"], "all", settings["mongo_uri"])
    except Exception:
        return []


def existing_tables(settings: Dict[str, Any]) -> list[Dict[str, Any]]:
    try:
        return list_table_items(settings["db_name"], settings["table_collection"], "all", settings["mongo_uri"])
    except Exception:
        return []


def show_issues(issues: list[Dict[str, Any]]) -> None:
    if not issues:
        st.success("검증 이슈가 없습니다.")
        return
    for issue in issues:
        message = str(issue.get("message") or issue)
        if issue.get("severity") == "error":
            st.error(message)
        elif issue.get("severity") == "warning":
            st.warning(message)
        else:
            st.info(message)


def result_summary_frame(rows: list[Dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["항목", "값", "설명"])


def show_result_summary(rows: list[Dict[str, str]]) -> None:
    st.dataframe(result_summary_frame(rows), use_container_width=True, hide_index=True)


def domain_frame(items: list[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in items:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        rows.append(
            {
                "gbn": item.get("gbn", ""),
                "key": item.get("key", ""),
                "status": item.get("status", ""),
                "display_name": payload.get("display_name", ""),
                "aliases": ", ".join(split_lines(payload.get("aliases"))),
                "required_datasets": ", ".join(split_lines(payload.get("required_datasets"))),
                "formula": payload.get("formula", ""),
                "output_column": payload.get("output_column", ""),
                "warnings": " | ".join(item.get("warnings", []) if isinstance(item.get("warnings"), list) else []),
            }
        )
    return pd.DataFrame(rows)


def table_frame(items: list[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in items:
        rows.append(
            {
                "dataset_key": item.get("dataset_key", ""),
                "status": item.get("status", ""),
                "display_name": item.get("display_name", ""),
                "tool_name": item.get("tool_name", ""),
                "source_type": item.get("source_type", ""),
                "db_key": item.get("db_key", ""),
                "required_params": ", ".join(split_lines(item.get("required_params"))),
                "format_params": ", ".join(split_lines(item.get("format_params"))),
                "keywords": ", ".join(split_lines(item.get("keywords"))),
            }
        )
    return pd.DataFrame(rows)


def value_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json_text(value)
    if value is None:
        return ""
    return str(value)


def key_value_frame(value: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"항목": key, "값": value_text(item)} for key, item in value.items()]
    return pd.DataFrame(rows, columns=["항목", "값"])


def domain_item_label(item: Dict[str, Any]) -> str:
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    display_name = str(payload.get("display_name") or "").strip()
    label = f"{item.get('gbn', '')}:{item.get('key', '')}"
    return f"{label} | {display_name}" if display_name else label


def table_item_label(item: Dict[str, Any]) -> str:
    label = str(item.get("dataset_key") or "")
    display_name = str(item.get("display_name") or "").strip()
    return f"{label} | {display_name}" if display_name else label


def render_domain_item_detail(item: Dict[str, Any], settings: Dict[str, Any], key_prefix: str) -> None:
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    single_domain_json = {"domain": aggregate_domain([item])}
    summary = {
        "gbn": item.get("gbn", ""),
        "key": item.get("key", ""),
        "status": item.get("status", ""),
        "display_name": payload.get("display_name", ""),
        "collection": settings["domain_collection"],
    }
    tab_summary, tab_payload, tab_langflow, tab_document = st.tabs(["요약", "Payload", "Langflow JSON", "원본 Document"])
    with tab_summary:
        st.dataframe(key_value_frame(summary), use_container_width=True, hide_index=True)
        if item.get("source_text"):
            st.text_area("Source Text", value=str(item.get("source_text") or ""), height=120, disabled=True, key=f"{key_prefix}_domain_source")
    with tab_payload:
        st.dataframe(key_value_frame(payload), use_container_width=True, hide_index=True)
    with tab_langflow:
        st.code(json_text(single_domain_json), language="json")
        st.download_button(
            "선택 항목 Domain JSON 다운로드",
            data=json_text(single_domain_json),
            file_name=f"langflow_v2_domain_{item.get('gbn', 'item')}_{item.get('key', 'item')}.json",
            mime="application/json",
            use_container_width=True,
            key=f"{key_prefix}_domain_download",
        )
    with tab_document:
        st.code(json_text(item), language="json")

    with st.expander("선택 항목 삭제", expanded=False):
        already_deleted = str(item.get("status") or "") == "deleted"
        if already_deleted:
            st.info("이미 deleted 상태인 항목입니다.")
        confirm = st.checkbox(
            f"{item.get('gbn')}:{item.get('key')} 항목을 deleted 상태로 변경합니다.",
            key=f"{key_prefix}_domain_delete_confirm",
            disabled=already_deleted,
        )
        if st.button("선택 domain item soft delete", disabled=already_deleted or not confirm, use_container_width=True, key=f"{key_prefix}_domain_delete"):
            result = soft_delete_domain_item(str(item.get("gbn") or ""), str(item.get("key") or ""), settings["db_name"], settings["domain_collection"], settings["mongo_uri"])
            st.success("삭제 처리했습니다.") if result.get("deleted") else st.warning("변경된 항목이 없습니다.")
            st.rerun()


def render_table_item_detail(item: Dict[str, Any], settings: Dict[str, Any], key_prefix: str) -> None:
    catalog_json = table_catalog([item])
    metadata = {key: value for key, value in item.items() if key not in {"columns", "source_text"}}
    summary = {
        "dataset_key": item.get("dataset_key", ""),
        "status": item.get("status", ""),
        "display_name": item.get("display_name", ""),
        "source_type": item.get("source_type", ""),
        "tool_name": item.get("tool_name", ""),
        "collection": settings["table_collection"],
    }
    tab_summary, tab_metadata, tab_columns, tab_langflow, tab_document = st.tabs(["요약", "Metadata", "Columns", "Langflow JSON", "원본 Document"])
    with tab_summary:
        st.dataframe(key_value_frame(summary), use_container_width=True, hide_index=True)
        if item.get("description"):
            st.text_area("Description", value=str(item.get("description") or ""), height=100, disabled=True, key=f"{key_prefix}_table_description")
    with tab_metadata:
        st.dataframe(key_value_frame(metadata), use_container_width=True, hide_index=True)
    with tab_columns:
        columns = item.get("columns") if isinstance(item.get("columns"), list) else []
        st.dataframe(pd.DataFrame(columns), use_container_width=True, hide_index=True)
    with tab_langflow:
        st.code(json_text(catalog_json), language="json")
        st.download_button(
            "선택 항목 Table Catalog JSON 다운로드",
            data=json_text(catalog_json),
            file_name=f"langflow_v2_table_catalog_{item.get('dataset_key', 'dataset')}.json",
            mime="application/json",
            use_container_width=True,
            key=f"{key_prefix}_table_download",
        )
    with tab_document:
        st.code(json_text(item), language="json")

    with st.expander("선택 항목 삭제", expanded=False):
        already_deleted = str(item.get("status") or "") == "deleted"
        if already_deleted:
            st.info("이미 deleted 상태인 항목입니다.")
        confirm = st.checkbox(
            f"{item.get('dataset_key')} dataset을 deleted 상태로 변경합니다.",
            key=f"{key_prefix}_table_delete_confirm",
            disabled=already_deleted,
        )
        if st.button("선택 dataset soft delete", disabled=already_deleted or not confirm, use_container_width=True, key=f"{key_prefix}_table_delete"):
            result = soft_delete_table_item(str(item.get("dataset_key") or ""), settings["db_name"], settings["table_collection"], settings["mongo_uri"])
            st.success("삭제 처리했습니다.") if result.get("deleted") else st.warning("변경된 항목이 없습니다.")
            st.rerun()


def render_domain_registration(settings: Dict[str, Any]) -> None:
    st.title("도메인 자동 등록")
    st.caption("사용자가 자연어로 적은 도메인 지식을 LLM이 v2 domain item document로 변환하고 MongoDB에 저장합니다.")

    with st.expander("입력 예시 보기", expanded=False):
        st.code(DOMAIN_EXAMPLE, language="text")

    raw_text = st.text_area(
        "도메인 설명",
        key="domain_user_text",
        height=260,
        placeholder=example_placeholder(DOMAIN_EXAMPLE),
    )
    convert_clicked = st.button("LLM으로 v2 도메인 변환", type="primary", use_container_width=True)

    if convert_clicked:
        try:
            with st.spinner("LLM이 도메인 설명을 v2 item document로 변환하는 중입니다."):
                preview = build_domain_preview_from_text(
                    raw_text=raw_text,
                    llm_api_key=settings["llm_api_key"],
                    model_name=settings["model_name"],
                    temperature=settings["temperature"],
                    existing_items=existing_domain(settings),
                )
            st.session_state.domain_text_preview = preview
            st.session_state.domain_text_items = preview["items"]
            st.session_state.domain_text_review_json = json_text(preview["items"])
        except Exception as exc:
            st.session_state.domain_text_preview = None
            st.session_state.domain_text_items = []
            st.error(f"도메인 변환 실패: {exc}")

    preview = st.session_state.get("domain_text_preview")
    items = st.session_state.get("domain_text_items", [])
    if not preview and not items:
        return

    st.subheader("변환 결과")
    if preview:
        st.info(f"자동 분류 후보: {', '.join(preview.get('routes', []))}")
        for error in preview.get("errors", []):
            st.error(error)
        if preview.get("unmapped_text"):
            st.warning(f"구조화하지 못한 내용: {preview['unmapped_text']}")

    review_json = st.text_area("검토/수정용 MongoDB item JSON", key="domain_text_review_json", height=360)
    if st.button("수정한 JSON 다시 검증", key="domain_revalidate", use_container_width=True):
        normalized = normalize_domain_input(review_json)
        st.session_state.domain_text_items = normalized["items"]
        for error in normalized["errors"]:
            st.error(error)
        if normalized["items"]:
            st.success("수정한 JSON을 다시 검증했습니다.")
        st.rerun()

    items = st.session_state.get("domain_text_items", [])
    validation = validate_domain_items(items, existing_domain(settings))
    st.markdown("#### 요약")
    show_result_summary(
        [
            {"항목": "변환 item", "값": f"{len(items)}건", "설명": "LLM이 생성한 domain item 수"},
            {"항목": "저장 가능 여부", "값": "가능" if validation["can_save"] else "확인 필요", "설명": "error가 없으면 저장 가능"},
            {"항목": "저장 collection", "값": settings["domain_collection"], "설명": "MongoDB 저장 위치"},
        ]
    )

    st.markdown("#### 검증")
    show_issues(validation["issues"])
    st.markdown("#### Item Preview")
    st.dataframe(domain_frame(items), use_container_width=True, hide_index=True)

    with st.expander("Langflow Domain JSON Loader 입력값 보기"):
        st.code(json_text({"domain": aggregate_domain(items)}), language="json")
    with st.expander("LLM Raw JSON / Prompt 보기"):
        st.markdown("LLM Raw JSON")
        st.code(json_text(preview.get("llm_json", {}) if preview else {}), language="json")
        st.markdown("Prompt")
        st.code(preview.get("prompt", "") if preview else "", language="text")

    st.download_button(
        "Domain JSON 다운로드",
        data=json_text({"domain": aggregate_domain(items)}),
        file_name="langflow_v2_domain.json",
        mime="application/json",
        use_container_width=True,
    )
    if st.button("MongoDB에 도메인 저장", disabled=not validation["can_save"], use_container_width=True):
        result = save_domain_items(items, settings["db_name"], settings["domain_collection"], settings["mongo_uri"])
        if result["saved"]:
            st.success(f"{result['saved_count']}건 저장했습니다.")
        else:
            st.error("저장에 실패했습니다.")
            for error in result.get("errors", []):
                st.error(error)


def render_table_registration(settings: Dict[str, Any]) -> None:
    st.title("테이블 자동 등록")
    st.caption("테이블/컬럼 설명을 LLM이 v2 Table Catalog item으로 변환합니다. SQL 본문은 저장하지 않습니다.")

    with st.expander("입력 예시 보기", expanded=False):
        st.code(TABLE_EXAMPLE, language="text")

    raw_text = st.text_area(
        "테이블/데이터셋 설명",
        key="table_user_text",
        height=300,
        placeholder=example_placeholder(TABLE_EXAMPLE),
    )
    if st.button("LLM으로 v2 테이블 카탈로그 변환", type="primary", use_container_width=True):
        try:
            with st.spinner("LLM이 테이블 설명을 v2 Table Catalog item으로 변환하는 중입니다."):
                preview = build_table_preview_from_text(
                    raw_text=raw_text,
                    llm_api_key=settings["llm_api_key"],
                    model_name=settings["model_name"],
                    temperature=settings["temperature"],
                    existing_items=existing_tables(settings),
                )
            st.session_state.table_text_preview = preview
            st.session_state.table_text_items = preview["items"]
            st.session_state.table_text_review_json = json_text(preview["items"])
        except Exception as exc:
            st.session_state.table_text_preview = None
            st.session_state.table_text_items = []
            st.error(f"테이블 변환 실패: {exc}")

    preview = st.session_state.get("table_text_preview")
    items = st.session_state.get("table_text_items", [])
    if not preview and not items:
        return

    st.subheader("변환 결과")
    for error in (preview or {}).get("errors", []):
        st.error(error)
    review_json = st.text_area("검토/수정용 Table Catalog item JSON", key="table_text_review_json", height=360)
    if st.button("수정한 테이블 JSON 다시 검증", key="table_revalidate", use_container_width=True):
        normalized = normalize_table_input(review_json)
        st.session_state.table_text_items = normalized["items"]
        for error in normalized["errors"]:
            st.error(error)
        if normalized["items"]:
            st.success("수정한 JSON을 다시 검증했습니다.")
        st.rerun()

    items = st.session_state.get("table_text_items", [])
    validation = validate_table_items(items, existing_tables(settings))
    st.markdown("#### 요약")
    show_result_summary(
        [
            {"항목": "변환 dataset", "값": f"{len(items)}건", "설명": "LLM이 생성한 table catalog item 수"},
            {"항목": "저장 가능 여부", "값": "가능" if validation["can_save"] else "확인 필요", "설명": "error가 없으면 저장 가능"},
            {"항목": "저장 collection", "값": settings["table_collection"], "설명": "MongoDB 저장 위치"},
        ]
    )

    st.markdown("#### 검증")
    show_issues(validation["issues"])
    st.markdown("#### Dataset Preview")
    st.dataframe(table_frame(items), use_container_width=True, hide_index=True)

    catalog = table_catalog(items)
    with st.expander("Langflow Table Catalog Loader 입력값 보기"):
        st.code(json_text(catalog), language="json")
    with st.expander("LLM Raw JSON / Prompt 보기"):
        st.markdown("LLM Raw JSON")
        st.code(json_text(preview.get("llm_json", {}) if preview else {}), language="json")
        st.markdown("Prompt")
        st.code(preview.get("prompt", "") if preview else "", language="text")

    st.download_button(
        "Table Catalog JSON 다운로드",
        data=json_text(catalog),
        file_name="langflow_v2_table_catalog.json",
        mime="application/json",
        use_container_width=True,
    )
    if st.button("MongoDB에 테이블 카탈로그 저장", disabled=not validation["can_save"], use_container_width=True):
        result = save_table_items(items, settings["db_name"], settings["table_collection"], settings["mongo_uri"])
        if result["saved"]:
            st.success(f"{result['saved_count']}건 저장했습니다.")
        else:
            st.error("저장에 실패했습니다.")
            for error in result.get("errors", []):
                st.error(error)


def render_json_import(settings: Dict[str, Any]) -> None:
    st.title("JSON 가져오기")
    tab_domain, tab_table = st.tabs(["도메인 JSON", "테이블 카탈로그 JSON"])

    with tab_domain:
        default_text = load_example("mongodb_domain_items_example.json", "[]")
        raw = st.text_area(
            "Domain JSON",
            key="domain_json_input_text",
            height=420,
            placeholder=example_placeholder(default_text),
        )
        if st.button("도메인 JSON 변환/검증", type="primary", use_container_width=True):
            if not raw.strip():
                st.warning("가져올 Domain JSON을 입력해 주세요.")
                return
            result = normalize_domain_input(raw)
            st.session_state.domain_import_items = result["items"]
            st.session_state.domain_import_errors = result["errors"]
        for error in st.session_state.get("domain_import_errors", []):
            st.error(error)
        items = st.session_state.get("domain_import_items", [])
        if items:
            validation = validate_domain_items(items, existing_domain(settings))
            show_issues(validation["issues"])
            st.dataframe(domain_frame(items), use_container_width=True, hide_index=True)
            if st.button("MongoDB에 도메인 JSON 저장", disabled=not validation["can_save"], use_container_width=True):
                result = save_domain_items(items, settings["db_name"], settings["domain_collection"], settings["mongo_uri"])
                st.success(f"{result['saved_count']}건 저장했습니다.") if result["saved"] else st.error(result.get("errors", ["저장 실패"])[0])

    with tab_table:
        default_text = load_example("table_catalog_example.json", '{"datasets": {}}')
        raw = st.text_area(
            "Table Catalog JSON",
            key="table_json_input_text",
            height=420,
            placeholder=example_placeholder(default_text),
        )
        if st.button("테이블 JSON 변환/검증", type="primary", use_container_width=True):
            if not raw.strip():
                st.warning("가져올 Table Catalog JSON을 입력해 주세요.")
                return
            result = normalize_table_input(raw)
            st.session_state.table_import_items = result["items"]
            st.session_state.table_import_errors = result["errors"]
        for error in st.session_state.get("table_import_errors", []):
            st.error(error)
        items = st.session_state.get("table_import_items", [])
        if items:
            validation = validate_table_items(items, existing_tables(settings))
            show_issues(validation["issues"])
            st.dataframe(table_frame(items), use_container_width=True, hide_index=True)
            if st.button("MongoDB에 테이블 JSON 저장", disabled=not validation["can_save"], use_container_width=True):
                result = save_table_items(items, settings["db_name"], settings["table_collection"], settings["mongo_uri"])
                st.success(f"{result['saved_count']}건 저장했습니다.") if result["saved"] else st.error(result.get("errors", ["저장 실패"])[0])


def render_lookup(settings: Dict[str, Any]) -> None:
    st.title("조회/내보내기")
    st.caption("MongoDB에 저장된 v2 item을 확인하고 Langflow 입력 JSON으로 내보냅니다.")
    tab_domain, tab_table = st.tabs(["도메인", "테이블 카탈로그"])

    with tab_domain:
        status = st.selectbox("Domain Status", ["active", "review_required", "deleted", "all"], index=0, key="domain_status")
        gbn_filter = st.selectbox("Domain Type", ["all", *VALID_GBNS], index=0, key="domain_gbn_filter")
        try:
            items = list_domain_items(settings["db_name"], settings["domain_collection"], status, settings["mongo_uri"])
        except Exception as exc:
            st.error(str(exc))
            items = []
        if gbn_filter != "all":
            items = [item for item in items if item.get("gbn") == gbn_filter]
        st.dataframe(domain_frame(items), use_container_width=True, hide_index=True)
        domain_json = {"domain": aggregate_domain(items)}
        st.download_button("Domain JSON 다운로드", data=json_text(domain_json), file_name="langflow_v2_domain_export.json", mime="application/json", use_container_width=True)
        with st.expander("Domain JSON 보기"):
            st.code(json_text(domain_json), language="json")
        if items:
            st.markdown("#### 선택 항목 상세")
            labels = [domain_item_label(item) for item in items]
            selected = st.selectbox("상세 조회할 domain item", labels, key="domain_detail_select")
            selected_item = items[labels.index(selected)]
            render_domain_item_detail(selected_item, settings, "lookup")

    with tab_table:
        status = st.selectbox("Table Status", ["active", "review_required", "deleted", "all"], index=0, key="table_status")
        try:
            items = list_table_items(settings["db_name"], settings["table_collection"], status, settings["mongo_uri"])
        except Exception as exc:
            st.error(str(exc))
            items = []
        st.dataframe(table_frame(items), use_container_width=True, hide_index=True)
        catalog_json = table_catalog(items)
        st.download_button("Table Catalog JSON 다운로드", data=json_text(catalog_json), file_name="langflow_v2_table_catalog_export.json", mime="application/json", use_container_width=True)
        with st.expander("Table Catalog JSON 보기"):
            st.code(json_text(catalog_json), language="json")
        if items:
            st.markdown("#### 선택 항목 상세")
            labels = [table_item_label(item) for item in items]
            selected = st.selectbox("상세 조회할 dataset", labels, key="table_detail_select")
            selected_item = items[labels.index(selected)]
            render_table_item_detail(selected_item, settings, "lookup")


def main() -> None:
    st.set_page_config(page_title="PKG Domain Registry", layout="wide")
    inject_style()
    settings = settings_sidebar()
    page = settings["page"]
    if page == "도메인 자동 등록":
        render_domain_registration(settings)
    elif page == "테이블 자동 등록":
        render_table_registration(settings)
    elif page == "JSON 가져오기":
        render_json_import(settings)
    else:
        render_lookup(settings)


if __name__ == "__main__":
    main()
