from __future__ import annotations

# VISIBLE_STANDALONE_RUNTIME: visible per-node standalone code with no hidden source bundle.

# ---- visible runtime: component_base ----
"""Helpers shared by standalone Langflow custom components.

This package is meant to be copied into a Langflow custom-component folder, so
the wrappers below keep the nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""
from dataclasses import dataclass as __lf_component_base__dataclass
from typing import Any as __lf_component_base__Any, Dict as __lf_component_base__Dict

def __lf_component_base___build_simple_data(payload: __lf_component_base__Dict[str, __lf_component_base__Any], text: str | None=None):

    @__lf_component_base__dataclass
    class SimpleData:
        data: __lf_component_base__Dict[str, __lf_component_base__Any]
        text: str | None = None
    return SimpleData(data=payload, text=text)
try:
    from lfx.custom.custom_component.component import Component as __lf_component_base__Component
    from lfx.io import DataInput as __lf_component_base__DataInput, MessageInput as __lf_component_base__MessageInput, MessageTextInput as __lf_component_base__MessageTextInput, MultilineInput as __lf_component_base__MultilineInput, Output as __lf_component_base__Output
    from lfx.schema import Data as __lf_component_base__Data
except Exception:
    try:
        from langflow.custom import Component as __lf_component_base__Component
        from langflow.io import DataInput as __lf_component_base__DataInput, MessageInput as __lf_component_base__MessageInput, MessageTextInput as __lf_component_base__MessageTextInput, MultilineInput as __lf_component_base__MultilineInput, Output as __lf_component_base__Output
        from langflow.schema import Data as __lf_component_base__Data
    except Exception:

        class __lf_component_base__Component:
            display_name = ''
            description = ''
            documentation = ''
            icon = ''
            name = ''
            inputs = []
            outputs = []
            status = ''

        @__lf_component_base__dataclass
        class __lf_component_base___Input:
            name: str
            display_name: str
            info: str = ''
            value: __lf_component_base__Any = None
            tool_mode: bool = False
            advanced: bool = False

        @__lf_component_base__dataclass
        class __lf_component_base__Output:
            name: str
            display_name: str
            method: str
            group_outputs: bool = False
            types: list[str] | None = None
            selected: str | None = None

        def __lf_component_base__MessageTextInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        def __lf_component_base__MultilineInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        def __lf_component_base__DataInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        def __lf_component_base__MessageInput(**kwargs):
            return __lf_component_base___Input(**kwargs)

        class __lf_component_base__Data:

            def __init__(self, data: __lf_component_base__Dict[str, __lf_component_base__Any] | None=None, text: str | None=None):
                self.data = data or {}
                self.text = text

def __lf_component_base__make_data(payload: __lf_component_base__Dict[str, __lf_component_base__Any], text: str | None=None):
    """Return a Data-like object in both Langflow and local test environments."""
    try:
        return __lf_component_base__Data(data=payload, text=text)
    except TypeError:
        try:
            return __lf_component_base__Data(payload)
        except Exception:
            return __lf_component_base___build_simple_data(payload, text=text)

def __lf_component_base__make_branch_data(active: bool, payload: __lf_component_base__Dict[str, __lf_component_base__Any], text: str | None=None):
    """Emit data only for the active branch output."""
    if not active:
        return None
    return __lf_component_base__make_data(payload, text=text)

def __lf_component_base__read_data_payload(value: __lf_component_base__Any) -> __lf_component_base__Dict[str, __lf_component_base__Any]:
    """Normalize Langflow Data, plain dict, or None into a regular dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, 'data', None)
    if isinstance(data, dict):
        return data
    if hasattr(value, 'dict'):
        try:
            result = value.dict()
            if isinstance(result, dict):
                return result
        except Exception:
            return {}
    return {}

def __lf_component_base__read_state_payload(value: __lf_component_base__Any) -> __lf_component_base__Dict[str, __lf_component_base__Any]:
    """Read a Langflow payload and unwrap the nested ``state`` field when present."""
    payload = __lf_component_base__read_data_payload(value)
    state = payload.get('state')
    if isinstance(state, dict):
        return state
    return payload if isinstance(payload, dict) else {}

# ---- visible runtime: _runtime.shared.filter_utils ----
import re as __lf_runtime_shared_filter_utils__re
import unicodedata as __lf_runtime_shared_filter_utils__unicodedata
from typing import Any as __lf_runtime_shared_filter_utils__Any, Iterable as __lf_runtime_shared_filter_utils__Iterable

def __lf_runtime_shared_filter_utils__normalize_text(value: __lf_runtime_shared_filter_utils__Any) -> str:
    text = __lf_runtime_shared_filter_utils__unicodedata.normalize('NFKC', str(value or ''))
    return __lf_runtime_shared_filter_utils__re.sub('\\s+', ' ', text).strip().lower()

def __lf_runtime_shared_filter_utils__contains_any_keyword(text: str, keywords: __lf_runtime_shared_filter_utils__Iterable[str]) -> bool:
    normalized = __lf_runtime_shared_filter_utils__normalize_text(text)
    return any((__lf_runtime_shared_filter_utils__normalize_text(keyword) in normalized for keyword in keywords))

# ---- visible runtime: _runtime.domain.knowledge ----
"""제조 도메인 지식과 파라미터 추출 스펙을 모아 둔 파일."""
from typing import Dict as __lf_runtime_domain_knowledge__Dict, List as __lf_runtime_domain_knowledge__List, Set as __lf_runtime_domain_knowledge__Set
__lf_runtime_domain_knowledge__FILTER_FIELDS = {'date': {'field_name': 'WORK_DT', 'description': '작업일자 (YYYYMMDD 형식)'}, 'process': {'field_name': 'OPER_NAME', 'description': '제조 공정명 또는 공정 그룹'}, 'oper_num': {'field_name': 'OPER_NUM', 'description': '공정번호. 공정과 매핑되는 4자리 숫자 코드'}, 'pkg_type1': {'field_name': 'PKG_TYPE1', 'description': '패키지 기술 유형 (예: FCBGA, LFBGA)'}, 'pkg_type2': {'field_name': 'PKG_TYPE2', 'description': '스택 수/구성 유형 (예: ODP, 16DP, SDP)'}, 'mode': {'field_name': 'MODE', 'description': '제품 모드 (예: DDR4, DDR5, LPDDR5)'}, 'den': {'field_name': 'DEN', 'description': '제품 용량/Density (예: 256G, 512G, 1T)'}, 'tech': {'field_name': 'TECH', 'description': '기술 유형 (예: LC, FO, FC)'}, 'lead': {'field_name': 'LEAD', 'description': 'Ball 또는 Lead의 개수'}, 'mcp_no': {'field_name': 'MCP_NO', 'description': 'MCP 제품 코드'}}
__lf_runtime_domain_knowledge__PROCESS_GROUPS = {'DP': {'group_name': 'DP', 'synonyms': ['DP', 'D/P'], 'actual_values': ['WET1', 'WET2', 'L/T1', 'L/T2', 'B/G1', 'B/G2', 'H/S1', 'H/S2', 'W/S1', 'W/S2', 'WSD1', 'WSD2', 'WEC1', 'WEC2', 'WLS1', 'WLS2', 'WVI', 'UV', 'C/C1'], 'description': '전공정 DP 그룹'}, 'WET': {'group_name': 'WET', 'synonyms': ['WET'], 'actual_values': ['WET1', 'WET2'], 'description': 'WET 세부 공정 그룹'}, 'LT': {'group_name': 'LT', 'synonyms': ['LT', 'L/T'], 'actual_values': ['L/T1', 'L/T2'], 'description': 'L/T 세부 공정 그룹'}, 'BG': {'group_name': 'BG', 'synonyms': ['BG', 'B/G'], 'actual_values': ['B/G1', 'B/G2'], 'description': 'B/G 세부 공정 그룹'}, 'HS': {'group_name': 'HS', 'synonyms': ['HS', 'H/S'], 'actual_values': ['H/S1', 'H/S2'], 'description': 'H/S 세부 공정 그룹'}, 'WS': {'group_name': 'WS', 'synonyms': ['WS', 'W/S'], 'actual_values': ['W/S1', 'W/S2'], 'description': 'W/S 세부 공정 그룹'}, 'DA': {'group_name': 'D/A', 'synonyms': ['D/A', 'DA', 'Die Attach', 'DIE ATTACH', '다이어태치', '다이본딩'], 'actual_values': ['D/A1', 'D/A2', 'D/A3', 'D/A4', 'D/A5', 'D/A6'], 'description': 'Die Attach 공정 그룹'}, 'PCO': {'group_name': 'PCO', 'synonyms': ['PCO'], 'actual_values': ['PCO1', 'PCO2', 'PCO3', 'PCO4', 'PCO5', 'PCO6'], 'description': 'PCO 공정 그룹'}, 'DC': {'group_name': 'D/C', 'synonyms': ['D/C', 'DC'], 'actual_values': ['D/C1', 'D/C2', 'D/C3', 'D/C4'], 'description': 'D/C 공정 그룹'}, 'DI': {'group_name': 'D/I', 'synonyms': ['D/I', 'DI'], 'actual_values': ['D/I'], 'description': 'D/I 단일 공정'}, 'DS': {'group_name': 'D/S', 'synonyms': ['D/S', 'DS'], 'actual_values': ['D/S1'], 'description': 'D/S 공정 그룹'}, 'FCB': {'group_name': 'FCB', 'synonyms': ['FCB', 'Flip Chip', '플립칩'], 'actual_values': ['FCB1', 'FCB2', 'FCB/H'], 'description': 'FCB 공정 그룹'}, 'FCBH': {'group_name': 'FCB/H', 'synonyms': ['FCB/H', 'FCBH'], 'actual_values': ['FCB/H'], 'description': 'FCB/H 단일 공정'}, 'BM': {'group_name': 'B/M', 'synonyms': ['B/M', 'BN', '비엠'], 'actual_values': ['B/M'], 'description': 'B/M 단일 공정'}, 'PC': {'group_name': 'P/C', 'synonyms': ['P/C', 'PC'], 'actual_values': ['P/C1', 'P/C2', 'P/C3', 'P/C4', 'P/C5'], 'description': 'P/C 공정 그룹'}, 'WB': {'group_name': 'W/B', 'synonyms': ['W/B', 'WB', 'Wire Bonding', '와이어본딩'], 'actual_values': ['W/B1', 'W/B2', 'W/B3', 'W/B4', 'W/B5', 'W/B6'], 'description': 'Wire Bonding 공정 그룹'}, 'QCSPC': {'group_name': 'QCSPC', 'synonyms': ['QCSPC'], 'actual_values': ['QCSPC1', 'QCSPC2', 'QCSPC3', 'QCSPC4'], 'description': 'QCSPC 공정 그룹'}, 'SAT': {'group_name': 'SAT', 'synonyms': ['SAT'], 'actual_values': ['SAT1', 'SAT2'], 'description': 'SAT 공정 그룹'}, 'PL': {'group_name': 'P/L', 'synonyms': ['P/L', 'PL'], 'actual_values': ['PLH'], 'description': 'P/L 단일 공정'}}
__lf_runtime_domain_knowledge__LITERAL_PROCESSES = ['WVI', 'DVI', 'BBMS', 'AVI', 'MDVI', 'MDTI', 'QCSAT', 'LMDI', 'DIC', 'EVI']

def __lf_runtime_domain_knowledge___dedupe_processes() -> __lf_runtime_domain_knowledge__List[str]:
    ordered: __lf_runtime_domain_knowledge__List[str] = []
    for group in __lf_runtime_domain_knowledge__PROCESS_GROUPS.values():
        for process_name in group['actual_values']:
            if process_name not in ordered:
                ordered.append(process_name)
    for process_name in __lf_runtime_domain_knowledge__LITERAL_PROCESSES:
        if process_name not in ordered:
            ordered.append(process_name)
    return ordered
__lf_runtime_domain_knowledge__INDIVIDUAL_PROCESSES = __lf_runtime_domain_knowledge___dedupe_processes()
__lf_runtime_domain_knowledge__PROCESS_SPECS = [{'family': 'DP', 'OPER_NAME': 'WET1', '라인': 'DP-L1', 'OPER_NUM': '1000'}, {'family': 'DP', 'OPER_NAME': 'WET2', '라인': 'DP-L1', 'OPER_NUM': '1005'}, {'family': 'DP', 'OPER_NAME': 'L/T1', '라인': 'DP-L2', 'OPER_NUM': '1010'}, {'family': 'DP', 'OPER_NAME': 'L/T2', '라인': 'DP-L2', 'OPER_NUM': '1015'}, {'family': 'DP', 'OPER_NAME': 'B/G1', '라인': 'DP-L3', 'OPER_NUM': '1020'}, {'family': 'DP', 'OPER_NAME': 'B/G2', '라인': 'DP-L3', 'OPER_NUM': '1025'}, {'family': 'DP', 'OPER_NAME': 'H/S1', '라인': 'DP-L4', 'OPER_NUM': '1030'}, {'family': 'DP', 'OPER_NAME': 'H/S2', '라인': 'DP-L4', 'OPER_NUM': '1035'}, {'family': 'DP', 'OPER_NAME': 'W/S1', '라인': 'DP-L5', 'OPER_NUM': '1040'}, {'family': 'DP', 'OPER_NAME': 'W/S2', '라인': 'DP-L5', 'OPER_NUM': '1045'}, {'family': 'DP', 'OPER_NAME': 'WSD1', '라인': 'DP-L6', 'OPER_NUM': '1050'}, {'family': 'DP', 'OPER_NAME': 'WSD2', '라인': 'DP-L6', 'OPER_NUM': '1055'}, {'family': 'DP', 'OPER_NAME': 'WEC1', '라인': 'DP-L7', 'OPER_NUM': '1060'}, {'family': 'DP', 'OPER_NAME': 'WEC2', '라인': 'DP-L7', 'OPER_NUM': '1065'}, {'family': 'DP', 'OPER_NAME': 'WLS1', '라인': 'DP-L8', 'OPER_NUM': '1070'}, {'family': 'DP', 'OPER_NAME': 'WLS2', '라인': 'DP-L8', 'OPER_NUM': '1075'}, {'family': 'DP', 'OPER_NAME': 'WVI', '라인': 'DP-L9', 'OPER_NUM': '1080'}, {'family': 'DP', 'OPER_NAME': 'UV', '라인': 'DP-L9', 'OPER_NUM': '1085'}, {'family': 'DP', 'OPER_NAME': 'C/C1', '라인': 'DP-L9', 'OPER_NUM': '1090'}, {'family': 'DA', 'OPER_NAME': 'D/A1', '라인': 'DA-L1', 'OPER_NUM': '2000'}, {'family': 'DA', 'OPER_NAME': 'D/A2', '라인': 'DA-L1', 'OPER_NUM': '2010'}, {'family': 'DA', 'OPER_NAME': 'D/A3', '라인': 'DA-L2', 'OPER_NUM': '2020'}, {'family': 'DA', 'OPER_NAME': 'D/A4', '라인': 'DA-L2', 'OPER_NUM': '2030'}, {'family': 'DA', 'OPER_NAME': 'D/A5', '라인': 'DA-L3', 'OPER_NUM': '2040'}, {'family': 'DA', 'OPER_NAME': 'D/A6', '라인': 'DA-L3', 'OPER_NUM': '2050'}, {'family': 'PCO', 'OPER_NAME': 'PCO1', '라인': 'PCO-L1', 'OPER_NUM': '2100'}, {'family': 'PCO', 'OPER_NAME': 'PCO2', '라인': 'PCO-L1', 'OPER_NUM': '2110'}, {'family': 'PCO', 'OPER_NAME': 'PCO3', '라인': 'PCO-L2', 'OPER_NUM': '2120'}, {'family': 'PCO', 'OPER_NAME': 'PCO4', '라인': 'PCO-L2', 'OPER_NUM': '2130'}, {'family': 'PCO', 'OPER_NAME': 'PCO5', '라인': 'PCO-L3', 'OPER_NUM': '2140'}, {'family': 'PCO', 'OPER_NAME': 'PCO6', '라인': 'PCO-L3', 'OPER_NUM': '2150'}, {'family': 'DC', 'OPER_NAME': 'D/C1', '라인': 'DC-L1', 'OPER_NUM': '2200'}, {'family': 'DC', 'OPER_NAME': 'D/C2', '라인': 'DC-L1', 'OPER_NUM': '2210'}, {'family': 'DC', 'OPER_NAME': 'D/C3', '라인': 'DC-L2', 'OPER_NUM': '2220'}, {'family': 'DC', 'OPER_NAME': 'D/C4', '라인': 'DC-L2', 'OPER_NUM': '2230'}, {'family': 'DI', 'OPER_NAME': 'D/I', '라인': 'DI-L1', 'OPER_NUM': '2300'}, {'family': 'DS', 'OPER_NAME': 'D/S1', '라인': 'DS-L1', 'OPER_NUM': '2400'}, {'family': 'FCB', 'OPER_NAME': 'FCB1', '라인': 'FCB-L1', 'OPER_NUM': '2500'}, {'family': 'FCB', 'OPER_NAME': 'FCB2', '라인': 'FCB-L1', 'OPER_NUM': '2510'}, {'family': 'FCB', 'OPER_NAME': 'FCB/H', '라인': 'FCB-L2', 'OPER_NUM': '2520'}, {'family': 'BM', 'OPER_NAME': 'B/M', '라인': 'BM-L1', 'OPER_NUM': '2600'}, {'family': 'PC', 'OPER_NAME': 'P/C1', '라인': 'PC-L1', 'OPER_NUM': '2700'}, {'family': 'PC', 'OPER_NAME': 'P/C2', '라인': 'PC-L1', 'OPER_NUM': '2710'}, {'family': 'PC', 'OPER_NAME': 'P/C3', '라인': 'PC-L2', 'OPER_NUM': '2720'}, {'family': 'PC', 'OPER_NAME': 'P/C4', '라인': 'PC-L2', 'OPER_NUM': '2730'}, {'family': 'PC', 'OPER_NAME': 'P/C5', '라인': 'PC-L3', 'OPER_NUM': '2740'}, {'family': 'WB', 'OPER_NAME': 'W/B1', '라인': 'WB-L1', 'OPER_NUM': '3000'}, {'family': 'WB', 'OPER_NAME': 'W/B2', '라인': 'WB-L1', 'OPER_NUM': '3010'}, {'family': 'WB', 'OPER_NAME': 'W/B3', '라인': 'WB-L2', 'OPER_NUM': '3020'}, {'family': 'WB', 'OPER_NAME': 'W/B4', '라인': 'WB-L2', 'OPER_NUM': '3030'}, {'family': 'WB', 'OPER_NAME': 'W/B5', '라인': 'WB-L3', 'OPER_NUM': '3040'}, {'family': 'WB', 'OPER_NAME': 'W/B6', '라인': 'WB-L3', 'OPER_NUM': '3050'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC1', '라인': 'QC-L1', 'OPER_NUM': '3100'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC2', '라인': 'QC-L1', 'OPER_NUM': '3110'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC3', '라인': 'QC-L2', 'OPER_NUM': '3120'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC4', '라인': 'QC-L2', 'OPER_NUM': '3130'}, {'family': 'SAT', 'OPER_NAME': 'SAT1', '라인': 'SAT-L1', 'OPER_NUM': '3200'}, {'family': 'SAT', 'OPER_NAME': 'SAT2', '라인': 'SAT-L1', 'OPER_NUM': '3210'}, {'family': 'PL', 'OPER_NAME': 'PLH', '라인': 'PL-L1', 'OPER_NUM': '3300'}, {'family': 'ETC', 'OPER_NAME': 'DVI', '라인': 'ETC-L1', 'OPER_NUM': '3400'}, {'family': 'ETC', 'OPER_NAME': 'BBMS', '라인': 'ETC-L1', 'OPER_NUM': '3410'}, {'family': 'ETC', 'OPER_NAME': 'AVI', '라인': 'ETC-L2', 'OPER_NUM': '3420'}, {'family': 'ETC', 'OPER_NAME': 'MDVI', '라인': 'ETC-L2', 'OPER_NUM': '3430'}, {'family': 'ETC', 'OPER_NAME': 'MDTI', '라인': 'ETC-L3', 'OPER_NUM': '3440'}, {'family': 'ETC', 'OPER_NAME': 'QCSAT', '라인': 'ETC-L3', 'OPER_NUM': '3450'}, {'family': 'ETC', 'OPER_NAME': 'LMDI', '라인': 'ETC-L4', 'OPER_NUM': '3460'}, {'family': 'ETC', 'OPER_NAME': 'DIC', '라인': 'ETC-L4', 'OPER_NUM': '3470'}, {'family': 'ETC', 'OPER_NAME': 'EVI', '라인': 'ETC-L5', 'OPER_NUM': '3480'}, {'family': 'ETC', 'OPER_NAME': 'INPUT', '라인': 'ETC-L5', 'OPER_NUM': '3490'}]
__lf_runtime_domain_knowledge__PROCESS_GROUP_SYNONYMS = {group_id: list(group['synonyms']) for group_id, group in __lf_runtime_domain_knowledge__PROCESS_GROUPS.items()}
__lf_runtime_domain_knowledge__PROCESS_OPER_NUM_MAP = {spec['OPER_NAME']: spec['OPER_NUM'] for spec in __lf_runtime_domain_knowledge__PROCESS_SPECS}
__lf_runtime_domain_knowledge__PRODUCTS = [{'MODE': 'DDR4', 'DEN': '256G', 'TECH': 'LC', 'LEAD': '320', 'MCP_NO': 'A-410A', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'SDP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR4', 'DEN': '512G', 'TECH': 'LC', 'LEAD': '360', 'MCP_NO': 'A-421I', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': 'ODP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR5', 'DEN': '512G', 'TECH': 'FC', 'LEAD': '420', 'MCP_NO': 'A-587N', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': '16DP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR5', 'DEN': '256G', 'TECH': 'FC', 'LEAD': '400', 'MCP_NO': 'A-553P', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'SDP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR5', 'DEN': '1T', 'TECH': 'FC', 'LEAD': '480', 'MCP_NO': 'A-612B', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': 'ODP', 'TSV_DIE_TYP': 'TSV'}, {'MODE': 'LPDDR5', 'DEN': '512G', 'TECH': 'FO', 'LEAD': '560', 'MCP_NO': 'A-7301', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'SDP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'LPDDR5', 'DEN': '256G', 'TECH': 'FO', 'LEAD': '520', 'MCP_NO': 'A-701O', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'ODP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'LPDDR5', 'DEN': '1T', 'TECH': 'FO', 'LEAD': '640', 'MCP_NO': 'A-811V', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': '16DP', 'TSV_DIE_TYP': 'TSV'}, {'MODE': 'DDR4', 'DEN': '1T', 'TECH': 'LC', 'LEAD': '380', 'MCP_NO': 'A-455V', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': '16DP', 'TSV_DIE_TYP': 'STD'}]
__lf_runtime_domain_knowledge__ALL_PROCESS_FAMILIES: __lf_runtime_domain_knowledge__Set[str] = {spec['family'] for spec in __lf_runtime_domain_knowledge__PROCESS_SPECS}
__lf_runtime_domain_knowledge__PRODUCT_TECH_FAMILY: __lf_runtime_domain_knowledge__Dict[str, __lf_runtime_domain_knowledge__Set[str]] = {'LC': set(__lf_runtime_domain_knowledge__ALL_PROCESS_FAMILIES), 'FO': set(__lf_runtime_domain_knowledge__ALL_PROCESS_FAMILIES), 'FC': set(__lf_runtime_domain_knowledge__ALL_PROCESS_FAMILIES)}
__lf_runtime_domain_knowledge__TECH_GROUPS = {'LC': {'synonyms': ['LC', '엘씨', 'LC제품', '엘시'], 'actual_values': ['LC'], 'description': 'LC 기술 유형'}, 'FO': {'synonyms': ['FO', '팬아웃', 'FO제품', 'fan-out', 'Fan-Out', '에프오'], 'actual_values': ['FO'], 'description': 'Fan-Out 기술 유형'}, 'FC': {'synonyms': ['FC', '플립칩', 'FC제품', '에프씨'], 'actual_values': ['FC'], 'description': 'Flip Chip 기술 유형'}}
__lf_runtime_domain_knowledge__MODE_GROUPS = {'DDR4': {'synonyms': ['DDR4', '디디알4', 'DDR 4'], 'actual_values': ['DDR4'], 'description': 'DDR4 메모리'}, 'DDR5': {'synonyms': ['DDR5', '디디알5', 'DDR 5'], 'actual_values': ['DDR5'], 'description': 'DDR5 메모리'}, 'LPDDR5': {'synonyms': ['LPDDR5', 'LP DDR5', '엘피디디알5', 'LP5', '저전력DDR5'], 'actual_values': ['LPDDR5'], 'description': '저전력 DDR5 메모리'}}
__lf_runtime_domain_knowledge__DEN_GROUPS = {'256G': {'synonyms': ['256G', '256기가', '256Gb', '256gb'], 'actual_values': ['256G'], 'description': '256Gb 용량'}, '512G': {'synonyms': ['512G', '512기가', '512Gb', '512gb'], 'actual_values': ['512G'], 'description': '512Gb 용량'}, '1T': {'synonyms': ['1T', '1테라', '1Tb', '1tb', '1TB'], 'actual_values': ['1T'], 'description': '1Tb 용량'}}
__lf_runtime_domain_knowledge__PKG_TYPE1_GROUPS = {'FCBGA': {'synonyms': ['FCBGA', 'fcbga'], 'actual_values': ['FCBGA'], 'description': 'FCBGA 패키지 타입'}, 'LFBGA': {'synonyms': ['LFBGA', 'lfbga'], 'actual_values': ['LFBGA'], 'description': 'LFBGA 패키지 타입'}}
__lf_runtime_domain_knowledge__PKG_TYPE2_GROUPS = {'ODP': {'synonyms': ['ODP', 'odp'], 'actual_values': ['ODP'], 'description': 'ODP 스택 타입'}, '16DP': {'synonyms': ['16DP', '16dp'], 'actual_values': ['16DP'], 'description': '16DP 스택 타입'}, 'SDP': {'synonyms': ['SDP', 'sdp'], 'actual_values': ['SDP'], 'description': 'SDP 스택 타입'}}
__lf_runtime_domain_knowledge__SPECIAL_PRODUCT_ALIASES = {'HBM_OR_3DS': ['hbm제품', 'hbm자재', 'hbm', '3ds', '3ds제품'], 'AUTO_PRODUCT': ['auto향', '오토향', '차량향', 'automotive']}
__lf_runtime_domain_knowledge__SPECIAL_PRODUCT_KEYWORD_RULES = [{'target_value': 'HBM_OR_3DS', 'aliases': ['HBM_OR_3DS', 'HBM/3DS', *__lf_runtime_domain_knowledge__SPECIAL_PRODUCT_ALIASES['HBM_OR_3DS']]}, {'target_value': 'AUTO_PRODUCT', 'aliases': ['AUTO_PRODUCT', 'AUTO', *__lf_runtime_domain_knowledge__SPECIAL_PRODUCT_ALIASES['AUTO_PRODUCT']]}]
__lf_runtime_domain_knowledge__PROCESS_KEYWORD_RULES = [{'target_value': 'INPUT', 'aliases': ['투입', 'input', '인풋']}]
__lf_runtime_domain_knowledge__OPER_NUM_DETECTION_PATTERNS = ['(?:공정번호|oper_num|oper|operation)\\s*[:=]?\\s*(\\d{4})', '(\\d{4})\\s*번?\\s*공정']
__lf_runtime_domain_knowledge__OPER_NUM_VALUES = [spec['OPER_NUM'] for spec in __lf_runtime_domain_knowledge__PROCESS_SPECS]

def __lf_runtime_domain_knowledge___build_group_field_spec(field_name: str, response_key: str, groups: __lf_runtime_domain_knowledge__Dict[str, __lf_runtime_domain_knowledge__Dict[str, __lf_runtime_domain_knowledge__List[str] | str]], literal_values: __lf_runtime_domain_knowledge__List[str] | None=None, keyword_rules: __lf_runtime_domain_knowledge__List[__lf_runtime_domain_knowledge__Dict[str, __lf_runtime_domain_knowledge__List[str] | str]] | None=None) -> __lf_runtime_domain_knowledge__Dict[str, object]:
    """그룹형 필드 스펙을 읽기 쉬운 형태로 만든다."""
    return {'field_name': field_name, 'response_key': response_key, 'value_kind': 'multi', 'resolver_kind': 'group', 'groups': groups, 'literal_values': literal_values, 'keyword_rules': keyword_rules, 'allow_text_detection': True}

def __lf_runtime_domain_knowledge___build_code_field_spec(field_name: str, response_key: str, candidate_values: __lf_runtime_domain_knowledge__List[str], patterns: __lf_runtime_domain_knowledge__List[str]) -> __lf_runtime_domain_knowledge__Dict[str, object]:
    """코드형 필드 스펙을 읽기 쉬운 형태로 만든다."""
    return {'field_name': field_name, 'response_key': response_key, 'value_kind': 'multi', 'resolver_kind': 'code', 'candidate_values': candidate_values, 'patterns': patterns, 'allow_text_detection': True}

def __lf_runtime_domain_knowledge___build_single_field_spec(field_name: str, response_key: str, keyword_rules: __lf_runtime_domain_knowledge__List[__lf_runtime_domain_knowledge__Dict[str, __lf_runtime_domain_knowledge__List[str] | str]] | None=None) -> __lf_runtime_domain_knowledge__Dict[str, object]:
    """단일 값 필드 스펙을 읽기 쉬운 형태로 만든다."""
    return {'field_name': field_name, 'response_key': response_key, 'value_kind': 'single', 'resolver_kind': 'single', 'keyword_rules': keyword_rules, 'allow_text_detection': True}
__lf_runtime_domain_knowledge__GROUP_PARAMETER_FIELD_SPECS = [__lf_runtime_domain_knowledge___build_group_field_spec(field_name='process_name', response_key='process', groups=__lf_runtime_domain_knowledge__PROCESS_GROUPS, literal_values=__lf_runtime_domain_knowledge__INDIVIDUAL_PROCESSES + ['INPUT'], keyword_rules=__lf_runtime_domain_knowledge__PROCESS_KEYWORD_RULES), __lf_runtime_domain_knowledge___build_group_field_spec('pkg_type1', 'pkg_type1', __lf_runtime_domain_knowledge__PKG_TYPE1_GROUPS), __lf_runtime_domain_knowledge___build_group_field_spec('pkg_type2', 'pkg_type2', __lf_runtime_domain_knowledge__PKG_TYPE2_GROUPS), __lf_runtime_domain_knowledge___build_group_field_spec('mode', 'mode', __lf_runtime_domain_knowledge__MODE_GROUPS), __lf_runtime_domain_knowledge___build_group_field_spec('den', 'den', __lf_runtime_domain_knowledge__DEN_GROUPS), __lf_runtime_domain_knowledge___build_group_field_spec('tech', 'tech', __lf_runtime_domain_knowledge__TECH_GROUPS)]
__lf_runtime_domain_knowledge__CODE_PARAMETER_FIELD_SPECS = [__lf_runtime_domain_knowledge___build_code_field_spec(field_name='oper_num', response_key='oper_num', candidate_values=__lf_runtime_domain_knowledge__OPER_NUM_VALUES, patterns=__lf_runtime_domain_knowledge__OPER_NUM_DETECTION_PATTERNS)]
__lf_runtime_domain_knowledge__SINGLE_VALUE_PARAMETER_FIELD_SPECS = [__lf_runtime_domain_knowledge___build_single_field_spec('product_name', 'product_name', __lf_runtime_domain_knowledge__SPECIAL_PRODUCT_KEYWORD_RULES), __lf_runtime_domain_knowledge___build_single_field_spec('line_name', 'line_name'), __lf_runtime_domain_knowledge___build_single_field_spec('mcp_no', 'mcp_no')]
__lf_runtime_domain_knowledge__PARAMETER_FIELD_SPECS = [*__lf_runtime_domain_knowledge__GROUP_PARAMETER_FIELD_SPECS, *__lf_runtime_domain_knowledge__CODE_PARAMETER_FIELD_SPECS, *__lf_runtime_domain_knowledge__SINGLE_VALUE_PARAMETER_FIELD_SPECS]
__lf_runtime_domain_knowledge__QUERY_MODE_SIGNAL_SPECS = {'explicit_date_reference': {'keywords': ['오늘', '어제', 'today', 'yesterday'], 'patterns': ['\\b20\\d{6}\\b'], 'description': '새 날짜를 직접 언급한 경우'}, 'grouping_expression': {'keywords': ['group by', 'by', '기준', '별'], 'patterns': ['([\\w/\\-가-힣]+)\\s*(by|기준|별)'], 'description': '그룹화 또는 breakdown 의도를 드러내는 표현'}, 'retrieval_request': {'keywords': ['생산', '목표', '불량', '설비', '가동률', 'wip', '수율', 'hold', '스크랩', '레시피', 'lot', '조회'], 'patterns': [], 'description': '새 raw dataset 조회 쪽으로 기울게 하는 표현'}, 'followup_filter_intent': {'keywords': ['조건', '필터', '공정', '공정번호', 'oper', 'pkg', '라인', 'mode', 'den', 'tech', 'lead', 'mcp'], 'patterns': [], 'description': '현재 결과에 새 필터를 적용하려는 의도를 드러내는 표현'}, 'fresh_retrieval_hint': {'keywords': ['조회', '데이터', '현황', '새로'], 'patterns': [], 'description': '현재 테이블 재가공보다 새 조회를 더 강하게 시사하는 표현'}}
__lf_runtime_domain_knowledge__AUTO_SUFFIXES = {'I', 'O', 'N', 'P', '1', 'V'}
__lf_runtime_domain_knowledge__SPECIAL_DOMAIN_RULES = ['투입량, INPUT, 인풋은 INPUT 공정의 생산량(실적)을 의미한다.', 'HBM제품, HBM자재, 3DS, 3DS제품은 TSV_DIE_TYP 값이 TSV인 제품을 의미한다.', 'Auto향은 MCP_NO의 마지막 문자가 I, O, N, P, 1, V 중 하나인 제품을 의미한다.', 'D/S 또는 DS는 기본적으로 D/S1 공정을 의미한다. 사용자가 PKG_TYPE1을 함께 말하면 그 조건도 동시에 적용한다.', 'DVI는 standalone 공정으로 우선 해석하고, D/I 그룹은 D/I 또는 DI로만 해석한다.', '나머지 공정들인 WVI, DVI, BBMS, AVI, MDVI, MDTI, QCSAT, LMDI, DIC, EVI는 공정명 그대로 사용한다.']
__lf_runtime_domain_knowledge__DATASET_METADATA = {'production': {'label': '생산', 'keywords': ['생산', 'production', '실적', '투입', 'input', '인풋']}, 'target': {'label': '목표', 'keywords': ['목표', 'target', '계획']}, 'defect': {'label': '불량', 'keywords': ['불량', 'defect', '결함']}, 'equipment': {'label': '설비', 'keywords': ['설비', '가동률', 'equipment', 'downtime']}, 'wip': {'label': 'WIP', 'keywords': ['wip', '재공', '대기']}, 'yield': {'label': '수율', 'keywords': ['수율', 'yield', 'pass rate', '합격률']}, 'hold': {'label': '홀드', 'keywords': ['hold', '홀드', '보류 lot', 'hold lot']}, 'scrap': {'label': '스크랩', 'keywords': ['scrap', '스크랩', '폐기', 'loss cost', '손실비용']}, 'recipe': {'label': '레시피', 'keywords': ['recipe', '레시피', '공정 조건', '조건값', 'parameter', '파라미터']}, 'lot_trace': {'label': 'LOT 이력', 'keywords': ['lot', 'lot trace', 'lot 이력', '추적', 'traceability', '로트']}}
__lf_runtime_domain_knowledge__DATASET_COLUMN_ALIAS_SPECS = {'production': {'production': ['production', 'prod', 'prod_qty', 'actual', 'actual_qty', '생산', '생산량', '실적']}, 'target': {'target': ['target', 'plan', 'plan_qty', 'goal', 'goal_qty', '목표', '목표량', '계획']}, 'defect': {'불량수량': ['불량수량', 'defect_qty', 'defect_count', 'ng_qty', 'ng_count'], 'defect_rate': ['defect_rate', 'defect ratio', 'ng_rate', '불량률']}, 'equipment': {'가동률': ['가동률', 'utilization', 'util_rate', 'util', '稼動率']}, 'wip': {'재공수량': ['재공수량', 'wip', 'wip_qty', 'queue_qty', 'in_process_qty']}, 'yield': {'yield_rate': ['yield_rate', 'yield', 'pass_rate', '수율'], 'pass_qty': ['pass_qty', 'pass', 'good_qty', '합격수량', '양품수량'], 'tested_qty': ['tested_qty', 'tested', 'input_qty', '검사수량', '투입수량']}, 'hold': {'hold_qty': ['hold_qty', 'hold', 'hold_count', '보류수량', '홀드수량']}}

def __lf_runtime_domain_knowledge__build_domain_knowledge_prompt() -> str:
    lines: __lf_runtime_domain_knowledge__List[str] = []
    lines.append('=' * 50)
    lines.append('[도메인 지식: 필터 추출 규칙]')
    lines.append('=' * 50)
    lines.append('\n## 사용 가능한 필터 필드')
    for key, field in __lf_runtime_domain_knowledge__FILTER_FIELDS.items():
        lines.append(f"- {field['field_name']} ({key}): {field['description']}")
    lines.append('\n## 파라미터 추출 스펙 요약')
    lines.append('- 그룹형 필드: process, pkg_type1, pkg_type2, mode, den, tech')
    lines.append('- 코드형 필드: oper_num')
    lines.append('- 단일 값 필드: product_name, line_name, mcp_no')
    lines.append('- LLM은 먼저 질문을 읽고 값을 뽑고, 이후 도메인 스펙에 따라 값이 정규화된다.')
    lines.append('\n## 공정 (process) 필터 규칙')
    lines.append('사용자가 그룹명이나 유사어로 언급하면 actual_values 전체를 process 필터로 사용한다.')
    lines.append('사용자가 개별 공정명으로 언급하면 해당 공정만 process 필터로 사용한다.')
    lines.append('')
    for group in __lf_runtime_domain_knowledge__PROCESS_GROUPS.values():
        lines.append(f"### {group['group_name']}")
        lines.append(f"  유사어: {', '.join(group['synonyms'])}")
        lines.append(f"  실제 값: [{', '.join(group['actual_values'])}]")
        lines.append(f"  설명: {group['description']}")
        lines.append('')
    lines.append('### 개별 공정 목록')
    lines.append(f"  {', '.join(__lf_runtime_domain_knowledge__INDIVIDUAL_PROCESSES)}")
    lines.append('\n## 공정번호 (OPER_NUM) 규칙')
    lines.append('공정번호는 4자리 숫자이며 공정명과 매핑된다.')
    lines.append('예시:')
    for process_name, oper_num in list(__lf_runtime_domain_knowledge__PROCESS_OPER_NUM_MAP.items())[:12]:
        lines.append(f'  - {process_name} -> {oper_num}')
    lines.append('사용자가 공정번호를 말하면 oper_num에 넣고, 공정명이 함께 있으면 두 조건을 동시에 유지한다.')
    lines.append('\n## PKG_TYPE1 규칙')
    for group_id, group in __lf_runtime_domain_knowledge__PKG_TYPE1_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## PKG_TYPE2 규칙')
    for group_id, group in __lf_runtime_domain_knowledge__PKG_TYPE2_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## TECH 규칙')
    for group_id, group in __lf_runtime_domain_knowledge__TECH_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## MODE 규칙')
    for group_id, group in __lf_runtime_domain_knowledge__MODE_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## DEN 규칙')
    for group_id, group in __lf_runtime_domain_knowledge__DEN_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## 특수 용어 규칙')
    for rule in __lf_runtime_domain_knowledge__SPECIAL_DOMAIN_RULES:
        lines.append(f'- {rule}')
    lines.append('\n## 특수 제품/공정 정규화 규칙')
    for rule in __lf_runtime_domain_knowledge__SPECIAL_PRODUCT_KEYWORD_RULES:
        lines.append(f"- 제품 별칭 {', '.join(rule['aliases'])} 는 product_name '{rule['target_value']}' 로 정규화한다.")
    for rule in __lf_runtime_domain_knowledge__PROCESS_KEYWORD_RULES:
        lines.append(f"- 공정 키워드 {', '.join(rule['aliases'])} 는 process '{rule['target_value']}' 로 정규화한다.")
    lines.append('\n## 공통 추출 규칙')
    lines.append('1. 사용자가 언급하지 않은 필드는 null로 설정한다.')
    lines.append('2. 여러 값을 나열하면 리스트로 추출한다.')
    lines.append('3. 그룹명과 개별값을 구분한다.')
    lines.append('4. 공정, OPER_NUM, PKG_TYPE1, PKG_TYPE2가 함께 나오면 가능한 조건을 모두 유지한다.')
    lines.append('5. mcp_no는 MCP_NO 문자열 그대로 유지한다.')
    return '\n'.join(lines)

# ---- visible runtime: _runtime.shared.config ----
import os as __lf_runtime_shared_config__os
from dotenv import load_dotenv as __lf_runtime_shared_config__load_dotenv
__lf_runtime_shared_config__load_dotenv()
__lf_runtime_shared_config__MODEL_TASK_GROUPS = {'fast': {'parameter_extract', 'query_mode_review', 'response_summary'}, 'strong': {'retrieval_plan', 'sufficiency_review', 'analysis_code', 'analysis_retry', 'domain_registry_parse'}}

def __lf_runtime_shared_config___resolve_model_name(task: str) -> str:
    """Return the model name that fits the task."""
    fast_model = __lf_runtime_shared_config__os.getenv('LLM_FAST_MODEL', '').strip() or 'gemini-flash-latest'
    strong_model = __lf_runtime_shared_config__os.getenv('LLM_STRONG_MODEL', '').strip() or fast_model
    normalized_task = str(task or '').strip().lower()
    if normalized_task in __lf_runtime_shared_config__MODEL_TASK_GROUPS['strong']:
        return strong_model
    return fast_model

def __lf_runtime_shared_config__get_llm(task: str='general', temperature: float=0.0):
    """Create an LLM client for one task category."""
    api_key = __lf_runtime_shared_config__os.getenv('LLM_API_KEY', '').strip()
    if not api_key:
        raise ValueError('LLM_API_KEY environment variable is not set.')
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as exc:
        raise ImportError('langchain_google_genai package is required to build the LLM client.') from exc
    return ChatGoogleGenerativeAI(model=__lf_runtime_shared_config___resolve_model_name(task), google_api_key=api_key, temperature=temperature)
__lf_runtime_shared_config__SYSTEM_PROMPT = 'You are an AI assistant for manufacturing data retrieval and follow-up analysis.\n\nRules:\n- First decide whether the user needs fresh source retrieval or a follow-up transformation on current data.\n- When retrieval is needed, extract only retrieval-safe parameters and use them to load raw source data.\n- When current data is already sufficient, answer through pandas-style follow-up analysis.\n- Never invent missing datasets or columns.\n- Always explain results based on the current result table.\n'

# ---- visible runtime: _runtime.domain.registry ----
import copy as __lf_runtime_domain_registry__copy
import json as __lf_runtime_domain_registry__json
from datetime import datetime as __lf_runtime_domain_registry__datetime
from typing import Any as __lf_runtime_domain_registry__Any, Dict as __lf_runtime_domain_registry__Dict, Iterable as __lf_runtime_domain_registry__Iterable, List as __lf_runtime_domain_registry__List
from langchain_core.messages import HumanMessage as __lf_runtime_domain_registry__HumanMessage, SystemMessage as __lf_runtime_domain_registry__SystemMessage
__lf_runtime_domain_registry__SYSTEM_PROMPT = __lf_runtime_shared_config__SYSTEM_PROMPT
__lf_runtime_domain_registry__get_llm = __lf_runtime_shared_config__get_llm
__lf_runtime_domain_registry__normalize_text = __lf_runtime_shared_filter_utils__normalize_text
__lf_runtime_domain_registry__DATASET_METADATA = __lf_runtime_domain_knowledge__DATASET_METADATA
__lf_runtime_domain_registry__DEN_GROUPS = __lf_runtime_domain_knowledge__DEN_GROUPS
__lf_runtime_domain_registry__MODE_GROUPS = __lf_runtime_domain_knowledge__MODE_GROUPS
__lf_runtime_domain_registry__PKG_TYPE1_GROUPS = __lf_runtime_domain_knowledge__PKG_TYPE1_GROUPS
__lf_runtime_domain_registry__PKG_TYPE2_GROUPS = __lf_runtime_domain_knowledge__PKG_TYPE2_GROUPS
__lf_runtime_domain_registry__PROCESS_GROUPS = __lf_runtime_domain_knowledge__PROCESS_GROUPS
__lf_runtime_domain_registry__SPECIAL_PRODUCT_ALIASES = __lf_runtime_domain_knowledge__SPECIAL_PRODUCT_ALIASES
__lf_runtime_domain_registry__TECH_GROUPS = __lf_runtime_domain_knowledge__TECH_GROUPS
__lf_runtime_domain_registry__SUPPORTED_VALUE_FIELDS = {'process_name', 'mode', 'den', 'tech', 'pkg_type1', 'pkg_type2', 'product_name', 'line_name', 'oper_num', 'mcp_no'}
__lf_runtime_domain_registry__FIELD_NAME_ALIASES = {'process': 'process_name', 'process_name': 'process_name', 'oper_name': 'process_name', 'mode': 'mode', 'den': 'den', 'density': 'den', 'tech': 'tech', 'pkg1': 'pkg_type1', 'pkg_type1': 'pkg_type1', 'pkg2': 'pkg_type2', 'pkg_type2': 'pkg_type2', 'product': 'product_name', 'product_name': 'product_name', 'line': 'line_name', 'line_name': 'line_name', 'oper_num': 'oper_num', 'mcp': 'mcp_no', 'mcp_no': 'mcp_no'}
__lf_runtime_domain_registry__VALID_CALCULATION_MODES = {'', 'ratio', 'difference', 'sum', 'mean', 'count', 'condition_flag', 'threshold_flag', 'count_if', 'sum_if', 'mean_if', 'custom'}
__lf_runtime_domain_registry__VALID_JOIN_TYPES = {'left', 'inner', 'right', 'outer'}
__lf_runtime_domain_registry__DEFAULT_ANALYSIS_RULES = [{'name': 'achievement_rate', 'display_name': 'achievement rate', 'synonyms': ['achievement rate', '달성율', '달성률', '생산 달성율', '생산 달성률', '목표 대비 생산'], 'required_datasets': ['production', 'target'], 'required_columns': ['production', 'target'], 'source_columns': [{'dataset_key': 'production', 'column': 'production', 'role': 'numerator'}, {'dataset_key': 'target', 'column': 'target', 'role': 'denominator'}], 'calculation_mode': 'ratio', 'output_column': 'achievement_rate', 'default_group_by': ['OPER_NAME'], 'condition': '', 'decision_rule': '', 'formula': 'production / target', 'pandas_hint': 'group by OPER_NAME and calculate production / target', 'description': 'Calculate production achievement rate using production and target.', 'source': 'builtin'}, {'name': 'yield_rate', 'display_name': 'yield rate', 'synonyms': ['yield', 'yield rate', '수율'], 'required_datasets': ['yield'], 'required_columns': ['yield_rate', 'pass_qty', 'tested_qty'], 'source_columns': [{'dataset_key': 'yield', 'column': 'yield_rate', 'role': 'preferred_metric'}, {'dataset_key': 'yield', 'column': 'pass_qty', 'role': 'pass_qty'}, {'dataset_key': 'yield', 'column': 'tested_qty', 'role': 'tested_qty'}], 'calculation_mode': 'ratio', 'output_column': 'yield_rate', 'default_group_by': ['OPER_NAME'], 'condition': '', 'decision_rule': '', 'formula': 'yield_rate or pass_qty / tested_qty', 'pandas_hint': 'group by OPER_NAME and average yield_rate', 'description': 'Analyze yield-focused questions with yield data.', 'source': 'builtin'}, {'name': 'production_saturation_rate', 'display_name': 'production saturation rate', 'synonyms': ['production saturation', 'production saturation rate', '포화율', '생산 포화율', '생산포화율'], 'required_datasets': ['production', 'wip'], 'required_columns': ['production', '재공수량'], 'source_columns': [{'dataset_key': 'production', 'column': 'production', 'role': 'numerator'}, {'dataset_key': 'wip', 'column': '재공수량', 'role': 'denominator'}], 'calculation_mode': 'ratio', 'output_column': 'production_saturation_rate', 'default_group_by': ['OPER_NAME'], 'condition': '', 'decision_rule': '', 'formula': 'production / 재공수량', 'pandas_hint': 'group by OPER_NAME and calculate production / 재공수량', 'description': 'Calculate production saturation rate using production and WIP quantity.', 'source': 'builtin'}]
__lf_runtime_domain_registry__DEFAULT_JOIN_RULES = [{'name': 'production_target_join', 'base_dataset': 'production', 'join_dataset': 'target', 'join_type': 'left', 'join_keys': ['WORK_DT', 'OPER_NAME', '공정군', '라인', 'MODE', 'DEN'], 'description': 'Join production and target rows with common manufacturing dimensions.', 'source': 'builtin'}, {'name': 'production_wip_join', 'base_dataset': 'production', 'join_dataset': 'wip', 'join_type': 'left', 'join_keys': ['WORK_DT', 'OPER_NAME', '공정군', '라인', 'MODE', 'DEN'], 'description': 'Join production and WIP rows with common manufacturing dimensions.', 'source': 'builtin'}]

def __lf_runtime_domain_registry___empty_registry() -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    return {'entries': [], 'dataset_keywords': [], 'value_groups': [], 'analysis_rules': [], 'join_rules': [], 'notes': [], 'domain_rules_text': ''}
__lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any] = __lf_runtime_domain_registry___empty_registry()

def __lf_runtime_domain_registry___get_llm_for_task(task: str):
    try:
        return __lf_runtime_domain_registry__get_llm(task=task)
    except TypeError:
        return __lf_runtime_domain_registry__get_llm()

def __lf_runtime_domain_registry___as_list(value: __lf_runtime_domain_registry__Any) -> __lf_runtime_domain_registry__List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []

def __lf_runtime_domain_registry___dedupe(values: __lf_runtime_domain_registry__Iterable[str]) -> __lf_runtime_domain_registry__List[str]:
    seen: __lf_runtime_domain_registry__List[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen

def __lf_runtime_domain_registry___parse_json_block(text: str) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    cleaned = str(text or '').strip()
    if '```json' in cleaned:
        cleaned = cleaned.split('```json', 1)[1].split('```', 1)[0]
    elif '```' in cleaned:
        cleaned = cleaned.split('```', 1)[1].split('```', 1)[0]
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return __lf_runtime_domain_registry__json.loads(cleaned[start:end + 1])
    except Exception:
        return {}

def __lf_runtime_domain_registry___extract_text(content: __lf_runtime_domain_registry__Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join((str(item.get('text', '')) if isinstance(item, dict) else str(item) for item in content))
    return str(content)

def __lf_runtime_domain_registry___field_name(value: __lf_runtime_domain_registry__Any) -> str:
    return __lf_runtime_domain_registry__FIELD_NAME_ALIASES.get(__lf_runtime_domain_registry__normalize_text(value), __lf_runtime_domain_registry__normalize_text(value))

def __lf_runtime_domain_registry___normalize_source_columns(raw_columns: __lf_runtime_domain_registry__Any) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, str]]:
    items: __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, str]] = []
    for item in raw_columns or []:
        if not isinstance(item, dict):
            continue
        dataset_key = __lf_runtime_domain_registry__normalize_text(item.get('dataset_key'))
        column = str(item.get('column', '')).strip()
        role = str(item.get('role', '')).strip()
        if dataset_key and column:
            items.append({'dataset_key': dataset_key, 'column': column, 'role': role})
    return items

def __lf_runtime_domain_registry___normalize_value_group(raw_group: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    canonical = str(raw_group.get('canonical', '')).strip()
    return {'field': __lf_runtime_domain_registry___field_name(raw_group.get('field')), 'canonical': canonical, 'synonyms': __lf_runtime_domain_registry___dedupe([canonical, *__lf_runtime_domain_registry___as_list(raw_group.get('synonyms'))]), 'values': __lf_runtime_domain_registry___dedupe(__lf_runtime_domain_registry___as_list(raw_group.get('values'))), 'description': str(raw_group.get('description', '')).strip()}

def __lf_runtime_domain_registry___normalize_analysis_rule(raw_rule: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    name = str(raw_rule.get('name', '')).strip()
    display_name = str(raw_rule.get('display_name', name)).strip() or name
    calc_mode = str(raw_rule.get('calculation_mode', '')).strip()
    if calc_mode not in __lf_runtime_domain_registry__VALID_CALCULATION_MODES:
        calc_mode = 'custom' if calc_mode else ''
    return {'name': name, 'display_name': display_name, 'synonyms': __lf_runtime_domain_registry___dedupe([name, display_name, *__lf_runtime_domain_registry___as_list(raw_rule.get('synonyms'))]), 'required_datasets': [__lf_runtime_domain_registry__normalize_text(item) for item in __lf_runtime_domain_registry___as_list(raw_rule.get('required_datasets'))], 'required_columns': __lf_runtime_domain_registry___dedupe(__lf_runtime_domain_registry___as_list(raw_rule.get('required_columns'))), 'source_columns': __lf_runtime_domain_registry___normalize_source_columns(raw_rule.get('source_columns')), 'calculation_mode': calc_mode, 'output_column': str(raw_rule.get('output_column', '')).strip(), 'default_group_by': __lf_runtime_domain_registry___dedupe(__lf_runtime_domain_registry___as_list(raw_rule.get('default_group_by'))), 'condition': str(raw_rule.get('condition', '')).strip(), 'decision_rule': str(raw_rule.get('decision_rule', '')).strip(), 'formula': str(raw_rule.get('formula', '')).strip(), 'pandas_hint': str(raw_rule.get('pandas_hint', '')).strip(), 'description': str(raw_rule.get('description', '')).strip(), 'source': str(raw_rule.get('source', 'custom')).strip() or 'custom'}

def __lf_runtime_domain_registry___normalize_join_rule(raw_rule: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    join_type = str(raw_rule.get('join_type', 'left')).strip().lower()
    if join_type not in __lf_runtime_domain_registry__VALID_JOIN_TYPES:
        join_type = 'left'
    return {'name': str(raw_rule.get('name', '')).strip(), 'base_dataset': __lf_runtime_domain_registry__normalize_text(raw_rule.get('base_dataset')), 'join_dataset': __lf_runtime_domain_registry__normalize_text(raw_rule.get('join_dataset')), 'join_type': join_type, 'join_keys': __lf_runtime_domain_registry___dedupe(__lf_runtime_domain_registry___as_list(raw_rule.get('join_keys'))), 'description': str(raw_rule.get('description', '')).strip(), 'source': str(raw_rule.get('source', 'custom')).strip() or 'custom'}

def __lf_runtime_domain_registry___normalize_entry(payload: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any], raw_text: str='') -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    return {'id': str(payload.get('id', '')).strip() or __lf_runtime_domain_registry__datetime.now().strftime('%Y%m%d%H%M%S%f'), 'title': str(payload.get('title', '')).strip() or raw_text[:30].strip() or 'domain note', 'created_at': str(payload.get('created_at', '')).strip() or __lf_runtime_domain_registry__datetime.now().isoformat(), 'raw_text': str(payload.get('raw_text', '')).strip() or raw_text, 'dataset_keywords': [{'dataset_key': __lf_runtime_domain_registry__normalize_text(item.get('dataset_key')), 'keywords': __lf_runtime_domain_registry___dedupe(__lf_runtime_domain_registry___as_list(item.get('keywords')))} for item in payload.get('dataset_keywords', []) if isinstance(item, dict)], 'value_groups': [__lf_runtime_domain_registry___normalize_value_group(item) for item in payload.get('value_groups', []) if isinstance(item, dict)], 'analysis_rules': [__lf_runtime_domain_registry___normalize_analysis_rule(item) for item in payload.get('analysis_rules', []) if isinstance(item, dict)], 'join_rules': [__lf_runtime_domain_registry___normalize_join_rule(item) for item in payload.get('join_rules', []) if isinstance(item, dict)], 'notes': __lf_runtime_domain_registry___dedupe(__lf_runtime_domain_registry___as_list(payload.get('notes')))}

def __lf_runtime_domain_registry___merge_registry(registry: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any], entry: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]) -> None:
    registry['entries'].append(entry)
    registry['dataset_keywords'].extend(entry.get('dataset_keywords', []))
    registry['value_groups'].extend(entry.get('value_groups', []))
    registry['analysis_rules'].extend(entry.get('analysis_rules', []))
    registry['join_rules'].extend(entry.get('join_rules', []))
    registry['notes'].extend(entry.get('notes', []))

def __lf_runtime_domain_registry___normalize_registry_payload(payload: __lf_runtime_domain_registry__Any) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    registry = __lf_runtime_domain_registry___empty_registry()
    if payload in (None, '', {}, []):
        return registry
    if isinstance(payload, str):
        parsed = __lf_runtime_domain_registry___parse_json_block(payload)
        if parsed:
            payload = parsed
        else:
            registry['notes'] = __lf_runtime_domain_registry___dedupe([str(payload).strip()])
            return registry
    candidates: __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]] = []
    if isinstance(payload, list):
        candidates = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        if isinstance(payload.get('entries'), list):
            candidates.extend((item for item in payload.get('entries', []) if isinstance(item, dict)))
            extra = {key: value for key, value in payload.items() if key != 'entries'}
            if any((key in extra for key in ('dataset_keywords', 'value_groups', 'analysis_rules', 'join_rules', 'notes', 'title', 'raw_text'))):
                candidates.insert(0, extra)
        else:
            candidates = [payload]
    for item in candidates:
        __lf_runtime_domain_registry___merge_registry(registry, __lf_runtime_domain_registry___normalize_entry(item, str(item.get('raw_text', ''))))
    registry['notes'] = __lf_runtime_domain_registry___dedupe(registry['notes'])
    return registry

def __lf_runtime_domain_registry__set_active_domain_context(domain_rules_text: str | None=None, domain_registry_payload: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any] | __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Any] | str | None=None) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    global __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT
    __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT = __lf_runtime_domain_registry___normalize_registry_payload(domain_registry_payload)
    __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT['domain_rules_text'] = str(domain_rules_text or '').strip()
    return __lf_runtime_domain_registry__load_domain_registry()

def __lf_runtime_domain_registry__clear_active_domain_context() -> None:
    global __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT
    __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT = __lf_runtime_domain_registry___empty_registry()

def __lf_runtime_domain_registry__load_domain_registry() -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    return __lf_runtime_domain_registry__copy.deepcopy(__lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT)

def __lf_runtime_domain_registry__validate_domain_payload(payload: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any], registry: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any] | None=None) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, str]]:
    registry = registry or __lf_runtime_domain_registry__load_domain_registry()
    issues: __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, str]] = []
    owners: __lf_runtime_domain_registry__Dict[str, str] = {}
    for dataset_key, keywords in __lf_runtime_domain_registry___build_builtin_dataset_keywords().items():
        for keyword in keywords:
            owners[__lf_runtime_domain_registry__normalize_text(keyword)] = dataset_key
    for item in registry.get('dataset_keywords', []):
        for keyword in item.get('keywords', []):
            owners[__lf_runtime_domain_registry__normalize_text(keyword)] = item.get('dataset_key', '')
    for item in payload.get('dataset_keywords', []):
        dataset_key = item.get('dataset_key', '')
        if dataset_key not in __lf_runtime_domain_registry__DATASET_METADATA:
            issues.append({'severity': 'error', 'message': f'Unknown dataset key: {dataset_key}'})
        for keyword in item.get('keywords', []):
            owner = owners.get(__lf_runtime_domain_registry__normalize_text(keyword))
            if owner and owner != dataset_key:
                issues.append({'severity': 'error', 'message': f'Keyword conflict: `{keyword}` is already used by `{owner}`.'})
    for group in payload.get('value_groups', []):
        if group.get('field') not in __lf_runtime_domain_registry__SUPPORTED_VALUE_FIELDS:
            issues.append({'severity': 'error', 'message': f"Unsupported field for value group: {group.get('field')}"})
        if not group.get('canonical'):
            issues.append({'severity': 'error', 'message': 'Value group requires `canonical`.'})
    for rule in payload.get('analysis_rules', []):
        if not rule.get('name'):
            issues.append({'severity': 'error', 'message': 'Analysis rule requires `name`.'})
        if not rule.get('required_datasets'):
            issues.append({'severity': 'warning', 'message': f"Analysis rule `{rule.get('name', 'unknown')}` has no required_datasets."})
    for rule in payload.get('join_rules', []):
        if not rule.get('base_dataset') or not rule.get('join_dataset'):
            issues.append({'severity': 'error', 'message': 'Join rule requires both base_dataset and join_dataset.'})
    return issues

def __lf_runtime_domain_registry___detect_join_keys_from_text(raw_text: str) -> __lf_runtime_domain_registry__List[str]:
    candidates = ['WORK_DT', 'OPER_NAME', 'MODE', 'FAMILY', 'FACTORY', 'ORG', 'TECH', 'DEN', 'LEAD']
    normalized = __lf_runtime_domain_registry__normalize_text(raw_text)
    return [candidate for candidate in candidates if __lf_runtime_domain_registry__normalize_text(candidate) in normalized]

def __lf_runtime_domain_registry___infer_join_type_from_text(raw_text: str) -> str:
    normalized = __lf_runtime_domain_registry__normalize_text(raw_text)
    if 'inner' in normalized:
        return 'inner'
    if 'outer' in normalized:
        return 'outer'
    if 'right' in normalized:
        return 'right'
    return 'left'

def __lf_runtime_domain_registry___infer_join_rules_from_text(raw_text: str, payload: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]:
    rules: __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]] = []
    for analysis_rule in payload.get('analysis_rules', []):
        datasets = analysis_rule.get('required_datasets', [])
        if len(datasets) < 2:
            continue
        rules.append({'name': f'{datasets[0]}_{datasets[1]}_join', 'base_dataset': datasets[0], 'join_dataset': datasets[1], 'join_type': __lf_runtime_domain_registry___infer_join_type_from_text(raw_text), 'join_keys': __lf_runtime_domain_registry___detect_join_keys_from_text(raw_text) or ['WORK_DT', 'OPER_NAME'], 'description': f'Inferred from free-text note: {raw_text[:80]}', 'source': 'custom'})
    return rules

def __lf_runtime_domain_registry__parse_domain_text_to_payload(raw_text: str) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    prompt = f'Extract a structured manufacturing domain note into JSON only.\n\nFields:\n- title\n- dataset_keywords: [{{dataset_key, keywords}}]\n- value_groups: [{{field, canonical, synonyms, values, description}}]\n- analysis_rules: [{{name, display_name, synonyms, required_datasets, required_columns, source_columns, calculation_mode, output_column, default_group_by, condition, decision_rule, formula, pandas_hint, description}}]\n- join_rules: [{{name, base_dataset, join_dataset, join_type, join_keys, description}}]\n- notes\n\nText:\n{raw_text}\n'
    try:
        llm = __lf_runtime_domain_registry___get_llm_for_task('domain_registry_parse')
        response = llm.invoke([__lf_runtime_domain_registry__SystemMessage(content=__lf_runtime_domain_registry__SYSTEM_PROMPT), __lf_runtime_domain_registry__HumanMessage(content=prompt)])
        parsed = __lf_runtime_domain_registry___parse_json_block(__lf_runtime_domain_registry___extract_text(response.content))
    except Exception:
        parsed = {}
    normalized = __lf_runtime_domain_registry___normalize_entry(parsed, raw_text)
    if not normalized.get('join_rules'):
        normalized['join_rules'] = __lf_runtime_domain_registry___infer_join_rules_from_text(raw_text, normalized)
    return normalized

def __lf_runtime_domain_registry__preview_domain_submission(raw_text: str) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    payload = __lf_runtime_domain_registry__parse_domain_text_to_payload(raw_text)
    issues = __lf_runtime_domain_registry__validate_domain_payload(payload)
    return {'success': True, 'payload': payload, 'issues': issues, 'can_save': not any((item['severity'] == 'error' for item in issues))}

def __lf_runtime_domain_registry__register_domain_submission(raw_text: str) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    preview = __lf_runtime_domain_registry__preview_domain_submission(raw_text)
    if not preview['can_save']:
        return {'success': False, 'payload': preview['payload'], 'issues': preview['issues'], 'message': 'Validation failed.'}
    global __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT
    updated = __lf_runtime_domain_registry__load_domain_registry()
    __lf_runtime_domain_registry___merge_registry(updated, preview['payload'])
    updated['notes'] = __lf_runtime_domain_registry___dedupe(updated['notes'])
    __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT = updated
    return {'success': True, 'payload': preview['payload'], 'issues': preview['issues'], 'message': 'Saved in active context.'}

def __lf_runtime_domain_registry__delete_domain_entry(entry_id: str) -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    global __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT
    current = __lf_runtime_domain_registry__load_domain_registry()
    entries = [entry for entry in current.get('entries', []) if entry.get('id') != entry_id]
    if len(entries) == len(current.get('entries', [])):
        return {'success': False, 'deleted': False, 'message': 'Entry not found.'}
    rebuilt = __lf_runtime_domain_registry___empty_registry()
    rebuilt['domain_rules_text'] = current.get('domain_rules_text', '')
    for entry in entries:
        __lf_runtime_domain_registry___merge_registry(rebuilt, entry)
    rebuilt['notes'] = __lf_runtime_domain_registry___dedupe(rebuilt['notes'])
    __lf_runtime_domain_registry__ACTIVE_DOMAIN_CONTEXT = rebuilt
    return {'success': True, 'deleted': True, 'message': 'Deleted from active context.'}

def __lf_runtime_domain_registry__list_domain_entries() -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]:
    return __lf_runtime_domain_registry__load_domain_registry()['entries']

def __lf_runtime_domain_registry___build_builtin_value_groups() -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]]:
    registry: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]] = {field: [] for field in __lf_runtime_domain_registry__SUPPORTED_VALUE_FIELDS}

    def add_group(field: str, canonical: str, synonyms: __lf_runtime_domain_registry__List[str], values: __lf_runtime_domain_registry__List[str], description: str) -> None:
        registry[field].append({'field': field, 'canonical': canonical, 'synonyms': __lf_runtime_domain_registry___dedupe([canonical, *synonyms]), 'values': __lf_runtime_domain_registry___dedupe(values), 'description': description, 'source': 'builtin'})
    for key, group in __lf_runtime_domain_registry__PROCESS_GROUPS.items():
        add_group('process_name', group.get('group_name', key), group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in __lf_runtime_domain_registry__MODE_GROUPS.items():
        add_group('mode', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in __lf_runtime_domain_registry__DEN_GROUPS.items():
        add_group('den', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in __lf_runtime_domain_registry__TECH_GROUPS.items():
        add_group('tech', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in __lf_runtime_domain_registry__PKG_TYPE1_GROUPS.items():
        add_group('pkg_type1', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in __lf_runtime_domain_registry__PKG_TYPE2_GROUPS.items():
        add_group('pkg_type2', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    registry['product_name'].append({'field': 'product_name', 'canonical': 'HBM_OR_3DS', 'synonyms': ['HBM_OR_3DS', 'HBM/3DS', *__lf_runtime_domain_registry__SPECIAL_PRODUCT_ALIASES['HBM_OR_3DS']], 'values': ['HBM_OR_3DS'], 'description': 'TSV-based products such as HBM and 3DS.', 'source': 'builtin'})
    registry['product_name'].append({'field': 'product_name', 'canonical': 'AUTO_PRODUCT', 'synonyms': ['AUTO_PRODUCT', 'AUTO', *__lf_runtime_domain_registry__SPECIAL_PRODUCT_ALIASES['AUTO_PRODUCT']], 'values': ['AUTO_PRODUCT'], 'description': 'Automotive products.', 'source': 'builtin'})
    return registry

def __lf_runtime_domain_registry___build_builtin_dataset_keywords() -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__List[str]]:
    return {key: list(meta.get('keywords', [])) for key, meta in __lf_runtime_domain_registry__DATASET_METADATA.items()}

def __lf_runtime_domain_registry__get_dataset_keyword_map() -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__List[str]]:
    registry = __lf_runtime_domain_registry__load_domain_registry()
    keyword_map = __lf_runtime_domain_registry___build_builtin_dataset_keywords()
    for item in registry.get('dataset_keywords', []):
        dataset_key = item.get('dataset_key', '')
        keyword_map.setdefault(dataset_key, [])
        for keyword in item.get('keywords', []):
            if keyword not in keyword_map[dataset_key]:
                keyword_map[dataset_key].append(keyword)
    return keyword_map

def __lf_runtime_domain_registry__get_registered_value_groups(field_name: str | None=None, include_builtin: bool=False) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]:
    registry = __lf_runtime_domain_registry__load_domain_registry()
    groups: __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]] = []
    if include_builtin:
        builtin = __lf_runtime_domain_registry___build_builtin_value_groups()
        if field_name:
            groups.extend(builtin.get(field_name, []))
        else:
            for values in builtin.values():
                groups.extend(values)
    for group in registry.get('value_groups', []):
        if field_name and group.get('field') != field_name:
            continue
        groups.append(group)
    return groups

def __lf_runtime_domain_registry__expand_registered_values(field_name: str, raw_values: __lf_runtime_domain_registry__Any) -> __lf_runtime_domain_registry__List[str] | None:
    requested = __lf_runtime_domain_registry___as_list(raw_values)
    if not requested:
        return None
    normalized_field = __lf_runtime_domain_registry___field_name(field_name)
    expanded: __lf_runtime_domain_registry__List[str] = []
    for raw_value in requested:
        matched = False
        raw_key = __lf_runtime_domain_registry__normalize_text(raw_value)
        for group in __lf_runtime_domain_registry__get_registered_value_groups(normalized_field, include_builtin=True):
            aliases = [group.get('canonical', ''), *group.get('synonyms', []), *group.get('values', [])]
            if any((raw_key == __lf_runtime_domain_registry__normalize_text(alias) for alias in aliases)):
                expanded.extend(group.get('values', []))
                matched = True
                break
        if not matched:
            expanded.append(raw_value)
    expanded = __lf_runtime_domain_registry___dedupe(expanded)
    return expanded or None

def __lf_runtime_domain_registry__detect_registered_values(field_name: str, text: str) -> __lf_runtime_domain_registry__List[str] | None:
    normalized_field = __lf_runtime_domain_registry___field_name(field_name)
    normalized_text_value = __lf_runtime_domain_registry__normalize_text(text)
    detected: __lf_runtime_domain_registry__List[str] = []
    for group in __lf_runtime_domain_registry__get_registered_value_groups(normalized_field, include_builtin=True):
        aliases = [group.get('canonical', ''), *group.get('synonyms', []), *group.get('values', [])]
        if any((__lf_runtime_domain_registry__normalize_text(alias) in normalized_text_value for alias in aliases if str(alias).strip())):
            detected.extend(group.get('values', []))
    detected = __lf_runtime_domain_registry___dedupe(detected)
    return detected or None

def __lf_runtime_domain_registry__get_registered_analysis_rules(include_builtin: bool=True) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]:
    registry = __lf_runtime_domain_registry__load_domain_registry()
    return [*(__lf_runtime_domain_registry__DEFAULT_ANALYSIS_RULES if include_builtin else []), *registry.get('analysis_rules', [])]

def __lf_runtime_domain_registry__get_registered_join_rules(include_builtin: bool=True) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]:
    registry = __lf_runtime_domain_registry__load_domain_registry()
    return [*(__lf_runtime_domain_registry__DEFAULT_JOIN_RULES if include_builtin else []), *registry.get('join_rules', [])]

def __lf_runtime_domain_registry___compact_text(value: __lf_runtime_domain_registry__Any) -> str:
    return __lf_runtime_domain_registry__normalize_text(str(value or '')).replace(' ', '')

def __lf_runtime_domain_registry__match_registered_analysis_rules(query_text: str, include_builtin: bool=True) -> __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]]:
    normalized = __lf_runtime_domain_registry___compact_text(query_text)
    matched: __lf_runtime_domain_registry__List[__lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]] = []
    for rule in __lf_runtime_domain_registry__get_registered_analysis_rules(include_builtin=include_builtin):
        candidates = [rule.get('name', ''), rule.get('display_name', ''), *rule.get('synonyms', [])]
        if any((__lf_runtime_domain_registry___compact_text(candidate) and __lf_runtime_domain_registry___compact_text(candidate) in normalized for candidate in candidates)):
            matched.append(rule)
    return matched

def __lf_runtime_domain_registry__format_analysis_rule_for_prompt(rule: __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]) -> str:
    return f"- name={rule.get('name', '')}, display_name={rule.get('display_name', '')}, required_datasets={rule.get('required_datasets', [])}, required_columns={rule.get('required_columns', [])}, calculation_mode={rule.get('calculation_mode', '')}, output_column={rule.get('output_column', '')}, default_group_by={rule.get('default_group_by', [])}, condition={rule.get('condition', '')}, decision_rule={rule.get('decision_rule', '')}, formula={rule.get('formula', '')}, source_columns={rule.get('source_columns', [])}"

def __lf_runtime_domain_registry__build_registered_domain_prompt() -> str:
    registry = __lf_runtime_domain_registry__load_domain_registry()
    lines = ['Custom domain registry summary:']
    if registry.get('domain_rules_text'):
        lines.append('Free-text domain rules:')
        lines.append(registry['domain_rules_text'])
    keyword_map = __lf_runtime_domain_registry__get_dataset_keyword_map()
    if keyword_map:
        lines.append('Dataset keywords:')
        for dataset_key, keywords in keyword_map.items():
            if keywords:
                lines.append(f"- {dataset_key}: {', '.join(keywords)}")
    custom_groups = __lf_runtime_domain_registry__get_registered_value_groups(include_builtin=False)
    if custom_groups:
        lines.append('Custom value groups:')
        for group in custom_groups:
            lines.append(f"- field={group.get('field')}, canonical={group.get('canonical')}, values={group.get('values', [])}, synonyms={group.get('synonyms', [])}")
    if registry.get('analysis_rules'):
        lines.append('Custom analysis rules:')
        for rule in registry['analysis_rules']:
            lines.append(__lf_runtime_domain_registry__format_analysis_rule_for_prompt(rule))
    if registry.get('join_rules'):
        lines.append('Custom join rules:')
        for rule in registry['join_rules']:
            lines.append(f"- {rule.get('base_dataset')} -> {rule.get('join_dataset')}, type={rule.get('join_type')}, keys={rule.get('join_keys', [])}")
    if registry.get('notes'):
        lines.append('Notes:')
        for note in registry['notes']:
            lines.append(f'- {note}')
    if len(lines) == 1:
        lines.append('- No custom registry entries.')
    return '\n'.join(lines)

def __lf_runtime_domain_registry__get_domain_registry_summary() -> __lf_runtime_domain_registry__Dict[str, __lf_runtime_domain_registry__Any]:
    registry = __lf_runtime_domain_registry__load_domain_registry()
    return {'custom_entry_count': len(registry['entries']), 'custom_dataset_keyword_count': len(registry['dataset_keywords']), 'custom_value_group_count': len(registry['value_groups']), 'custom_analysis_rule_count': len(registry['analysis_rules']), 'custom_join_rule_count': len(registry['join_rules']), 'domain_rules_text_length': len(str(registry.get('domain_rules_text', ''))), 'builtin_analysis_rule_count': len(__lf_runtime_domain_registry__DEFAULT_ANALYSIS_RULES), 'builtin_join_rule_count': len(__lf_runtime_domain_registry__DEFAULT_JOIN_RULES), 'builtin_value_group_count': sum((len(items) for items in __lf_runtime_domain_registry___build_builtin_value_groups().values()))}

# ---- visible runtime: node_utils ----
"""Local helpers shared by standalone Langflow component nodes."""
import json as __lf_node_utils__json
import sys as __lf_node_utils__sys
from pathlib import Path as __lf_node_utils__Path
from typing import Any as __lf_node_utils__Any, Dict as __lf_node_utils__Dict, List as __lf_node_utils__List
__lf_node_utils__read_data_payload = __lf_component_base__read_data_payload

def __lf_node_utils__ensure_component_root() -> __lf_node_utils__Path:
    """Ensure the package parent is importable when Langflow loads nodes by file path."""
    repo_root = __lf_node_utils__Path(__file__).resolve().parent.parent
    repo_root_text = str(repo_root)
    if repo_root_text not in __lf_node_utils__sys.path:
        __lf_node_utils__sys.path.insert(0, repo_root_text)
    return repo_root

def __lf_node_utils__coerce_json_field(value: __lf_node_utils__Any, default: __lf_node_utils__Any) -> __lf_node_utils__Any:
    """Parse dict/list JSON-like input when the source passes plain text."""
    if value is None or value == '':
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return __lf_node_utils__json.loads(str(value))
    except Exception:
        return default

def __lf_node_utils__append_history(history: __lf_node_utils__List[__lf_node_utils__Dict[str, str]], role: str, content: str) -> __lf_node_utils__List[__lf_node_utils__Dict[str, str]]:
    """Append one chat turn without duplicating the latest identical entry."""
    cleaned = str(content or '').strip()
    if not cleaned:
        return history
    if history and history[-1].get('role') == role and (history[-1].get('content') == cleaned):
        return history
    history.append({'role': role, 'content': cleaned})
    return history

def __lf_node_utils__read_message_text(message: __lf_node_utils__Any) -> str:
    """Extract the visible user text from a Langflow Chat Input style payload."""
    if message is None:
        return ''
    text = getattr(message, 'text', None)
    if text is None and isinstance(message, dict):
        text = message.get('text')
    return str(text or '')

def __lf_node_utils__read_domain_text_payload(value: __lf_node_utils__Any) -> str:
    """Extract raw domain-rules text from a node payload."""
    payload = __lf_node_utils__read_data_payload(value)
    text = payload.get('domain_rules_text')
    return str(text or '').strip()

def __lf_node_utils__read_domain_registry_payload(value: __lf_node_utils__Any) -> __lf_node_utils__Dict[str, __lf_node_utils__Any] | __lf_node_utils__List[__lf_node_utils__Any]:
    """Extract parsed domain-registry JSON from a node payload."""
    payload = __lf_node_utils__read_data_payload(value)
    registry_payload = payload.get('domain_registry_payload')
    if isinstance(registry_payload, (dict, list)):
        return registry_payload
    return __lf_node_utils__coerce_json_field(registry_payload, {})

def __lf_node_utils__activate_domain_context_from_state(state: __lf_node_utils__Dict[str, __lf_node_utils__Any]) -> None:
    """Push the current state's domain inputs into the runtime registry layer."""
    set_active_domain_context = __lf_runtime_domain_registry__set_active_domain_context
    set_active_domain_context(domain_rules_text=state.get('domain_rules_text', ''), domain_registry_payload=state.get('domain_registry_payload', {}))

# ---- node component ----
import sys
from pathlib import Path

Component = __lf_component_base__Component
MultilineInput = __lf_component_base__MultilineInput
Output = __lf_component_base__Output
make_data = __lf_component_base__make_data
coerce_json_field = __lf_node_utils__coerce_json_field


class DomainRegistryComponent(Component):
    display_name = "Domain Registry"
    description = "Provide saved manufacturing registry JSON used by the standalone Langflow runtime."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Braces"
    name = "domain_registry"

    inputs = [
        MultilineInput(
            name="registry_json",
            display_name="Registry JSON",
            info="Paste the saved domain registry JSON here. Leave empty to use only built-in rules.",
            value="{}",
        )
    ]
    outputs = [Output(name="registry", display_name="Registry", method="build_registry", types=["Data"], selected="Data")]

    def build_registry(self):
        raw_value = getattr(self, "registry_json", None)
        parsed = coerce_json_field(raw_value, {})
        is_empty = parsed in ({}, [])
        self.status = "Domain registry loaded" if not is_empty else "No domain registry JSON"
        return make_data({"domain_registry_payload": parsed})
