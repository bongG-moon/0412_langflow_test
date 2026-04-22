from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from services.config import (
    DEFAULT_DB_NAME,
    DOMAIN_ITEMS_COLLECTION,
    LLM_API_KEY,
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
    MONGO_URI,
    TABLE_CATALOG_ITEMS_COLLECTION,
    VALID_GBNS,
)
from services.domain_authoring_service import build_domain_preview
from services.domain_save_service import save_domain_preview
from services.domain_validation_service import validate_domain_items
from services.mongo import (
    list_domain_items,
    list_table_items,
    soft_delete_domain_item,
    soft_delete_table_item,
    test_connection,
)
from services.table_catalog_generate_service import generate_table_catalog, try_parse_table_catalog_text
from services.table_catalog_save_service import save_table_preview
from services.table_catalog_validation_service import normalize_and_validate_table_catalog, table_catalog_json_text


APP_DIR = Path(__file__).resolve().parent
AUTO_MODE = "자동 처리"
FORCE_LLM_MODE = "항상 LLM 생성"
JSON_ONLY_MODE = "JSON만 검증"


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }
        .block-container,
        .block-container p,
        .block-container label,
        .block-container li,
        .block-container div {
            font-size: 0.94rem;
        }
        .block-container h1 {
            font-size: 2.1rem;
            line-height: 1.2;
        }
        .block-container h2 {
            font-size: 1.38rem;
        }
        .block-container h3 {
            font-size: 1.12rem;
        }
        textarea,
        input,
        select,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="input"] input,
        [data-baseweb="select"] div,
        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] div,
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] p {
            font-size: 0.86rem !important;
        }
        pre,
        code,
        [data-testid="stCodeBlock"] pre,
        [data-testid="stCodeBlock"] code {
            font-size: 0.78rem !important;
            line-height: 1.42 !important;
        }
        [data-testid="stSidebar"] {
            background: #f8fafc;
            border-right: 1px solid #e2e8f0;
        }
        .side-title {
            font-size: 0.94rem;
            font-weight: 750;
            margin: 0.65rem 0 0.28rem;
            color: #0f172a;
        }
        .side-copy {
            color: #475569;
            font-size: 0.8rem;
            line-height: 1.48;
        }
        .flow-step {
            padding: 0.48rem 0.58rem;
            border: 1px solid #e2e8f0;
            background: #ffffff;
            border-radius: 8px;
            margin-bottom: 0.35rem;
            color: #334155;
            font-size: 0.78rem;
        }
        .section-panel {
            padding: 1rem 1.1rem;
            border: 1px solid #dbe4ee;
            border-radius: 8px;
            background: #ffffff;
            margin: 0.75rem 0 1.2rem;
        }
        .example-label {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 0.35rem;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] button {
            font-size: 0.82rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_example(filename: str, fallback: str) -> str:
    path = APP_DIR / "examples" / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _settings() -> Dict[str, Any]:
    return {
        "mongo_uri": MONGO_URI,
        "db_name": DEFAULT_DB_NAME,
        "domain_collection": DOMAIN_ITEMS_COLLECTION,
        "table_collection": TABLE_CATALOG_ITEMS_COLLECTION,
        "api_key": LLM_API_KEY,
        "model_name": LLM_MODEL_NAME,
        "temperature": LLM_TEMPERATURE,
    }


def _render_sidebar(settings: Dict[str, Any]) -> str:
    st.sidebar.title("Manufacturing Registry")
    page = st.sidebar.radio(
        "Menu",
        ["도메인 정보 등록", "테이블 정보 등록", "도메인 정보 조회", "테이블 정보 조회"],
        label_visibility="collapsed",
    )

    st.sidebar.markdown('<div class="side-title">무엇을 하는 화면인가요?</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div class="side-copy">
        제조 분석 Agent가 질문을 이해할 때 필요한 도메인 지식과 테이블 정보를 등록하는 관리 화면입니다.
        등록된 도메인 항목은 Main Flow가 MongoDB에서 읽어 의도 분류와 조건 정규화에 사용합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="side-title">사용 순서</div>', unsafe_allow_html=True)
    for step in (
        "1. 도메인 설명 또는 테이블 설명을 입력합니다.",
        "2. 작성 내용 검증을 눌러 구조화 결과를 확인합니다.",
        "3. 오류가 없으면 MongoDB에 등록합니다.",
        "4. Main Flow에서 등록된 정보를 불러와 질문 분석에 사용합니다.",
    ):
        st.sidebar.markdown(f'<div class="flow-step">{html.escape(step)}</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="side-title">등록 대상</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div class="side-copy">
        도메인: 제품, 공정 그룹, 용어, 지표, 조인 규칙<br>
        테이블: dataset key, SQL, 필수 파라미터, 컬럼, 질문 키워드
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar.expander("시스템 상태 확인"):
        st.caption("연결 정보와 LLM 키는 화면에서 수정하지 않고 설정 파일 값을 사용합니다.")
        if st.button("MongoDB 연결 확인", use_container_width=True):
            result = test_connection(settings["db_name"], settings["mongo_uri"])
            if result["ok"]:
                st.success(result["message"])
            else:
                st.error(result["message"])

    return page


def _render_example_block(title: str, example: str, state_key: str) -> None:
    st.markdown('<div class="example-label">입력 예시</div>', unsafe_allow_html=True)
    with st.expander(title, expanded=False):
        st.code(example, language="text")
        if st.button("예시를 입력창에 넣기", key=f"load_{state_key}", use_container_width=True):
            st.session_state[state_key] = example


def _render_summary_cards(cards: list[Dict[str, str]]) -> None:
    if not cards:
        return
    card_html = []
    for card in cards:
        label = html.escape(card.get("label", ""))
        value = html.escape(card.get("value", ""))
        help_text = html.escape(card.get("help", ""))
        card_html.append(
            f"""
            <div class="result-card">
                <div class="result-label">{label}</div>
                <div class="result-value" title="{value}">{value}</div>
                <div class="result-help">{help_text}</div>
            </div>
            """
        )
    components.html(
        f"""
        <style>
        body {{
            margin: 0;
            font-family: "Source Sans Pro", sans-serif;
            color: #0f172a;
        }}
        .result-grid {{
            display: grid;
            grid-template-columns: repeat({len(cards)}, minmax(0, 1fr));
            gap: 12px;
            width: 100%;
        }}
        .result-card {{
            box-sizing: border-box;
            height: 124px;
            border: 1px solid #d7dde8;
            border-radius: 8px;
            background: #ffffff;
            padding: 15px 18px;
            overflow: hidden;
        }}
        .result-label {{
            color: #6b7280;
            font-size: 13px;
            font-weight: 650;
            margin-bottom: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .result-value {{
            color: #111827;
            font-size: 19px;
            line-height: 1.15;
            font-weight: 740;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 13px;
        }}
        .result-help {{
            color: #7a828f;
            font-size: 12px;
            line-height: 1.35;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        @media (max-width: 820px) {{
            .result-grid {{
                grid-template-columns: 1fr;
            }}
            .result-card {{
                height: 112px;
            }}
        }}
        </style>
        <div class="result-grid">
            {"".join(card_html)}
        </div>
        """,
        height=138 if len(cards) > 1 else 132,
    )


def _render_issues(issues: list[Dict[str, Any]]) -> None:
    if not issues:
        st.success("검증 이슈가 없습니다.")
        return
    for issue in issues:
        message = f"[{issue.get('type', 'info')}] {issue.get('message', '')}"
        severity = issue.get("severity", "info")
        if severity == "error":
            st.error(message)
        elif severity == "warning":
            st.warning(message)
        else:
            st.info(message)


def _domain_items_frame(items: list[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in items:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        rows.append(
            {
                "gbn": item.get("gbn", ""),
                "key": item.get("key", ""),
                "status": item.get("status", ""),
                "display_name": payload.get("display_name", ""),
                "aliases": ", ".join(payload.get("aliases", []) if isinstance(payload.get("aliases"), list) else []),
                "keywords": ", ".join(payload.get("keywords", []) if isinstance(payload.get("keywords"), list) else []),
                "warnings": " | ".join(item.get("warnings", []) if isinstance(item.get("warnings"), list) else []),
            }
        )
    return pd.DataFrame(rows)


def _table_items_frame(items: list[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in items:
        rows.append(
            {
                "dataset_key": item.get("dataset_key", ""),
                "status": item.get("status", ""),
                "display_name": item.get("display_name", ""),
                "db_key": item.get("db_key", ""),
                "tool_name": item.get("tool_name", ""),
                "required_params": ", ".join(item.get("required_params", []) if isinstance(item.get("required_params"), list) else []),
                "keywords": ", ".join(item.get("keywords", []) if isinstance(item.get("keywords"), list) else []),
            }
        )
    return pd.DataFrame(rows)


def _domain_detail_label(item: Dict[str, Any]) -> str:
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    display_name = str(payload.get("display_name") or "").strip()
    prefix = f"{item.get('gbn', '')}:{item.get('key', '')}"
    if display_name:
        prefix = f"{prefix} | {display_name}"
    return f"{prefix} | {item.get('status', '')}"


def _table_detail_label(item: Dict[str, Any]) -> str:
    display_name = str(item.get("display_name") or "").strip()
    prefix = str(item.get("dataset_key") or "")
    if display_name:
        prefix = f"{prefix} | {display_name}"
    return f"{prefix} | {item.get('status', '')}"


def _render_key_value_grid(rows: list[tuple[str, Any]]) -> None:
    left, right = st.columns(2)
    for idx, (label, value) in enumerate(rows):
        target = left if idx % 2 == 0 else right
        with target:
            st.caption(label)
            text = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value or "-")
            st.write(text)


def _table_columns_frame(columns: Any) -> pd.DataFrame:
    rows = []
    for column in columns if isinstance(columns, list) else []:
        if isinstance(column, dict):
            rows.append(
                {
                    "name": column.get("name", ""),
                    "type": column.get("type", ""),
                    "description": column.get("description", ""),
                }
            )
    return pd.DataFrame(rows)


def render_domain_registration_page(settings: Dict[str, Any]) -> None:
    st.title("도메인 정보 등록")
    st.caption("자연어 도메인 설명을 Main Flow가 읽는 MongoDB domain item 구조로 변환하고 저장합니다.")

    example = """[공정 그룹]
DP,D/P는 WET1, WET2, L/T1, L/T2 공정 그룹을 의미한다.
D/A,DA는 D/A1, D/A2, D/A3, D/A4, D/A5, D/A6 공정 그룹을 의미한다.

[용어/조건]
투입량은 PKG INPUT 공정의 생산 실적으로 OPER_DESC 값이 INPUT인 경우를 말한다.
POP 제품은 MODE가 LP로 시작하고 PKG_TYPE1이 LFBGA, TFBGA, UFBGA, VFBGA, WFBGA 중 하나이며 MCP_SALES_NO 값이 존재하는 경우를 말한다.

[지표]
생산 달성율은 생산량 / 목표량으로 계산하며 생산 데이터와 목표 데이터를 함께 사용한다.
CAPA 대비 생산율은 생산량 / capa_qty로 계산하며 생산 데이터와 CAPA 데이터를 함께 사용한다."""
    _render_example_block("도메인 설명 예시 보기", example, "domain_raw_text")
    if "domain_raw_text" not in st.session_state:
        st.session_state.domain_raw_text = ""

    with st.container(border=True):
        raw_text = st.text_area(
            "등록할 도메인 설명",
            key="domain_raw_text",
            height=150,
            placeholder="예: DP,D/P는 WET1, WET2 공정 그룹을 의미한다.\n예: 생산 달성율은 생산량 / 목표량으로 계산한다.",
        )
        manual_gbn = st.selectbox("분류 방식", options=["auto", *VALID_GBNS], index=0)
        preview_clicked = st.button("작성 내용 검증", type="primary", use_container_width=True)

    if preview_clicked:
        if not raw_text.strip():
            st.warning("등록할 도메인 설명을 입력해주세요.")
            return
        try:
            existing_items = list_domain_items(
                db_name=settings["db_name"],
                collection_name=settings["domain_collection"],
                status="all",
                mongo_uri=settings["mongo_uri"],
            )
            with st.spinner("LLM으로 도메인 항목을 추출하고 기존 항목과 충돌 여부를 확인하는 중입니다."):
                preview = build_domain_preview(
                    raw_text=raw_text,
                    api_key=settings["api_key"],
                    model_name=settings["model_name"],
                    temperature=settings["temperature"],
                    existing_items=existing_items,
                    manual_gbn=manual_gbn,
                )
                validation = validate_domain_items(preview["normalized_domain_items"], existing_items)
                preview["validation"] = validation
                preview["normalized_domain_items"] = validation["normalized_domain_items"]
                st.session_state.domain_preview = preview
        except Exception as exc:
            st.session_state.domain_preview = None
            st.error(f"도메인 검증 실패: {exc}")

    preview = st.session_state.get("domain_preview")
    if not preview:
        return

    validation = preview.get("validation", {})
    items = preview.get("normalized_domain_items", [])
    can_save = bool(validation.get("can_save"))
    st.subheader("처리 결과")
    _render_summary_cards(
        [
            {"label": "추출 항목", "value": f"{len(items)}건", "help": "LLM이 구조화한 도메인 항목 수", "style": "info"},
            {"label": "분류", "value": ", ".join(preview.get("routes", [])), "help": "이번 입력에서 감지한 도메인 유형", "style": "info"},
            {"label": "저장 가능", "value": "가능" if can_save else "확인 필요", "help": "오류가 없으면 저장할 수 있습니다.", "style": "good" if can_save else "warn"},
        ]
    )

    st.subheader("검증 결과")
    _render_issues(validation.get("issues", []))

    st.subheader("추출 항목 미리보기")
    st.dataframe(_domain_items_frame(items), use_container_width=True, hide_index=True)

    with st.expander("정규화 JSON 보기"):
        st.code(_json_dumps(items), language="json")
    with st.expander("LLM Prompt 보기"):
        st.code(preview.get("prompt", ""), language="text")

    if st.button("MongoDB에 도메인 항목 등록", disabled=not can_save, use_container_width=True):
        try:
            saved = save_domain_preview(
                preview,
                db_name=settings["db_name"],
                collection_name=settings["domain_collection"],
                mongo_uri=settings["mongo_uri"],
            )
            if saved.get("saved"):
                st.success(f"{saved.get('saved_count', 0)}개 도메인 항목을 저장했습니다.")
                st.session_state.domain_preview = None
            else:
                st.error("도메인 저장에 실패했습니다.")
                _render_issues([{"severity": "error", "type": "save_error", "message": msg} for msg in saved.get("errors", [])])
        except Exception as exc:
            st.error(f"도메인 저장 실패: {exc}")


def render_table_registration_page(settings: Dict[str, Any]) -> None:
    st.title("테이블 정보 등록")
    st.caption("SQL, DDL, 설명 또는 JSON을 Main Flow의 Table Catalog JSON 형식으로 변환합니다.")

    example = _load_example(
        "table_input_example.txt",
        "생산 데이터\n테이블명: PROD_TABLE\n필수 조건: date\nSQL:\nSELECT WORK_DT, SUM(QTY) AS production FROM PROD_TABLE WHERE WORK_DT = :date GROUP BY WORK_DT",
    )
    _render_example_block("테이블 설명 예시 보기", example, "table_raw_text")
    if "table_raw_text" not in st.session_state:
        st.session_state.table_raw_text = ""

    with st.container(border=True):
        raw_text = st.text_area(
            "등록할 테이블 설명 / SQL / JSON",
            key="table_raw_text",
            height=360,
            placeholder="예: 생산 데이터셋을 등록한다.\ndataset_key는 production이다.\nSQL:\nSELECT ... WHERE WORK_DT = :date",
        )
        input_mode = st.radio(
            "처리 방식",
            options=[AUTO_MODE, FORCE_LLM_MODE, JSON_ONLY_MODE],
            horizontal=True,
        )
        preview_clicked = st.button("Table Catalog 생성/검증", type="primary", use_container_width=True)

    if preview_clicked:
        if not raw_text.strip():
            st.warning("등록할 테이블 설명, SQL 또는 JSON을 입력해주세요.")
            return
        try:
            existing_tables = list_table_items(
                db_name=settings["db_name"],
                collection_name=settings["table_collection"],
                status="all",
                mongo_uri=settings["mongo_uri"],
            )
            if input_mode == JSON_ONLY_MODE:
                parsed = try_parse_table_catalog_text(raw_text)
                if parsed is None:
                    raise ValueError("JSON으로 해석할 수 없습니다. JSON 입력 또는 자동/LLM 모드를 사용하세요.")
                generated = {"table_catalog_raw": parsed, "used_llm": False, "prompt": "", "llm_text": ""}
            else:
                with st.spinner("입력 내용을 Table Catalog JSON으로 변환하는 중입니다."):
                    generated = generate_table_catalog(
                        raw_text=raw_text,
                        api_key=settings["api_key"],
                        model_name=settings["model_name"],
                        temperature=settings["temperature"],
                        existing_table_items=existing_tables,
                        force_llm=input_mode == FORCE_LLM_MODE,
                    )
            validation = normalize_and_validate_table_catalog(generated["table_catalog_raw"], existing_tables)
            preview = {**generated, **validation}
            st.session_state.table_preview = preview
        except Exception as exc:
            st.session_state.table_preview = None
            st.error(f"테이블 검증 실패: {exc}")

    preview = st.session_state.get("table_preview")
    if not preview:
        return

    table_catalog = preview.get("table_catalog", {})
    datasets = table_catalog.get("datasets") if isinstance(table_catalog.get("datasets"), dict) else {}
    can_save = bool(preview.get("can_save"))
    st.subheader("처리 결과")
    _render_summary_cards(
        [
            {"label": "데이터셋", "value": f"{len(datasets)}개", "help": "생성된 dataset 정의 수", "style": "info"},
            {"label": "LLM 처리", "value": "사용" if preview.get("used_llm") else "미사용", "help": "JSON 직접 검증이면 LLM을 사용하지 않습니다.", "style": "info"},
            {"label": "저장 가능", "value": "가능" if can_save else "확인 필요", "help": "오류가 없으면 저장할 수 있습니다.", "style": "good" if can_save else "warn"},
        ]
    )

    st.subheader("검증 결과")
    _render_issues(preview.get("issues", []))

    if datasets:
        st.subheader("데이터셋 미리보기")
        rows = []
        for key, dataset in datasets.items():
            rows.append(
                {
                    "dataset_key": key,
                    "display_name": dataset.get("display_name", ""),
                    "db_key": dataset.get("db_key", ""),
                    "tool_name": dataset.get("tool_name", ""),
                    "required_params": ", ".join(dataset.get("required_params", [])),
                    "keywords": ", ".join(dataset.get("keywords", [])),
                    "sql_chars": len(dataset.get("sql_template", "")),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Main Flow 붙여넣기용 JSON")
    st.text_area("Table Catalog JSON", value=table_catalog_json_text(table_catalog), height=360)

    with st.expander("LLM Prompt 보기"):
        st.code(preview.get("prompt", ""), language="text")

    if st.button("MongoDB에 테이블 정의 등록", disabled=not can_save, use_container_width=True):
        try:
            saved = save_table_preview(
                preview,
                db_name=settings["db_name"],
                collection_name=settings["table_collection"],
                mongo_uri=settings["mongo_uri"],
            )
            if saved.get("saved"):
                st.success(f"{saved.get('saved_count', 0)}개 테이블 정의를 저장했습니다.")
                st.session_state.table_preview = None
            else:
                st.error("테이블 정의 저장에 실패했습니다.")
                _render_issues([{"severity": "error", "type": "save_error", "message": msg} for msg in saved.get("errors", [])])
        except Exception as exc:
            st.error(f"테이블 정의 저장 실패: {exc}")


def render_domain_lookup_page(settings: Dict[str, Any]) -> None:
    st.title("도메인 정보 조회")
    st.caption("MongoDB에 저장된 domain item을 유형별로 확인하고, 선택한 항목의 상세 정보를 봅니다.")

    filter_col, gbn_col = st.columns([1, 1])
    with filter_col:
        status = st.selectbox("상태 필터", options=["active", "review_required", "deleted", "all"], index=0, key="domain_lookup_status")
    with gbn_col:
        gbn_filter = st.selectbox("도메인 유형", options=["all", *VALID_GBNS], index=0, key="domain_lookup_gbn")

    try:
        domain_items = list_domain_items(
            db_name=settings["db_name"],
            collection_name=settings["domain_collection"],
            status=status,
            mongo_uri=settings["mongo_uri"],
        )
    except Exception as exc:
        st.error(f"도메인 항목 조회 실패: {exc}")
        return

    if gbn_filter != "all":
        domain_items = [item for item in domain_items if item.get("gbn") == gbn_filter]

    gbn_counts: Dict[str, int] = {}
    for item in domain_items:
        gbn = str(item.get("gbn") or "unknown")
        gbn_counts[gbn] = gbn_counts.get(gbn, 0) + 1

    _render_summary_cards(
        [
            {"label": "조회 항목", "value": f"{len(domain_items)}건", "help": "현재 필터에 해당하는 domain item", "style": "info"},
            {"label": "도메인 유형", "value": f"{len(gbn_counts)}개", "help": ", ".join(sorted(gbn_counts)) or "-", "style": "info"},
            {"label": "저장 위치", "value": settings["domain_collection"], "help": "MongoDB collection", "style": "info"},
        ]
    )

    st.subheader("도메인 항목 목록")
    st.dataframe(_domain_items_frame(domain_items), use_container_width=True, hide_index=True)

    if not domain_items:
        st.info("조회된 도메인 항목이 없습니다.")
        return

    st.subheader("상세 정보")
    selected_label = st.selectbox(
        "상세 조회 항목",
        options=[_domain_detail_label(item) for item in domain_items],
        key="domain_detail_item",
    )
    selected_index = [_domain_detail_label(item) for item in domain_items].index(selected_label)
    selected = domain_items[selected_index]
    payload = selected.get("payload") if isinstance(selected.get("payload"), dict) else {}

    with st.container(border=True):
        _render_key_value_grid(
            [
                ("유형", selected.get("gbn", "")),
                ("Key", selected.get("key", "")),
                ("상태", selected.get("status", "")),
                ("표시명", payload.get("display_name", "")),
                ("Alias", payload.get("aliases", [])),
                ("Keyword", payload.get("keywords", [])),
                ("생성일", selected.get("created_at", "")),
                ("수정일", selected.get("updated_at", "")),
            ]
        )

    payload_tab, source_tab, index_tab, raw_tab = st.tabs(["Payload", "원문", "Index 정보", "전체 Document"])
    with payload_tab:
        st.code(_json_dumps(payload), language="json")
    with source_tab:
        st.text_area("source_text", value=str(selected.get("source_text") or ""), height=150, disabled=True)
        warnings = selected.get("warnings") if isinstance(selected.get("warnings"), list) else []
        if warnings:
            st.caption("warnings")
            st.code("\n".join(str(item) for item in warnings), language="text")
    with index_tab:
        st.code(
            _json_dumps(
                {
                    "normalized_aliases": selected.get("normalized_aliases", []),
                    "normalized_keywords": selected.get("normalized_keywords", []),
                    "source_note_id": selected.get("source_note_id", ""),
                }
            ),
            language="json",
        )
    with raw_tab:
        st.code(_json_dumps(selected), language="json")

    with st.expander("삭제", expanded=False):
        st.warning("삭제하면 status가 deleted로 변경되어 Main Flow에서 더 이상 active 도메인으로 불러오지 않습니다.")
        confirm = st.checkbox(
            f"{selected.get('gbn')}:{selected.get('key')} 항목 삭제를 확인합니다.",
            key=f"confirm_delete_domain_{selected.get('gbn')}_{selected.get('key')}",
        )
        if st.button("선택한 도메인 항목 삭제", disabled=not confirm, use_container_width=True):
            try:
                result = soft_delete_domain_item(
                    str(selected.get("gbn") or ""),
                    str(selected.get("key") or ""),
                    db_name=settings["db_name"],
                    collection_name=settings["domain_collection"],
                    mongo_uri=settings["mongo_uri"],
                )
                if result.get("deleted"):
                    st.success("도메인 항목을 삭제 상태로 변경했습니다.")
                    st.rerun()
                else:
                    st.error("삭제할 도메인 항목을 찾지 못했습니다.")
            except Exception as exc:
                st.error(f"도메인 항목 삭제 실패: {exc}")


def render_table_lookup_page(settings: Dict[str, Any]) -> None:
    st.title("테이블 정보 조회")
    st.caption("MongoDB에 저장된 table catalog item을 확인하고, SQL/컬럼/키워드 상세 정보를 봅니다.")

    status = st.selectbox("상태 필터", options=["active", "review_required", "deleted", "all"], index=0, key="table_lookup_status")

    try:
        table_items = list_table_items(
            db_name=settings["db_name"],
            collection_name=settings["table_collection"],
            status=status,
            mongo_uri=settings["mongo_uri"],
        )
    except Exception as exc:
        st.error(f"테이블 정의 조회 실패: {exc}")
        return

    oracle_count = sum(1 for item in table_items if item.get("source_type") == "oracle")
    sql_count = sum(1 for item in table_items if str(item.get("sql_template") or "").strip())
    _render_summary_cards(
        [
            {"label": "조회 항목", "value": f"{len(table_items)}건", "help": "현재 필터에 해당하는 table item", "style": "info"},
            {"label": "Oracle Dataset", "value": f"{oracle_count}건", "help": "source_type이 oracle인 항목", "style": "info"},
            {"label": "SQL 보유", "value": f"{sql_count}건", "help": "sql_template이 등록된 항목", "style": "info"},
        ]
    )

    st.subheader("테이블 정의 목록")
    st.dataframe(_table_items_frame(table_items), use_container_width=True, hide_index=True)

    if not table_items:
        st.info("조회된 테이블 정의가 없습니다.")
        return

    st.subheader("상세 정보")
    selected_label = st.selectbox(
        "상세 조회 항목",
        options=[_table_detail_label(item) for item in table_items],
        key="table_detail_item",
    )
    selected_index = [_table_detail_label(item) for item in table_items].index(selected_label)
    selected = table_items[selected_index]

    with st.container(border=True):
        _render_key_value_grid(
            [
                ("Dataset Key", selected.get("dataset_key", "")),
                ("표시명", selected.get("display_name", "")),
                ("상태", selected.get("status", "")),
                ("DB Key", selected.get("db_key", "")),
                ("Tool Name", selected.get("tool_name", "")),
                ("Source Type", selected.get("source_type", "")),
                ("필수 Parameter", selected.get("required_params", [])),
                ("Table Name", selected.get("table_name", "")),
                ("생성일", selected.get("created_at", "")),
                ("수정일", selected.get("updated_at", "")),
            ]
        )

    sql_tab, column_tab, keyword_tab, raw_tab = st.tabs(["SQL", "Columns", "Keywords", "전체 Document"])
    with sql_tab:
        sql = str(selected.get("sql_template") or "")
        if sql.strip():
            st.code(sql, language="sql")
        else:
            st.info("등록된 SQL이 없습니다.")
        st.caption("bind_params")
        st.code(_json_dumps(selected.get("bind_params", {})), language="json")
    with column_tab:
        columns = selected.get("columns") if isinstance(selected.get("columns"), list) else []
        st.dataframe(_table_columns_frame(columns), use_container_width=True, hide_index=True)
    with keyword_tab:
        st.caption("keywords")
        st.code("\n".join(str(item) for item in selected.get("keywords", []) or []), language="text")
        st.caption("question_examples")
        st.code("\n".join(str(item) for item in selected.get("question_examples", []) or []), language="text")
        st.caption("description")
        st.text_area("description", value=str(selected.get("description") or ""), height=120, disabled=True)
    with raw_tab:
        st.code(_json_dumps(selected), language="json")

    with st.expander("삭제", expanded=False):
        st.warning("삭제하면 status가 deleted로 변경됩니다. 현재 Main Flow는 테이블 정보를 JSON 입력으로 사용하지만, MongoDB 조회 구조로 전환하면 deleted 항목은 제외할 수 있습니다.")
        confirm = st.checkbox(
            f"{selected.get('dataset_key')} 테이블 정의 삭제를 확인합니다.",
            key=f"confirm_delete_table_{selected.get('dataset_key')}",
        )
        if st.button("선택한 테이블 정의 삭제", disabled=not confirm, use_container_width=True):
            try:
                result = soft_delete_table_item(
                    str(selected.get("dataset_key") or ""),
                    db_name=settings["db_name"],
                    collection_name=settings["table_collection"],
                    mongo_uri=settings["mongo_uri"],
                )
                if result.get("deleted"):
                    st.success("테이블 정의를 삭제 상태로 변경했습니다.")
                    st.rerun()
                else:
                    st.error("삭제할 테이블 정의를 찾지 못했습니다.")
            except Exception as exc:
                st.error(f"테이블 정의 삭제 실패: {exc}")


def main() -> None:
    st.set_page_config(page_title="Manufacturing Registry", layout="wide")
    _inject_style()
    settings = _settings()
    page = _render_sidebar(settings)

    if page == "도메인 정보 등록":
        render_domain_registration_page(settings)
    elif page == "테이블 정보 등록":
        render_table_registration_page(settings)
    elif page == "도메인 정보 조회":
        render_domain_lookup_page(settings)
    else:
        render_table_lookup_page(settings)


if __name__ == "__main__":
    main()
