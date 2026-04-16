from __future__ import annotations

# VISIBLE_STANDALONE_RUNTIME: visible per-node standalone code with no hidden source bundle.

# ---- visible runtime: component_base ----
"""Helpers shared by standalone Langflow custom components.

This package is meant to be copied into a Langflow custom-component folder, so
the wrappers below keep the nodes importable both inside Langflow and in a
plain local Python environment where the full Langflow runtime may be missing.
"""
import dataclasses as lf_component_base_import_dataclasses
lf_component_base_dataclass = lf_component_base_import_dataclasses.dataclass
import importlib as lf_component_base_import_importlib
lf_component_base_import_module = lf_component_base_import_importlib.import_module
import typing as lf_component_base_import_typing
lf_component_base_Any = lf_component_base_import_typing.Any
lf_component_base_Dict = lf_component_base_import_typing.Dict

def lf_component_base__load_attr(module_names: list[str], attr_name: str, fallback: lf_component_base_Any) -> lf_component_base_Any:
    """Load a Langflow class while keeping direct-paste validation friendly."""
    for module_name in module_names:
        try:
            return getattr(lf_component_base_import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback

class lf_component_base__FallbackComponent:
    display_name = ''
    description = ''
    documentation = ''
    icon = ''
    name = ''
    inputs = []
    outputs = []
    status = ''

@lf_component_base_dataclass
class lf_component_base__Input:
    name: str
    display_name: str
    info: str = ''
    value: lf_component_base_Any = None
    tool_mode: bool = False
    advanced: bool = False

@lf_component_base_dataclass
class lf_component_base__FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None

class lf_component_base__FallbackData:

    def __init__(self, data: lf_component_base_Dict[str, lf_component_base_Any] | None=None, text: str | None=None):
        self.data = data or {}
        self.text = text

def lf_component_base__make_input(**kwargs):
    return lf_component_base__Input(**kwargs)

def lf_component_base__build_simple_data(payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):

    @lf_component_base_dataclass
    class SimpleData:
        data: lf_component_base_Dict[str, lf_component_base_Any]
        text: str | None = None
    return SimpleData(data=payload, text=text)
lf_component_base_Component = lf_component_base__load_attr(['lfx.custom.custom_component.component', 'lfx.custom', 'langflow.custom'], 'Component', lf_component_base__FallbackComponent)
lf_component_base_DataInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'DataInput', lf_component_base__make_input)
lf_component_base_MessageInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MessageInput', lf_component_base__make_input)
lf_component_base_MessageTextInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MessageTextInput', lf_component_base__make_input)
lf_component_base_MultilineInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'MultilineInput', lf_component_base__make_input)
lf_component_base_SecretStrInput = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'SecretStrInput', lf_component_base__make_input)
lf_component_base_Output = lf_component_base__load_attr(['lfx.io', 'langflow.io'], 'Output', lf_component_base__FallbackOutput)
lf_component_base_Data = lf_component_base__load_attr(['lfx.schema.data', 'lfx.schema', 'langflow.schema'], 'Data', lf_component_base__FallbackData)

def lf_component_base_make_data(payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):
    """Return a Data-like object in both Langflow and local test environments."""
    try:
        return lf_component_base_Data(data=payload, text=text)
    except TypeError:
        try:
            return lf_component_base_Data(payload)
        except Exception:
            return lf_component_base__build_simple_data(payload, text=text)

def lf_component_base_make_branch_data(active: bool, payload: lf_component_base_Dict[str, lf_component_base_Any], text: str | None=None):
    """Emit data only for the active branch output."""
    if not active:
        return None
    return lf_component_base_make_data(payload, text=text)

def lf_component_base_read_data_payload(value: lf_component_base_Any) -> lf_component_base_Dict[str, lf_component_base_Any]:
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

def lf_component_base_read_state_payload(value: lf_component_base_Any) -> lf_component_base_Dict[str, lf_component_base_Any]:
    """Read a Langflow payload and unwrap the nested ``state`` field when present."""
    payload = lf_component_base_read_data_payload(value)
    state = payload.get('state')
    if isinstance(state, dict):
        return state
    return payload if isinstance(payload, dict) else {}

# ---- visible runtime: _runtime ----
"""Standalone runtime copied for Langflow custom components."""

# ---- visible runtime: _runtime.shared.filter_utils ----
import re as lf_runtime_shared_filter_utils_re
import unicodedata as lf_runtime_shared_filter_utils_unicodedata
import typing as lf_runtime_shared_filter_utils_import_typing
lf_runtime_shared_filter_utils_Any = lf_runtime_shared_filter_utils_import_typing.Any
lf_runtime_shared_filter_utils_Iterable = lf_runtime_shared_filter_utils_import_typing.Iterable

def lf_runtime_shared_filter_utils_normalize_text(value: lf_runtime_shared_filter_utils_Any) -> str:
    text = lf_runtime_shared_filter_utils_unicodedata.normalize('NFKC', str(value or ''))
    return lf_runtime_shared_filter_utils_re.sub('\\s+', ' ', text).strip().lower()

def lf_runtime_shared_filter_utils_contains_any_keyword(text: str, keywords: lf_runtime_shared_filter_utils_Iterable[str]) -> bool:
    normalized = lf_runtime_shared_filter_utils_normalize_text(text)
    return any((lf_runtime_shared_filter_utils_normalize_text(keyword) in normalized for keyword in keywords))

# ---- visible runtime: _runtime.domain.knowledge ----
"""제조 도메인 지식과 파라미터 추출 스펙을 모아 둔 파일."""
import typing as lf_runtime_domain_knowledge_import_typing
lf_runtime_domain_knowledge_Dict = lf_runtime_domain_knowledge_import_typing.Dict
lf_runtime_domain_knowledge_List = lf_runtime_domain_knowledge_import_typing.List
lf_runtime_domain_knowledge_Set = lf_runtime_domain_knowledge_import_typing.Set
lf_runtime_domain_knowledge_FILTER_FIELDS = {'date': {'field_name': 'WORK_DT', 'description': '작업일자 (YYYYMMDD 형식)'}, 'process': {'field_name': 'OPER_NAME', 'description': '제조 공정명 또는 공정 그룹'}, 'oper_num': {'field_name': 'OPER_NUM', 'description': '공정번호. 공정과 매핑되는 4자리 숫자 코드'}, 'pkg_type1': {'field_name': 'PKG_TYPE1', 'description': '패키지 기술 유형 (예: FCBGA, LFBGA)'}, 'pkg_type2': {'field_name': 'PKG_TYPE2', 'description': '스택 수/구성 유형 (예: ODP, 16DP, SDP)'}, 'mode': {'field_name': 'MODE', 'description': '제품 모드 (예: DDR4, DDR5, LPDDR5)'}, 'den': {'field_name': 'DEN', 'description': '제품 용량/Density (예: 256G, 512G, 1T)'}, 'tech': {'field_name': 'TECH', 'description': '기술 유형 (예: LC, FO, FC)'}, 'lead': {'field_name': 'LEAD', 'description': 'Ball 또는 Lead의 개수'}, 'mcp_no': {'field_name': 'MCP_NO', 'description': 'MCP 제품 코드'}}
lf_runtime_domain_knowledge_PROCESS_GROUPS = {'DP': {'group_name': 'DP', 'synonyms': ['DP', 'D/P'], 'actual_values': ['WET1', 'WET2', 'L/T1', 'L/T2', 'B/G1', 'B/G2', 'H/S1', 'H/S2', 'W/S1', 'W/S2', 'WSD1', 'WSD2', 'WEC1', 'WEC2', 'WLS1', 'WLS2', 'WVI', 'UV', 'C/C1'], 'description': '전공정 DP 그룹'}, 'WET': {'group_name': 'WET', 'synonyms': ['WET'], 'actual_values': ['WET1', 'WET2'], 'description': 'WET 세부 공정 그룹'}, 'LT': {'group_name': 'LT', 'synonyms': ['LT', 'L/T'], 'actual_values': ['L/T1', 'L/T2'], 'description': 'L/T 세부 공정 그룹'}, 'BG': {'group_name': 'BG', 'synonyms': ['BG', 'B/G'], 'actual_values': ['B/G1', 'B/G2'], 'description': 'B/G 세부 공정 그룹'}, 'HS': {'group_name': 'HS', 'synonyms': ['HS', 'H/S'], 'actual_values': ['H/S1', 'H/S2'], 'description': 'H/S 세부 공정 그룹'}, 'WS': {'group_name': 'WS', 'synonyms': ['WS', 'W/S'], 'actual_values': ['W/S1', 'W/S2'], 'description': 'W/S 세부 공정 그룹'}, 'DA': {'group_name': 'D/A', 'synonyms': ['D/A', 'DA', 'Die Attach', 'DIE ATTACH', '다이어태치', '다이본딩'], 'actual_values': ['D/A1', 'D/A2', 'D/A3', 'D/A4', 'D/A5', 'D/A6'], 'description': 'Die Attach 공정 그룹'}, 'PCO': {'group_name': 'PCO', 'synonyms': ['PCO'], 'actual_values': ['PCO1', 'PCO2', 'PCO3', 'PCO4', 'PCO5', 'PCO6'], 'description': 'PCO 공정 그룹'}, 'DC': {'group_name': 'D/C', 'synonyms': ['D/C', 'DC'], 'actual_values': ['D/C1', 'D/C2', 'D/C3', 'D/C4'], 'description': 'D/C 공정 그룹'}, 'DI': {'group_name': 'D/I', 'synonyms': ['D/I', 'DI'], 'actual_values': ['D/I'], 'description': 'D/I 단일 공정'}, 'DS': {'group_name': 'D/S', 'synonyms': ['D/S', 'DS'], 'actual_values': ['D/S1'], 'description': 'D/S 공정 그룹'}, 'FCB': {'group_name': 'FCB', 'synonyms': ['FCB', 'Flip Chip', '플립칩'], 'actual_values': ['FCB1', 'FCB2', 'FCB/H'], 'description': 'FCB 공정 그룹'}, 'FCBH': {'group_name': 'FCB/H', 'synonyms': ['FCB/H', 'FCBH'], 'actual_values': ['FCB/H'], 'description': 'FCB/H 단일 공정'}, 'BM': {'group_name': 'B/M', 'synonyms': ['B/M', 'BN', '비엠'], 'actual_values': ['B/M'], 'description': 'B/M 단일 공정'}, 'PC': {'group_name': 'P/C', 'synonyms': ['P/C', 'PC'], 'actual_values': ['P/C1', 'P/C2', 'P/C3', 'P/C4', 'P/C5'], 'description': 'P/C 공정 그룹'}, 'WB': {'group_name': 'W/B', 'synonyms': ['W/B', 'WB', 'Wire Bonding', '와이어본딩'], 'actual_values': ['W/B1', 'W/B2', 'W/B3', 'W/B4', 'W/B5', 'W/B6'], 'description': 'Wire Bonding 공정 그룹'}, 'QCSPC': {'group_name': 'QCSPC', 'synonyms': ['QCSPC'], 'actual_values': ['QCSPC1', 'QCSPC2', 'QCSPC3', 'QCSPC4'], 'description': 'QCSPC 공정 그룹'}, 'SAT': {'group_name': 'SAT', 'synonyms': ['SAT'], 'actual_values': ['SAT1', 'SAT2'], 'description': 'SAT 공정 그룹'}, 'PL': {'group_name': 'P/L', 'synonyms': ['P/L', 'PL'], 'actual_values': ['PLH'], 'description': 'P/L 단일 공정'}}
lf_runtime_domain_knowledge_LITERAL_PROCESSES = ['WVI', 'DVI', 'BBMS', 'AVI', 'MDVI', 'MDTI', 'QCSAT', 'LMDI', 'DIC', 'EVI']

def lf_runtime_domain_knowledge__dedupe_processes() -> lf_runtime_domain_knowledge_List[str]:
    ordered: lf_runtime_domain_knowledge_List[str] = []
    for group in lf_runtime_domain_knowledge_PROCESS_GROUPS.values():
        for process_name in group['actual_values']:
            if process_name not in ordered:
                ordered.append(process_name)
    for process_name in lf_runtime_domain_knowledge_LITERAL_PROCESSES:
        if process_name not in ordered:
            ordered.append(process_name)
    return ordered
lf_runtime_domain_knowledge_INDIVIDUAL_PROCESSES = lf_runtime_domain_knowledge__dedupe_processes()
lf_runtime_domain_knowledge_PROCESS_SPECS = [{'family': 'DP', 'OPER_NAME': 'WET1', '라인': 'DP-L1', 'OPER_NUM': '1000'}, {'family': 'DP', 'OPER_NAME': 'WET2', '라인': 'DP-L1', 'OPER_NUM': '1005'}, {'family': 'DP', 'OPER_NAME': 'L/T1', '라인': 'DP-L2', 'OPER_NUM': '1010'}, {'family': 'DP', 'OPER_NAME': 'L/T2', '라인': 'DP-L2', 'OPER_NUM': '1015'}, {'family': 'DP', 'OPER_NAME': 'B/G1', '라인': 'DP-L3', 'OPER_NUM': '1020'}, {'family': 'DP', 'OPER_NAME': 'B/G2', '라인': 'DP-L3', 'OPER_NUM': '1025'}, {'family': 'DP', 'OPER_NAME': 'H/S1', '라인': 'DP-L4', 'OPER_NUM': '1030'}, {'family': 'DP', 'OPER_NAME': 'H/S2', '라인': 'DP-L4', 'OPER_NUM': '1035'}, {'family': 'DP', 'OPER_NAME': 'W/S1', '라인': 'DP-L5', 'OPER_NUM': '1040'}, {'family': 'DP', 'OPER_NAME': 'W/S2', '라인': 'DP-L5', 'OPER_NUM': '1045'}, {'family': 'DP', 'OPER_NAME': 'WSD1', '라인': 'DP-L6', 'OPER_NUM': '1050'}, {'family': 'DP', 'OPER_NAME': 'WSD2', '라인': 'DP-L6', 'OPER_NUM': '1055'}, {'family': 'DP', 'OPER_NAME': 'WEC1', '라인': 'DP-L7', 'OPER_NUM': '1060'}, {'family': 'DP', 'OPER_NAME': 'WEC2', '라인': 'DP-L7', 'OPER_NUM': '1065'}, {'family': 'DP', 'OPER_NAME': 'WLS1', '라인': 'DP-L8', 'OPER_NUM': '1070'}, {'family': 'DP', 'OPER_NAME': 'WLS2', '라인': 'DP-L8', 'OPER_NUM': '1075'}, {'family': 'DP', 'OPER_NAME': 'WVI', '라인': 'DP-L9', 'OPER_NUM': '1080'}, {'family': 'DP', 'OPER_NAME': 'UV', '라인': 'DP-L9', 'OPER_NUM': '1085'}, {'family': 'DP', 'OPER_NAME': 'C/C1', '라인': 'DP-L9', 'OPER_NUM': '1090'}, {'family': 'DA', 'OPER_NAME': 'D/A1', '라인': 'DA-L1', 'OPER_NUM': '2000'}, {'family': 'DA', 'OPER_NAME': 'D/A2', '라인': 'DA-L1', 'OPER_NUM': '2010'}, {'family': 'DA', 'OPER_NAME': 'D/A3', '라인': 'DA-L2', 'OPER_NUM': '2020'}, {'family': 'DA', 'OPER_NAME': 'D/A4', '라인': 'DA-L2', 'OPER_NUM': '2030'}, {'family': 'DA', 'OPER_NAME': 'D/A5', '라인': 'DA-L3', 'OPER_NUM': '2040'}, {'family': 'DA', 'OPER_NAME': 'D/A6', '라인': 'DA-L3', 'OPER_NUM': '2050'}, {'family': 'PCO', 'OPER_NAME': 'PCO1', '라인': 'PCO-L1', 'OPER_NUM': '2100'}, {'family': 'PCO', 'OPER_NAME': 'PCO2', '라인': 'PCO-L1', 'OPER_NUM': '2110'}, {'family': 'PCO', 'OPER_NAME': 'PCO3', '라인': 'PCO-L2', 'OPER_NUM': '2120'}, {'family': 'PCO', 'OPER_NAME': 'PCO4', '라인': 'PCO-L2', 'OPER_NUM': '2130'}, {'family': 'PCO', 'OPER_NAME': 'PCO5', '라인': 'PCO-L3', 'OPER_NUM': '2140'}, {'family': 'PCO', 'OPER_NAME': 'PCO6', '라인': 'PCO-L3', 'OPER_NUM': '2150'}, {'family': 'DC', 'OPER_NAME': 'D/C1', '라인': 'DC-L1', 'OPER_NUM': '2200'}, {'family': 'DC', 'OPER_NAME': 'D/C2', '라인': 'DC-L1', 'OPER_NUM': '2210'}, {'family': 'DC', 'OPER_NAME': 'D/C3', '라인': 'DC-L2', 'OPER_NUM': '2220'}, {'family': 'DC', 'OPER_NAME': 'D/C4', '라인': 'DC-L2', 'OPER_NUM': '2230'}, {'family': 'DI', 'OPER_NAME': 'D/I', '라인': 'DI-L1', 'OPER_NUM': '2300'}, {'family': 'DS', 'OPER_NAME': 'D/S1', '라인': 'DS-L1', 'OPER_NUM': '2400'}, {'family': 'FCB', 'OPER_NAME': 'FCB1', '라인': 'FCB-L1', 'OPER_NUM': '2500'}, {'family': 'FCB', 'OPER_NAME': 'FCB2', '라인': 'FCB-L1', 'OPER_NUM': '2510'}, {'family': 'FCB', 'OPER_NAME': 'FCB/H', '라인': 'FCB-L2', 'OPER_NUM': '2520'}, {'family': 'BM', 'OPER_NAME': 'B/M', '라인': 'BM-L1', 'OPER_NUM': '2600'}, {'family': 'PC', 'OPER_NAME': 'P/C1', '라인': 'PC-L1', 'OPER_NUM': '2700'}, {'family': 'PC', 'OPER_NAME': 'P/C2', '라인': 'PC-L1', 'OPER_NUM': '2710'}, {'family': 'PC', 'OPER_NAME': 'P/C3', '라인': 'PC-L2', 'OPER_NUM': '2720'}, {'family': 'PC', 'OPER_NAME': 'P/C4', '라인': 'PC-L2', 'OPER_NUM': '2730'}, {'family': 'PC', 'OPER_NAME': 'P/C5', '라인': 'PC-L3', 'OPER_NUM': '2740'}, {'family': 'WB', 'OPER_NAME': 'W/B1', '라인': 'WB-L1', 'OPER_NUM': '3000'}, {'family': 'WB', 'OPER_NAME': 'W/B2', '라인': 'WB-L1', 'OPER_NUM': '3010'}, {'family': 'WB', 'OPER_NAME': 'W/B3', '라인': 'WB-L2', 'OPER_NUM': '3020'}, {'family': 'WB', 'OPER_NAME': 'W/B4', '라인': 'WB-L2', 'OPER_NUM': '3030'}, {'family': 'WB', 'OPER_NAME': 'W/B5', '라인': 'WB-L3', 'OPER_NUM': '3040'}, {'family': 'WB', 'OPER_NAME': 'W/B6', '라인': 'WB-L3', 'OPER_NUM': '3050'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC1', '라인': 'QC-L1', 'OPER_NUM': '3100'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC2', '라인': 'QC-L1', 'OPER_NUM': '3110'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC3', '라인': 'QC-L2', 'OPER_NUM': '3120'}, {'family': 'QCSPC', 'OPER_NAME': 'QCSPC4', '라인': 'QC-L2', 'OPER_NUM': '3130'}, {'family': 'SAT', 'OPER_NAME': 'SAT1', '라인': 'SAT-L1', 'OPER_NUM': '3200'}, {'family': 'SAT', 'OPER_NAME': 'SAT2', '라인': 'SAT-L1', 'OPER_NUM': '3210'}, {'family': 'PL', 'OPER_NAME': 'PLH', '라인': 'PL-L1', 'OPER_NUM': '3300'}, {'family': 'ETC', 'OPER_NAME': 'DVI', '라인': 'ETC-L1', 'OPER_NUM': '3400'}, {'family': 'ETC', 'OPER_NAME': 'BBMS', '라인': 'ETC-L1', 'OPER_NUM': '3410'}, {'family': 'ETC', 'OPER_NAME': 'AVI', '라인': 'ETC-L2', 'OPER_NUM': '3420'}, {'family': 'ETC', 'OPER_NAME': 'MDVI', '라인': 'ETC-L2', 'OPER_NUM': '3430'}, {'family': 'ETC', 'OPER_NAME': 'MDTI', '라인': 'ETC-L3', 'OPER_NUM': '3440'}, {'family': 'ETC', 'OPER_NAME': 'QCSAT', '라인': 'ETC-L3', 'OPER_NUM': '3450'}, {'family': 'ETC', 'OPER_NAME': 'LMDI', '라인': 'ETC-L4', 'OPER_NUM': '3460'}, {'family': 'ETC', 'OPER_NAME': 'DIC', '라인': 'ETC-L4', 'OPER_NUM': '3470'}, {'family': 'ETC', 'OPER_NAME': 'EVI', '라인': 'ETC-L5', 'OPER_NUM': '3480'}, {'family': 'ETC', 'OPER_NAME': 'INPUT', '라인': 'ETC-L5', 'OPER_NUM': '3490'}]
lf_runtime_domain_knowledge_PROCESS_GROUP_SYNONYMS = {group_id: list(group['synonyms']) for group_id, group in lf_runtime_domain_knowledge_PROCESS_GROUPS.items()}
lf_runtime_domain_knowledge_PROCESS_OPER_NUM_MAP = {spec['OPER_NAME']: spec['OPER_NUM'] for spec in lf_runtime_domain_knowledge_PROCESS_SPECS}
lf_runtime_domain_knowledge_PRODUCTS = [{'MODE': 'DDR4', 'DEN': '256G', 'TECH': 'LC', 'LEAD': '320', 'MCP_NO': 'A-410A', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'SDP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR4', 'DEN': '512G', 'TECH': 'LC', 'LEAD': '360', 'MCP_NO': 'A-421I', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': 'ODP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR5', 'DEN': '512G', 'TECH': 'FC', 'LEAD': '420', 'MCP_NO': 'A-587N', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': '16DP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR5', 'DEN': '256G', 'TECH': 'FC', 'LEAD': '400', 'MCP_NO': 'A-553P', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'SDP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'DDR5', 'DEN': '1T', 'TECH': 'FC', 'LEAD': '480', 'MCP_NO': 'A-612B', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': 'ODP', 'TSV_DIE_TYP': 'TSV'}, {'MODE': 'LPDDR5', 'DEN': '512G', 'TECH': 'FO', 'LEAD': '560', 'MCP_NO': 'A-7301', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'SDP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'LPDDR5', 'DEN': '256G', 'TECH': 'FO', 'LEAD': '520', 'MCP_NO': 'A-701O', 'PKG_TYPE1': 'LFBGA', 'PKG_TYPE2': 'ODP', 'TSV_DIE_TYP': 'STD'}, {'MODE': 'LPDDR5', 'DEN': '1T', 'TECH': 'FO', 'LEAD': '640', 'MCP_NO': 'A-811V', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': '16DP', 'TSV_DIE_TYP': 'TSV'}, {'MODE': 'DDR4', 'DEN': '1T', 'TECH': 'LC', 'LEAD': '380', 'MCP_NO': 'A-455V', 'PKG_TYPE1': 'FCBGA', 'PKG_TYPE2': '16DP', 'TSV_DIE_TYP': 'STD'}]
lf_runtime_domain_knowledge_ALL_PROCESS_FAMILIES: lf_runtime_domain_knowledge_Set[str] = {spec['family'] for spec in lf_runtime_domain_knowledge_PROCESS_SPECS}
lf_runtime_domain_knowledge_PRODUCT_TECH_FAMILY: lf_runtime_domain_knowledge_Dict[str, lf_runtime_domain_knowledge_Set[str]] = {'LC': set(lf_runtime_domain_knowledge_ALL_PROCESS_FAMILIES), 'FO': set(lf_runtime_domain_knowledge_ALL_PROCESS_FAMILIES), 'FC': set(lf_runtime_domain_knowledge_ALL_PROCESS_FAMILIES)}
lf_runtime_domain_knowledge_TECH_GROUPS = {'LC': {'synonyms': ['LC', '엘씨', 'LC제품', '엘시'], 'actual_values': ['LC'], 'description': 'LC 기술 유형'}, 'FO': {'synonyms': ['FO', '팬아웃', 'FO제품', 'fan-out', 'Fan-Out', '에프오'], 'actual_values': ['FO'], 'description': 'Fan-Out 기술 유형'}, 'FC': {'synonyms': ['FC', '플립칩', 'FC제품', '에프씨'], 'actual_values': ['FC'], 'description': 'Flip Chip 기술 유형'}}
lf_runtime_domain_knowledge_MODE_GROUPS = {'DDR4': {'synonyms': ['DDR4', '디디알4', 'DDR 4'], 'actual_values': ['DDR4'], 'description': 'DDR4 메모리'}, 'DDR5': {'synonyms': ['DDR5', '디디알5', 'DDR 5'], 'actual_values': ['DDR5'], 'description': 'DDR5 메모리'}, 'LPDDR5': {'synonyms': ['LPDDR5', 'LP DDR5', '엘피디디알5', 'LP5', '저전력DDR5'], 'actual_values': ['LPDDR5'], 'description': '저전력 DDR5 메모리'}}
lf_runtime_domain_knowledge_DEN_GROUPS = {'256G': {'synonyms': ['256G', '256기가', '256Gb', '256gb'], 'actual_values': ['256G'], 'description': '256Gb 용량'}, '512G': {'synonyms': ['512G', '512기가', '512Gb', '512gb'], 'actual_values': ['512G'], 'description': '512Gb 용량'}, '1T': {'synonyms': ['1T', '1테라', '1Tb', '1tb', '1TB'], 'actual_values': ['1T'], 'description': '1Tb 용량'}}
lf_runtime_domain_knowledge_PKG_TYPE1_GROUPS = {'FCBGA': {'synonyms': ['FCBGA', 'fcbga'], 'actual_values': ['FCBGA'], 'description': 'FCBGA 패키지 타입'}, 'LFBGA': {'synonyms': ['LFBGA', 'lfbga'], 'actual_values': ['LFBGA'], 'description': 'LFBGA 패키지 타입'}}
lf_runtime_domain_knowledge_PKG_TYPE2_GROUPS = {'ODP': {'synonyms': ['ODP', 'odp'], 'actual_values': ['ODP'], 'description': 'ODP 스택 타입'}, '16DP': {'synonyms': ['16DP', '16dp'], 'actual_values': ['16DP'], 'description': '16DP 스택 타입'}, 'SDP': {'synonyms': ['SDP', 'sdp'], 'actual_values': ['SDP'], 'description': 'SDP 스택 타입'}}
lf_runtime_domain_knowledge_SPECIAL_PRODUCT_ALIASES = {'HBM_OR_3DS': ['hbm제품', 'hbm자재', 'hbm', '3ds', '3ds제품'], 'AUTO_PRODUCT': ['auto향', '오토향', '차량향', 'automotive']}
lf_runtime_domain_knowledge_SPECIAL_PRODUCT_KEYWORD_RULES = [{'target_value': 'HBM_OR_3DS', 'aliases': ['HBM_OR_3DS', 'HBM/3DS', *lf_runtime_domain_knowledge_SPECIAL_PRODUCT_ALIASES['HBM_OR_3DS']]}, {'target_value': 'AUTO_PRODUCT', 'aliases': ['AUTO_PRODUCT', 'AUTO', *lf_runtime_domain_knowledge_SPECIAL_PRODUCT_ALIASES['AUTO_PRODUCT']]}]
lf_runtime_domain_knowledge_PROCESS_KEYWORD_RULES = [{'target_value': 'INPUT', 'aliases': ['투입', 'input', '인풋']}]
lf_runtime_domain_knowledge_OPER_NUM_DETECTION_PATTERNS = ['(?:공정번호|oper_num|oper|operation)\\s*[:=]?\\s*(\\d{4})', '(\\d{4})\\s*번?\\s*공정']
lf_runtime_domain_knowledge_OPER_NUM_VALUES = [spec['OPER_NUM'] for spec in lf_runtime_domain_knowledge_PROCESS_SPECS]

def lf_runtime_domain_knowledge__build_group_field_spec(field_name: str, response_key: str, groups: lf_runtime_domain_knowledge_Dict[str, lf_runtime_domain_knowledge_Dict[str, lf_runtime_domain_knowledge_List[str] | str]], literal_values: lf_runtime_domain_knowledge_List[str] | None=None, keyword_rules: lf_runtime_domain_knowledge_List[lf_runtime_domain_knowledge_Dict[str, lf_runtime_domain_knowledge_List[str] | str]] | None=None) -> lf_runtime_domain_knowledge_Dict[str, object]:
    """그룹형 필드 스펙을 읽기 쉬운 형태로 만든다."""
    return {'field_name': field_name, 'response_key': response_key, 'value_kind': 'multi', 'resolver_kind': 'group', 'groups': groups, 'literal_values': literal_values, 'keyword_rules': keyword_rules, 'allow_text_detection': True}

def lf_runtime_domain_knowledge__build_code_field_spec(field_name: str, response_key: str, candidate_values: lf_runtime_domain_knowledge_List[str], patterns: lf_runtime_domain_knowledge_List[str]) -> lf_runtime_domain_knowledge_Dict[str, object]:
    """코드형 필드 스펙을 읽기 쉬운 형태로 만든다."""
    return {'field_name': field_name, 'response_key': response_key, 'value_kind': 'multi', 'resolver_kind': 'code', 'candidate_values': candidate_values, 'patterns': patterns, 'allow_text_detection': True}

def lf_runtime_domain_knowledge__build_single_field_spec(field_name: str, response_key: str, keyword_rules: lf_runtime_domain_knowledge_List[lf_runtime_domain_knowledge_Dict[str, lf_runtime_domain_knowledge_List[str] | str]] | None=None) -> lf_runtime_domain_knowledge_Dict[str, object]:
    """단일 값 필드 스펙을 읽기 쉬운 형태로 만든다."""
    return {'field_name': field_name, 'response_key': response_key, 'value_kind': 'single', 'resolver_kind': 'single', 'keyword_rules': keyword_rules, 'allow_text_detection': True}
lf_runtime_domain_knowledge_GROUP_PARAMETER_FIELD_SPECS = [lf_runtime_domain_knowledge__build_group_field_spec(field_name='process_name', response_key='process', groups=lf_runtime_domain_knowledge_PROCESS_GROUPS, literal_values=lf_runtime_domain_knowledge_INDIVIDUAL_PROCESSES + ['INPUT'], keyword_rules=lf_runtime_domain_knowledge_PROCESS_KEYWORD_RULES), lf_runtime_domain_knowledge__build_group_field_spec('pkg_type1', 'pkg_type1', lf_runtime_domain_knowledge_PKG_TYPE1_GROUPS), lf_runtime_domain_knowledge__build_group_field_spec('pkg_type2', 'pkg_type2', lf_runtime_domain_knowledge_PKG_TYPE2_GROUPS), lf_runtime_domain_knowledge__build_group_field_spec('mode', 'mode', lf_runtime_domain_knowledge_MODE_GROUPS), lf_runtime_domain_knowledge__build_group_field_spec('den', 'den', lf_runtime_domain_knowledge_DEN_GROUPS), lf_runtime_domain_knowledge__build_group_field_spec('tech', 'tech', lf_runtime_domain_knowledge_TECH_GROUPS)]
lf_runtime_domain_knowledge_CODE_PARAMETER_FIELD_SPECS = [lf_runtime_domain_knowledge__build_code_field_spec(field_name='oper_num', response_key='oper_num', candidate_values=lf_runtime_domain_knowledge_OPER_NUM_VALUES, patterns=lf_runtime_domain_knowledge_OPER_NUM_DETECTION_PATTERNS)]
lf_runtime_domain_knowledge_SINGLE_VALUE_PARAMETER_FIELD_SPECS = [lf_runtime_domain_knowledge__build_single_field_spec('product_name', 'product_name', lf_runtime_domain_knowledge_SPECIAL_PRODUCT_KEYWORD_RULES), lf_runtime_domain_knowledge__build_single_field_spec('line_name', 'line_name'), lf_runtime_domain_knowledge__build_single_field_spec('mcp_no', 'mcp_no')]
lf_runtime_domain_knowledge_PARAMETER_FIELD_SPECS = [*lf_runtime_domain_knowledge_GROUP_PARAMETER_FIELD_SPECS, *lf_runtime_domain_knowledge_CODE_PARAMETER_FIELD_SPECS, *lf_runtime_domain_knowledge_SINGLE_VALUE_PARAMETER_FIELD_SPECS]
lf_runtime_domain_knowledge_QUERY_MODE_SIGNAL_SPECS = {'explicit_date_reference': {'keywords': ['오늘', '어제', 'today', 'yesterday'], 'patterns': ['\\b20\\d{6}\\b'], 'description': '새 날짜를 직접 언급한 경우'}, 'grouping_expression': {'keywords': ['group by', 'by', '기준', '별'], 'patterns': ['([\\w/\\-가-힣]+)\\s*(by|기준|별)'], 'description': '그룹화 또는 breakdown 의도를 드러내는 표현'}, 'retrieval_request': {'keywords': ['생산', '목표', '불량', '설비', '가동률', 'wip', '수율', 'hold', '스크랩', '레시피', 'lot', '조회'], 'patterns': [], 'description': '새 raw dataset 조회 쪽으로 기울게 하는 표현'}, 'followup_filter_intent': {'keywords': ['조건', '필터', '공정', '공정번호', 'oper', 'pkg', '라인', 'mode', 'den', 'tech', 'lead', 'mcp'], 'patterns': [], 'description': '현재 결과에 새 필터를 적용하려는 의도를 드러내는 표현'}, 'fresh_retrieval_hint': {'keywords': ['조회', '데이터', '현황', '새로'], 'patterns': [], 'description': '현재 테이블 재가공보다 새 조회를 더 강하게 시사하는 표현'}}
lf_runtime_domain_knowledge_AUTO_SUFFIXES = {'I', 'O', 'N', 'P', '1', 'V'}
lf_runtime_domain_knowledge_SPECIAL_DOMAIN_RULES = ['투입량, INPUT, 인풋은 INPUT 공정의 생산량(실적)을 의미한다.', 'HBM제품, HBM자재, 3DS, 3DS제품은 TSV_DIE_TYP 값이 TSV인 제품을 의미한다.', 'Auto향은 MCP_NO의 마지막 문자가 I, O, N, P, 1, V 중 하나인 제품을 의미한다.', 'D/S 또는 DS는 기본적으로 D/S1 공정을 의미한다. 사용자가 PKG_TYPE1을 함께 말하면 그 조건도 동시에 적용한다.', 'DVI는 standalone 공정으로 우선 해석하고, D/I 그룹은 D/I 또는 DI로만 해석한다.', '나머지 공정들인 WVI, DVI, BBMS, AVI, MDVI, MDTI, QCSAT, LMDI, DIC, EVI는 공정명 그대로 사용한다.']
lf_runtime_domain_knowledge_DATASET_METADATA = {'production': {'label': '생산', 'keywords': ['생산', 'production', '실적', '투입', 'input', '인풋']}, 'target': {'label': '목표', 'keywords': ['목표', 'target', '계획']}, 'defect': {'label': '불량', 'keywords': ['불량', 'defect', '결함']}, 'equipment': {'label': '설비', 'keywords': ['설비', '가동률', 'equipment', 'downtime']}, 'wip': {'label': 'WIP', 'keywords': ['wip', '재공', '대기']}, 'yield': {'label': '수율', 'keywords': ['수율', 'yield', 'pass rate', '합격률']}, 'hold': {'label': '홀드', 'keywords': ['hold', '홀드', '보류 lot', 'hold lot']}, 'scrap': {'label': '스크랩', 'keywords': ['scrap', '스크랩', '폐기', 'loss cost', '손실비용']}, 'recipe': {'label': '레시피', 'keywords': ['recipe', '레시피', '공정 조건', '조건값', 'parameter', '파라미터']}, 'lot_trace': {'label': 'LOT 이력', 'keywords': ['lot', 'lot trace', 'lot 이력', '추적', 'traceability', '로트']}}
lf_runtime_domain_knowledge_DATASET_COLUMN_ALIAS_SPECS = {'production': {'production': ['production', 'prod', 'prod_qty', 'actual', 'actual_qty', '생산', '생산량', '실적']}, 'target': {'target': ['target', 'plan', 'plan_qty', 'goal', 'goal_qty', '목표', '목표량', '계획']}, 'defect': {'불량수량': ['불량수량', 'defect_qty', 'defect_count', 'ng_qty', 'ng_count'], 'defect_rate': ['defect_rate', 'defect ratio', 'ng_rate', '불량률']}, 'equipment': {'가동률': ['가동률', 'utilization', 'util_rate', 'util', '稼動率']}, 'wip': {'재공수량': ['재공수량', 'wip', 'wip_qty', 'queue_qty', 'in_process_qty']}, 'yield': {'yield_rate': ['yield_rate', 'yield', 'pass_rate', '수율'], 'pass_qty': ['pass_qty', 'pass', 'good_qty', '합격수량', '양품수량'], 'tested_qty': ['tested_qty', 'tested', 'input_qty', '검사수량', '투입수량']}, 'hold': {'hold_qty': ['hold_qty', 'hold', 'hold_count', '보류수량', '홀드수량']}}

def lf_runtime_domain_knowledge_build_domain_knowledge_prompt() -> str:
    lines: lf_runtime_domain_knowledge_List[str] = []
    lines.append('=' * 50)
    lines.append('[도메인 지식: 필터 추출 규칙]')
    lines.append('=' * 50)
    lines.append('\n## 사용 가능한 필터 필드')
    for key, field in lf_runtime_domain_knowledge_FILTER_FIELDS.items():
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
    for group in lf_runtime_domain_knowledge_PROCESS_GROUPS.values():
        lines.append(f"### {group['group_name']}")
        lines.append(f"  유사어: {', '.join(group['synonyms'])}")
        lines.append(f"  실제 값: [{', '.join(group['actual_values'])}]")
        lines.append(f"  설명: {group['description']}")
        lines.append('')
    lines.append('### 개별 공정 목록')
    lines.append(f"  {', '.join(lf_runtime_domain_knowledge_INDIVIDUAL_PROCESSES)}")
    lines.append('\n## 공정번호 (OPER_NUM) 규칙')
    lines.append('공정번호는 4자리 숫자이며 공정명과 매핑된다.')
    lines.append('예시:')
    for process_name, oper_num in list(lf_runtime_domain_knowledge_PROCESS_OPER_NUM_MAP.items())[:12]:
        lines.append(f'  - {process_name} -> {oper_num}')
    lines.append('사용자가 공정번호를 말하면 oper_num에 넣고, 공정명이 함께 있으면 두 조건을 동시에 유지한다.')
    lines.append('\n## PKG_TYPE1 규칙')
    for group_id, group in lf_runtime_domain_knowledge_PKG_TYPE1_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## PKG_TYPE2 규칙')
    for group_id, group in lf_runtime_domain_knowledge_PKG_TYPE2_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## TECH 규칙')
    for group_id, group in lf_runtime_domain_knowledge_TECH_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## MODE 규칙')
    for group_id, group in lf_runtime_domain_knowledge_MODE_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## DEN 규칙')
    for group_id, group in lf_runtime_domain_knowledge_DEN_GROUPS.items():
        lines.append(f"  - {group_id}: 유사어 {', '.join(group['synonyms'])} -> {', '.join(group['actual_values'])}")
    lines.append('\n## 특수 용어 규칙')
    for rule in lf_runtime_domain_knowledge_SPECIAL_DOMAIN_RULES:
        lines.append(f'- {rule}')
    lines.append('\n## 특수 제품/공정 정규화 규칙')
    for rule in lf_runtime_domain_knowledge_SPECIAL_PRODUCT_KEYWORD_RULES:
        lines.append(f"- 제품 별칭 {', '.join(rule['aliases'])} 는 product_name '{rule['target_value']}' 로 정규화한다.")
    for rule in lf_runtime_domain_knowledge_PROCESS_KEYWORD_RULES:
        lines.append(f"- 공정 키워드 {', '.join(rule['aliases'])} 는 process '{rule['target_value']}' 로 정규화한다.")
    lines.append('\n## 공통 추출 규칙')
    lines.append('1. 사용자가 언급하지 않은 필드는 null로 설정한다.')
    lines.append('2. 여러 값을 나열하면 리스트로 추출한다.')
    lines.append('3. 그룹명과 개별값을 구분한다.')
    lines.append('4. 공정, OPER_NUM, PKG_TYPE1, PKG_TYPE2가 함께 나오면 가능한 조건을 모두 유지한다.')
    lines.append('5. mcp_no는 MCP_NO 문자열 그대로 유지한다.')
    return '\n'.join(lines)

# ---- visible runtime: _runtime.shared.column_resolver ----
"""조회 직후 컬럼명을 내부 표준명으로 맞추는 유틸리티."""
import typing as lf_runtime_shared_column_resolver_import_typing
lf_runtime_shared_column_resolver_Any = lf_runtime_shared_column_resolver_import_typing.Any
lf_runtime_shared_column_resolver_Dict = lf_runtime_shared_column_resolver_import_typing.Dict
lf_runtime_shared_column_resolver_List = lf_runtime_shared_column_resolver_import_typing.List
lf_runtime_shared_column_resolver_DATASET_COLUMN_ALIAS_SPECS = lf_runtime_domain_knowledge_DATASET_COLUMN_ALIAS_SPECS
lf_runtime_shared_column_resolver_normalize_text = lf_runtime_shared_filter_utils_normalize_text

def lf_runtime_shared_column_resolver__normalize_column_key(value: lf_runtime_shared_column_resolver_Any) -> str:
    text = lf_runtime_shared_column_resolver_normalize_text(value)
    return text.replace('_', '').replace('-', '').replace('/', '').replace(' ', '')

def lf_runtime_shared_column_resolver_build_column_rename_map(rows: lf_runtime_shared_column_resolver_List[lf_runtime_shared_column_resolver_Dict[str, lf_runtime_shared_column_resolver_Any]], dataset_key: str) -> lf_runtime_shared_column_resolver_Dict[str, str]:
    """실제 데이터 컬럼명과 내부 표준 컬럼명 사이의 rename 규칙을 만든다."""
    if not rows:
        return {}
    first_row = rows[0]
    if not isinstance(first_row, dict):
        return {}
    alias_spec = lf_runtime_shared_column_resolver_DATASET_COLUMN_ALIAS_SPECS.get(dataset_key, {})
    if not alias_spec:
        return {}
    actual_columns = list(first_row.keys())
    normalized_actual_map = {lf_runtime_shared_column_resolver__normalize_column_key(column): column for column in actual_columns}
    rename_map: lf_runtime_shared_column_resolver_Dict[str, str] = {}
    for canonical_column, aliases in alias_spec.items():
        if canonical_column in actual_columns:
            continue
        for alias in aliases:
            matched_column = normalized_actual_map.get(lf_runtime_shared_column_resolver__normalize_column_key(alias))
            if matched_column and matched_column not in rename_map:
                rename_map[matched_column] = canonical_column
                break
    return rename_map

def lf_runtime_shared_column_resolver__rename_row_columns(row: lf_runtime_shared_column_resolver_Dict[str, lf_runtime_shared_column_resolver_Any], rename_map: lf_runtime_shared_column_resolver_Dict[str, str]) -> lf_runtime_shared_column_resolver_Dict[str, lf_runtime_shared_column_resolver_Any]:
    renamed_row: lf_runtime_shared_column_resolver_Dict[str, lf_runtime_shared_column_resolver_Any] = {}
    for column, value in row.items():
        renamed_row[rename_map.get(column, column)] = value
    return renamed_row

def lf_runtime_shared_column_resolver_normalize_dataset_result_columns(result: lf_runtime_shared_column_resolver_Dict[str, lf_runtime_shared_column_resolver_Any], dataset_key: str) -> lf_runtime_shared_column_resolver_Dict[str, lf_runtime_shared_column_resolver_Any]:
    """조회 결과의 컬럼명을 표준명으로 바꿔 뒤쪽 분석 코드가 같은 이름을 보게 한다."""
    if not isinstance(result, dict):
        return result
    rows = result.get('data')
    if not isinstance(rows, list) or not rows:
        return result
    rename_map = lf_runtime_shared_column_resolver_build_column_rename_map(rows, dataset_key)
    if not rename_map:
        return result
    normalized_rows = [lf_runtime_shared_column_resolver__rename_row_columns(row, rename_map) if isinstance(row, dict) else row for row in rows]
    normalized_result = dict(result)
    normalized_result['data'] = normalized_rows
    normalized_result['column_rename_map'] = rename_map
    return normalized_result

# ---- visible runtime: _runtime.shared.number_format ----
import typing as lf_runtime_shared_number_format_import_typing
lf_runtime_shared_number_format_Any = lf_runtime_shared_number_format_import_typing.Any
lf_runtime_shared_number_format_Dict = lf_runtime_shared_number_format_import_typing.Dict
lf_runtime_shared_number_format_List = lf_runtime_shared_number_format_import_typing.List
lf_runtime_shared_number_format_Tuple = lf_runtime_shared_number_format_import_typing.Tuple
lf_runtime_shared_number_format_QUANTITY_KEYWORDS = {'qty', 'quantity', 'count', 'production', 'target', 'inspection', '수량', '재공'}
lf_runtime_shared_number_format_NON_QUANTITY_KEYWORDS = {'rate', 'ratio', 'percent', 'minutes', 'minute', 'hour', 'hours', '가동률', '불량률', '대기시간'}
lf_runtime_shared_number_format_REDUNDANT_UNIT_COLUMNS = {'단위'}

def lf_runtime_shared_number_format_is_quantity_column(column_name: str) -> bool:
    name = str(column_name or '').strip().lower()
    if not name:
        return False
    if any((keyword in name for keyword in lf_runtime_shared_number_format_NON_QUANTITY_KEYWORDS)):
        return False
    return any((keyword in name for keyword in lf_runtime_shared_number_format_QUANTITY_KEYWORDS))

def lf_runtime_shared_number_format_pick_quantity_unit(values: lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Any]) -> str | None:
    numeric_values = [abs(float(value)) for value in values if isinstance(value, (int, float)) and (not isinstance(value, bool))]
    if not numeric_values:
        return None
    max_abs = max(numeric_values)
    if max_abs >= 1000000:
        return 'M'
    if max_abs >= 10000:
        return 'K'
    return None

def lf_runtime_shared_number_format_format_number_by_unit(value: lf_runtime_shared_number_format_Any, unit: str | None) -> lf_runtime_shared_number_format_Any:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return value
    if unit == 'K':
        return f'{value / 1000:,.2f}K'
    if unit == 'M':
        return f'{value / 1000000:,.2f}M'
    if float(value).is_integer():
        return f'{int(value):,}'
    return f'{float(value):,.2f}'

def lf_runtime_shared_number_format_build_quantity_unit_map(rows: lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]]) -> lf_runtime_shared_number_format_Dict[str, str | None]:
    unit_map: lf_runtime_shared_number_format_Dict[str, str | None] = {}
    if not rows:
        return unit_map
    columns = set()
    for row in rows:
        if isinstance(row, dict):
            columns.update(row.keys())
    for column in columns:
        if not lf_runtime_shared_number_format_is_quantity_column(column):
            continue
        values = [row.get(column) for row in rows if isinstance(row, dict)]
        unit_map[str(column)] = lf_runtime_shared_number_format_pick_quantity_unit(values)
    return unit_map

def lf_runtime_shared_number_format_format_rows_with_quantity_units(rows: lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]]) -> lf_runtime_shared_number_format_Tuple[lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]], lf_runtime_shared_number_format_Dict[str, str | None]]:
    unit_map = lf_runtime_shared_number_format_build_quantity_unit_map(rows)
    formatted_rows: lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        formatted_row: lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any] = {}
        for key, value in row.items():
            formatted_row[str(key)] = lf_runtime_shared_number_format_format_number_by_unit(value, unit_map.get(str(key)))
        formatted_rows.append(formatted_row)
    return (formatted_rows, unit_map)

def lf_runtime_shared_number_format_format_rows_for_display(rows: lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]]) -> lf_runtime_shared_number_format_Tuple[lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]], lf_runtime_shared_number_format_Dict[str, str | None]]:
    formatted_rows, unit_map = lf_runtime_shared_number_format_format_rows_with_quantity_units(rows)
    display_rows: lf_runtime_shared_number_format_List[lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any]] = []
    for row in formatted_rows:
        display_row: lf_runtime_shared_number_format_Dict[str, lf_runtime_shared_number_format_Any] = {}
        for key, value in row.items():
            if key in lf_runtime_shared_number_format_REDUNDANT_UNIT_COLUMNS and any((unit_map.get(column) for column in unit_map)):
                continue
            renamed_key = f'{key} ({unit_map[key]})' if unit_map.get(key) else key
            display_row[renamed_key] = value
        display_rows.append(display_row)
    return (display_rows, unit_map)

def lf_runtime_shared_number_format_format_summary_quantity(value: float | int) -> str:
    unit = lf_runtime_shared_number_format_pick_quantity_unit([value])
    formatted = lf_runtime_shared_number_format_format_number_by_unit(value, unit)
    return str(formatted)

# ---- visible runtime: _runtime.shared.config ----
import os as lf_runtime_shared_config_os
import typing as lf_runtime_shared_config_import_typing
lf_runtime_shared_config_Any = lf_runtime_shared_config_import_typing.Any
lf_runtime_shared_config_Dict = lf_runtime_shared_config_import_typing.Dict
import dotenv as lf_runtime_shared_config_import_dotenv
lf_runtime_shared_config_load_dotenv = lf_runtime_shared_config_import_dotenv.load_dotenv
lf_runtime_shared_config_load_dotenv()
lf_runtime_shared_config_MODEL_TASK_GROUPS = {'fast': {'parameter_extract', 'query_mode_review', 'response_summary'}, 'strong': {'retrieval_plan', 'sufficiency_review', 'analysis_code', 'analysis_retry', 'domain_registry_parse'}}
lf_runtime_shared_config_ACTIVE_LLM_CONFIG: lf_runtime_shared_config_Dict[str, lf_runtime_shared_config_Any] = {}

def lf_runtime_shared_config__clean_text(value: lf_runtime_shared_config_Any) -> str:
    if value is None:
        return ''
    if hasattr(value, 'get_secret_value'):
        try:
            return str(value.get_secret_value() or '').strip()
        except Exception:
            return ''
    return str(value or '').strip()

def lf_runtime_shared_config_set_active_llm_config(config: lf_runtime_shared_config_Dict[str, lf_runtime_shared_config_Any] | None=None) -> None:
    """Store per-run LLM settings passed through the Langflow state payload."""
    global lf_runtime_shared_config_ACTIVE_LLM_CONFIG
    if not isinstance(config, dict):
        lf_runtime_shared_config_ACTIVE_LLM_CONFIG = {}
        return
    lf_runtime_shared_config_ACTIVE_LLM_CONFIG = {'api_key': lf_runtime_shared_config__clean_text(config.get('api_key')), 'fast_model': lf_runtime_shared_config__clean_text(config.get('fast_model')) or 'gemini-flash-latest', 'strong_model': lf_runtime_shared_config__clean_text(config.get('strong_model')) or lf_runtime_shared_config__clean_text(config.get('fast_model')) or 'gemini-flash-latest'}

def lf_runtime_shared_config_get_active_llm_config() -> lf_runtime_shared_config_Dict[str, str]:
    return {'api_key': lf_runtime_shared_config__clean_text(lf_runtime_shared_config_ACTIVE_LLM_CONFIG.get('api_key')) or lf_runtime_shared_config_os.getenv('LLM_API_KEY', '').strip(), 'fast_model': lf_runtime_shared_config__clean_text(lf_runtime_shared_config_ACTIVE_LLM_CONFIG.get('fast_model')) or lf_runtime_shared_config_os.getenv('LLM_FAST_MODEL', '').strip() or 'gemini-flash-latest', 'strong_model': lf_runtime_shared_config__clean_text(lf_runtime_shared_config_ACTIVE_LLM_CONFIG.get('strong_model')) or lf_runtime_shared_config_os.getenv('LLM_STRONG_MODEL', '').strip() or lf_runtime_shared_config__clean_text(lf_runtime_shared_config_ACTIVE_LLM_CONFIG.get('fast_model')) or lf_runtime_shared_config_os.getenv('LLM_FAST_MODEL', '').strip() or 'gemini-flash-latest'}

def lf_runtime_shared_config__resolve_model_name(task: str) -> str:
    """Return the model name that fits the task."""
    config = lf_runtime_shared_config_get_active_llm_config()
    fast_model = config['fast_model']
    strong_model = config['strong_model']
    normalized_task = str(task or '').strip().lower()
    if normalized_task in lf_runtime_shared_config_MODEL_TASK_GROUPS['strong']:
        return strong_model
    return fast_model

def lf_runtime_shared_config_get_llm(task: str='general', temperature: float=0.0):
    """Create an LLM client for one task category."""
    api_key = lf_runtime_shared_config_get_active_llm_config()['api_key']
    if not api_key:
        raise ValueError('LLM API key is not set. Enter it in the Langflow LLM settings input or Global Variables.')
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as exc:
        raise ImportError('langchain_google_genai package is required to build the LLM client.') from exc
    return ChatGoogleGenerativeAI(model=lf_runtime_shared_config__resolve_model_name(task), google_api_key=api_key, temperature=temperature)
lf_runtime_shared_config_SYSTEM_PROMPT = 'You are an AI assistant for manufacturing data retrieval and follow-up analysis.\n\nRules:\n- First decide whether the user needs fresh source retrieval or a follow-up transformation on current data.\n- When retrieval is needed, extract only retrieval-safe parameters and use them to load raw source data.\n- When current data is already sufficient, answer through pandas-style follow-up analysis.\n- Never invent missing datasets or columns.\n- Always explain results based on the current result table.\n'

# ---- visible runtime: _runtime.domain.registry ----
import copy as lf_runtime_domain_registry_copy
import json as lf_runtime_domain_registry_json
import datetime as lf_runtime_domain_registry_import_datetime
lf_runtime_domain_registry_datetime = lf_runtime_domain_registry_import_datetime.datetime
import typing as lf_runtime_domain_registry_import_typing
lf_runtime_domain_registry_Any = lf_runtime_domain_registry_import_typing.Any
lf_runtime_domain_registry_Dict = lf_runtime_domain_registry_import_typing.Dict
lf_runtime_domain_registry_Iterable = lf_runtime_domain_registry_import_typing.Iterable
lf_runtime_domain_registry_List = lf_runtime_domain_registry_import_typing.List
import langchain_core.messages as lf_runtime_domain_registry_import_langchain_core_messages
lf_runtime_domain_registry_HumanMessage = lf_runtime_domain_registry_import_langchain_core_messages.HumanMessage
lf_runtime_domain_registry_SystemMessage = lf_runtime_domain_registry_import_langchain_core_messages.SystemMessage
lf_runtime_domain_registry_SYSTEM_PROMPT = lf_runtime_shared_config_SYSTEM_PROMPT
lf_runtime_domain_registry_get_llm = lf_runtime_shared_config_get_llm
lf_runtime_domain_registry_normalize_text = lf_runtime_shared_filter_utils_normalize_text
lf_runtime_domain_registry_DATASET_METADATA = lf_runtime_domain_knowledge_DATASET_METADATA
lf_runtime_domain_registry_DEN_GROUPS = lf_runtime_domain_knowledge_DEN_GROUPS
lf_runtime_domain_registry_MODE_GROUPS = lf_runtime_domain_knowledge_MODE_GROUPS
lf_runtime_domain_registry_PKG_TYPE1_GROUPS = lf_runtime_domain_knowledge_PKG_TYPE1_GROUPS
lf_runtime_domain_registry_PKG_TYPE2_GROUPS = lf_runtime_domain_knowledge_PKG_TYPE2_GROUPS
lf_runtime_domain_registry_PROCESS_GROUPS = lf_runtime_domain_knowledge_PROCESS_GROUPS
lf_runtime_domain_registry_SPECIAL_PRODUCT_ALIASES = lf_runtime_domain_knowledge_SPECIAL_PRODUCT_ALIASES
lf_runtime_domain_registry_TECH_GROUPS = lf_runtime_domain_knowledge_TECH_GROUPS
lf_runtime_domain_registry_SUPPORTED_VALUE_FIELDS = {'process_name', 'mode', 'den', 'tech', 'pkg_type1', 'pkg_type2', 'product_name', 'line_name', 'oper_num', 'mcp_no'}
lf_runtime_domain_registry_FIELD_NAME_ALIASES = {'process': 'process_name', 'process_name': 'process_name', 'oper_name': 'process_name', 'mode': 'mode', 'den': 'den', 'density': 'den', 'tech': 'tech', 'pkg1': 'pkg_type1', 'pkg_type1': 'pkg_type1', 'pkg2': 'pkg_type2', 'pkg_type2': 'pkg_type2', 'product': 'product_name', 'product_name': 'product_name', 'line': 'line_name', 'line_name': 'line_name', 'oper_num': 'oper_num', 'mcp': 'mcp_no', 'mcp_no': 'mcp_no'}
lf_runtime_domain_registry_VALID_CALCULATION_MODES = {'', 'ratio', 'difference', 'sum', 'mean', 'count', 'condition_flag', 'threshold_flag', 'count_if', 'sum_if', 'mean_if', 'custom'}
lf_runtime_domain_registry_VALID_JOIN_TYPES = {'left', 'inner', 'right', 'outer'}
lf_runtime_domain_registry_DEFAULT_ANALYSIS_RULES = [{'name': 'achievement_rate', 'display_name': 'achievement rate', 'synonyms': ['achievement rate', '달성율', '달성률', '생산 달성율', '생산 달성률', '목표 대비 생산'], 'required_datasets': ['production', 'target'], 'required_columns': ['production', 'target'], 'source_columns': [{'dataset_key': 'production', 'column': 'production', 'role': 'numerator'}, {'dataset_key': 'target', 'column': 'target', 'role': 'denominator'}], 'calculation_mode': 'ratio', 'output_column': 'achievement_rate', 'default_group_by': ['OPER_NAME'], 'condition': '', 'decision_rule': '', 'formula': 'production / target', 'pandas_hint': 'group by OPER_NAME and calculate production / target', 'description': 'Calculate production achievement rate using production and target.', 'source': 'builtin'}, {'name': 'yield_rate', 'display_name': 'yield rate', 'synonyms': ['yield', 'yield rate', '수율'], 'required_datasets': ['yield'], 'required_columns': ['yield_rate', 'pass_qty', 'tested_qty'], 'source_columns': [{'dataset_key': 'yield', 'column': 'yield_rate', 'role': 'preferred_metric'}, {'dataset_key': 'yield', 'column': 'pass_qty', 'role': 'pass_qty'}, {'dataset_key': 'yield', 'column': 'tested_qty', 'role': 'tested_qty'}], 'calculation_mode': 'ratio', 'output_column': 'yield_rate', 'default_group_by': ['OPER_NAME'], 'condition': '', 'decision_rule': '', 'formula': 'yield_rate or pass_qty / tested_qty', 'pandas_hint': 'group by OPER_NAME and average yield_rate', 'description': 'Analyze yield-focused questions with yield data.', 'source': 'builtin'}, {'name': 'production_saturation_rate', 'display_name': 'production saturation rate', 'synonyms': ['production saturation', 'production saturation rate', '포화율', '생산 포화율', '생산포화율'], 'required_datasets': ['production', 'wip'], 'required_columns': ['production', '재공수량'], 'source_columns': [{'dataset_key': 'production', 'column': 'production', 'role': 'numerator'}, {'dataset_key': 'wip', 'column': '재공수량', 'role': 'denominator'}], 'calculation_mode': 'ratio', 'output_column': 'production_saturation_rate', 'default_group_by': ['OPER_NAME'], 'condition': '', 'decision_rule': '', 'formula': 'production / 재공수량', 'pandas_hint': 'group by OPER_NAME and calculate production / 재공수량', 'description': 'Calculate production saturation rate using production and WIP quantity.', 'source': 'builtin'}]
lf_runtime_domain_registry_DEFAULT_JOIN_RULES = [{'name': 'production_target_join', 'base_dataset': 'production', 'join_dataset': 'target', 'join_type': 'left', 'join_keys': ['WORK_DT', 'OPER_NAME', '공정군', '라인', 'MODE', 'DEN'], 'description': 'Join production and target rows with common manufacturing dimensions.', 'source': 'builtin'}, {'name': 'production_wip_join', 'base_dataset': 'production', 'join_dataset': 'wip', 'join_type': 'left', 'join_keys': ['WORK_DT', 'OPER_NAME', '공정군', '라인', 'MODE', 'DEN'], 'description': 'Join production and WIP rows with common manufacturing dimensions.', 'source': 'builtin'}]

def lf_runtime_domain_registry__empty_registry() -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    return {'entries': [], 'dataset_keywords': [], 'value_groups': [], 'analysis_rules': [], 'join_rules': [], 'notes': [], 'domain_rules_text': ''}
lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any] = lf_runtime_domain_registry__empty_registry()

def lf_runtime_domain_registry__get_llm_for_task(task: str):
    try:
        return lf_runtime_domain_registry_get_llm(task=task)
    except TypeError:
        return lf_runtime_domain_registry_get_llm()

def lf_runtime_domain_registry__as_list(value: lf_runtime_domain_registry_Any) -> lf_runtime_domain_registry_List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []

def lf_runtime_domain_registry__dedupe(values: lf_runtime_domain_registry_Iterable[str]) -> lf_runtime_domain_registry_List[str]:
    seen: lf_runtime_domain_registry_List[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen

def lf_runtime_domain_registry__parse_json_block(text: str) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
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
        return lf_runtime_domain_registry_json.loads(cleaned[start:end + 1])
    except Exception:
        return {}

def lf_runtime_domain_registry__extract_text(content: lf_runtime_domain_registry_Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join((str(item.get('text', '')) if isinstance(item, dict) else str(item) for item in content))
    return str(content)

def lf_runtime_domain_registry__field_name(value: lf_runtime_domain_registry_Any) -> str:
    return lf_runtime_domain_registry_FIELD_NAME_ALIASES.get(lf_runtime_domain_registry_normalize_text(value), lf_runtime_domain_registry_normalize_text(value))

def lf_runtime_domain_registry__normalize_source_columns(raw_columns: lf_runtime_domain_registry_Any) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, str]]:
    items: lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, str]] = []
    for item in raw_columns or []:
        if not isinstance(item, dict):
            continue
        dataset_key = lf_runtime_domain_registry_normalize_text(item.get('dataset_key'))
        column = str(item.get('column', '')).strip()
        role = str(item.get('role', '')).strip()
        if dataset_key and column:
            items.append({'dataset_key': dataset_key, 'column': column, 'role': role})
    return items

def lf_runtime_domain_registry__normalize_value_group(raw_group: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    canonical = str(raw_group.get('canonical', '')).strip()
    return {'field': lf_runtime_domain_registry__field_name(raw_group.get('field')), 'canonical': canonical, 'synonyms': lf_runtime_domain_registry__dedupe([canonical, *lf_runtime_domain_registry__as_list(raw_group.get('synonyms'))]), 'values': lf_runtime_domain_registry__dedupe(lf_runtime_domain_registry__as_list(raw_group.get('values'))), 'description': str(raw_group.get('description', '')).strip()}

def lf_runtime_domain_registry__normalize_analysis_rule(raw_rule: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    name = str(raw_rule.get('name', '')).strip()
    display_name = str(raw_rule.get('display_name', name)).strip() or name
    calc_mode = str(raw_rule.get('calculation_mode', '')).strip()
    if calc_mode not in lf_runtime_domain_registry_VALID_CALCULATION_MODES:
        calc_mode = 'custom' if calc_mode else ''
    return {'name': name, 'display_name': display_name, 'synonyms': lf_runtime_domain_registry__dedupe([name, display_name, *lf_runtime_domain_registry__as_list(raw_rule.get('synonyms'))]), 'required_datasets': [lf_runtime_domain_registry_normalize_text(item) for item in lf_runtime_domain_registry__as_list(raw_rule.get('required_datasets'))], 'required_columns': lf_runtime_domain_registry__dedupe(lf_runtime_domain_registry__as_list(raw_rule.get('required_columns'))), 'source_columns': lf_runtime_domain_registry__normalize_source_columns(raw_rule.get('source_columns')), 'calculation_mode': calc_mode, 'output_column': str(raw_rule.get('output_column', '')).strip(), 'default_group_by': lf_runtime_domain_registry__dedupe(lf_runtime_domain_registry__as_list(raw_rule.get('default_group_by'))), 'condition': str(raw_rule.get('condition', '')).strip(), 'decision_rule': str(raw_rule.get('decision_rule', '')).strip(), 'formula': str(raw_rule.get('formula', '')).strip(), 'pandas_hint': str(raw_rule.get('pandas_hint', '')).strip(), 'description': str(raw_rule.get('description', '')).strip(), 'source': str(raw_rule.get('source', 'custom')).strip() or 'custom'}

def lf_runtime_domain_registry__normalize_join_rule(raw_rule: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    join_type = str(raw_rule.get('join_type', 'left')).strip().lower()
    if join_type not in lf_runtime_domain_registry_VALID_JOIN_TYPES:
        join_type = 'left'
    return {'name': str(raw_rule.get('name', '')).strip(), 'base_dataset': lf_runtime_domain_registry_normalize_text(raw_rule.get('base_dataset')), 'join_dataset': lf_runtime_domain_registry_normalize_text(raw_rule.get('join_dataset')), 'join_type': join_type, 'join_keys': lf_runtime_domain_registry__dedupe(lf_runtime_domain_registry__as_list(raw_rule.get('join_keys'))), 'description': str(raw_rule.get('description', '')).strip(), 'source': str(raw_rule.get('source', 'custom')).strip() or 'custom'}

def lf_runtime_domain_registry__normalize_entry(payload: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any], raw_text: str='') -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    return {'id': str(payload.get('id', '')).strip() or lf_runtime_domain_registry_datetime.now().strftime('%Y%m%d%H%M%S%f'), 'title': str(payload.get('title', '')).strip() or raw_text[:30].strip() or 'domain note', 'created_at': str(payload.get('created_at', '')).strip() or lf_runtime_domain_registry_datetime.now().isoformat(), 'raw_text': str(payload.get('raw_text', '')).strip() or raw_text, 'dataset_keywords': [{'dataset_key': lf_runtime_domain_registry_normalize_text(item.get('dataset_key')), 'keywords': lf_runtime_domain_registry__dedupe(lf_runtime_domain_registry__as_list(item.get('keywords')))} for item in payload.get('dataset_keywords', []) if isinstance(item, dict)], 'value_groups': [lf_runtime_domain_registry__normalize_value_group(item) for item in payload.get('value_groups', []) if isinstance(item, dict)], 'analysis_rules': [lf_runtime_domain_registry__normalize_analysis_rule(item) for item in payload.get('analysis_rules', []) if isinstance(item, dict)], 'join_rules': [lf_runtime_domain_registry__normalize_join_rule(item) for item in payload.get('join_rules', []) if isinstance(item, dict)], 'notes': lf_runtime_domain_registry__dedupe(lf_runtime_domain_registry__as_list(payload.get('notes')))}

def lf_runtime_domain_registry__merge_registry(registry: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any], entry: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]) -> None:
    registry['entries'].append(entry)
    registry['dataset_keywords'].extend(entry.get('dataset_keywords', []))
    registry['value_groups'].extend(entry.get('value_groups', []))
    registry['analysis_rules'].extend(entry.get('analysis_rules', []))
    registry['join_rules'].extend(entry.get('join_rules', []))
    registry['notes'].extend(entry.get('notes', []))

def lf_runtime_domain_registry__normalize_registry_payload(payload: lf_runtime_domain_registry_Any) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    registry = lf_runtime_domain_registry__empty_registry()
    if payload in (None, '', {}, []):
        return registry
    if isinstance(payload, str):
        parsed = lf_runtime_domain_registry__parse_json_block(payload)
        if parsed:
            payload = parsed
        else:
            registry['notes'] = lf_runtime_domain_registry__dedupe([str(payload).strip()])
            return registry
    candidates: lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]] = []
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
        lf_runtime_domain_registry__merge_registry(registry, lf_runtime_domain_registry__normalize_entry(item, str(item.get('raw_text', ''))))
    registry['notes'] = lf_runtime_domain_registry__dedupe(registry['notes'])
    return registry

def lf_runtime_domain_registry_set_active_domain_context(domain_rules_text: str | None=None, domain_registry_payload: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any] | lf_runtime_domain_registry_List[lf_runtime_domain_registry_Any] | str | None=None) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    global lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT
    lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT = lf_runtime_domain_registry__normalize_registry_payload(domain_registry_payload)
    lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT['domain_rules_text'] = str(domain_rules_text or '').strip()
    return lf_runtime_domain_registry_load_domain_registry()

def lf_runtime_domain_registry_clear_active_domain_context() -> None:
    global lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT
    lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT = lf_runtime_domain_registry__empty_registry()

def lf_runtime_domain_registry_load_domain_registry() -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    return lf_runtime_domain_registry_copy.deepcopy(lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT)

def lf_runtime_domain_registry_validate_domain_payload(payload: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any], registry: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any] | None=None) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, str]]:
    registry = registry or lf_runtime_domain_registry_load_domain_registry()
    issues: lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, str]] = []
    owners: lf_runtime_domain_registry_Dict[str, str] = {}
    for dataset_key, keywords in lf_runtime_domain_registry__build_builtin_dataset_keywords().items():
        for keyword in keywords:
            owners[lf_runtime_domain_registry_normalize_text(keyword)] = dataset_key
    for item in registry.get('dataset_keywords', []):
        for keyword in item.get('keywords', []):
            owners[lf_runtime_domain_registry_normalize_text(keyword)] = item.get('dataset_key', '')
    for item in payload.get('dataset_keywords', []):
        dataset_key = item.get('dataset_key', '')
        if dataset_key not in lf_runtime_domain_registry_DATASET_METADATA:
            issues.append({'severity': 'error', 'message': f'Unknown dataset key: {dataset_key}'})
        for keyword in item.get('keywords', []):
            owner = owners.get(lf_runtime_domain_registry_normalize_text(keyword))
            if owner and owner != dataset_key:
                issues.append({'severity': 'error', 'message': f'Keyword conflict: `{keyword}` is already used by `{owner}`.'})
    for group in payload.get('value_groups', []):
        if group.get('field') not in lf_runtime_domain_registry_SUPPORTED_VALUE_FIELDS:
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

def lf_runtime_domain_registry__detect_join_keys_from_text(raw_text: str) -> lf_runtime_domain_registry_List[str]:
    candidates = ['WORK_DT', 'OPER_NAME', 'MODE', 'FAMILY', 'FACTORY', 'ORG', 'TECH', 'DEN', 'LEAD']
    normalized = lf_runtime_domain_registry_normalize_text(raw_text)
    return [candidate for candidate in candidates if lf_runtime_domain_registry_normalize_text(candidate) in normalized]

def lf_runtime_domain_registry__infer_join_type_from_text(raw_text: str) -> str:
    normalized = lf_runtime_domain_registry_normalize_text(raw_text)
    if 'inner' in normalized:
        return 'inner'
    if 'outer' in normalized:
        return 'outer'
    if 'right' in normalized:
        return 'right'
    return 'left'

def lf_runtime_domain_registry__infer_join_rules_from_text(raw_text: str, payload: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]:
    rules: lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]] = []
    for analysis_rule in payload.get('analysis_rules', []):
        datasets = analysis_rule.get('required_datasets', [])
        if len(datasets) < 2:
            continue
        rules.append({'name': f'{datasets[0]}_{datasets[1]}_join', 'base_dataset': datasets[0], 'join_dataset': datasets[1], 'join_type': lf_runtime_domain_registry__infer_join_type_from_text(raw_text), 'join_keys': lf_runtime_domain_registry__detect_join_keys_from_text(raw_text) or ['WORK_DT', 'OPER_NAME'], 'description': f'Inferred from free-text note: {raw_text[:80]}', 'source': 'custom'})
    return rules

def lf_runtime_domain_registry_parse_domain_text_to_payload(raw_text: str) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    prompt = f'Extract a structured manufacturing domain note into JSON only.\n\nFields:\n- title\n- dataset_keywords: [{{dataset_key, keywords}}]\n- value_groups: [{{field, canonical, synonyms, values, description}}]\n- analysis_rules: [{{name, display_name, synonyms, required_datasets, required_columns, source_columns, calculation_mode, output_column, default_group_by, condition, decision_rule, formula, pandas_hint, description}}]\n- join_rules: [{{name, base_dataset, join_dataset, join_type, join_keys, description}}]\n- notes\n\nText:\n{raw_text}\n'
    try:
        llm = lf_runtime_domain_registry__get_llm_for_task('domain_registry_parse')
        response = llm.invoke([lf_runtime_domain_registry_SystemMessage(content=lf_runtime_domain_registry_SYSTEM_PROMPT), lf_runtime_domain_registry_HumanMessage(content=prompt)])
        parsed = lf_runtime_domain_registry__parse_json_block(lf_runtime_domain_registry__extract_text(response.content))
    except Exception:
        parsed = {}
    normalized = lf_runtime_domain_registry__normalize_entry(parsed, raw_text)
    if not normalized.get('join_rules'):
        normalized['join_rules'] = lf_runtime_domain_registry__infer_join_rules_from_text(raw_text, normalized)
    return normalized

def lf_runtime_domain_registry_preview_domain_submission(raw_text: str) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    payload = lf_runtime_domain_registry_parse_domain_text_to_payload(raw_text)
    issues = lf_runtime_domain_registry_validate_domain_payload(payload)
    return {'success': True, 'payload': payload, 'issues': issues, 'can_save': not any((item['severity'] == 'error' for item in issues))}

def lf_runtime_domain_registry_register_domain_submission(raw_text: str) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    preview = lf_runtime_domain_registry_preview_domain_submission(raw_text)
    if not preview['can_save']:
        return {'success': False, 'payload': preview['payload'], 'issues': preview['issues'], 'message': 'Validation failed.'}
    global lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT
    updated = lf_runtime_domain_registry_load_domain_registry()
    lf_runtime_domain_registry__merge_registry(updated, preview['payload'])
    updated['notes'] = lf_runtime_domain_registry__dedupe(updated['notes'])
    lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT = updated
    return {'success': True, 'payload': preview['payload'], 'issues': preview['issues'], 'message': 'Saved in active context.'}

def lf_runtime_domain_registry_delete_domain_entry(entry_id: str) -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    global lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT
    current = lf_runtime_domain_registry_load_domain_registry()
    entries = [entry for entry in current.get('entries', []) if entry.get('id') != entry_id]
    if len(entries) == len(current.get('entries', [])):
        return {'success': False, 'deleted': False, 'message': 'Entry not found.'}
    rebuilt = lf_runtime_domain_registry__empty_registry()
    rebuilt['domain_rules_text'] = current.get('domain_rules_text', '')
    for entry in entries:
        lf_runtime_domain_registry__merge_registry(rebuilt, entry)
    rebuilt['notes'] = lf_runtime_domain_registry__dedupe(rebuilt['notes'])
    lf_runtime_domain_registry_ACTIVE_DOMAIN_CONTEXT = rebuilt
    return {'success': True, 'deleted': True, 'message': 'Deleted from active context.'}

def lf_runtime_domain_registry_list_domain_entries() -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]:
    return lf_runtime_domain_registry_load_domain_registry()['entries']

def lf_runtime_domain_registry__build_builtin_value_groups() -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]]:
    registry: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]] = {field: [] for field in lf_runtime_domain_registry_SUPPORTED_VALUE_FIELDS}

    def add_group(field: str, canonical: str, synonyms: lf_runtime_domain_registry_List[str], values: lf_runtime_domain_registry_List[str], description: str) -> None:
        registry[field].append({'field': field, 'canonical': canonical, 'synonyms': lf_runtime_domain_registry__dedupe([canonical, *synonyms]), 'values': lf_runtime_domain_registry__dedupe(values), 'description': description, 'source': 'builtin'})
    for key, group in lf_runtime_domain_registry_PROCESS_GROUPS.items():
        add_group('process_name', group.get('group_name', key), group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in lf_runtime_domain_registry_MODE_GROUPS.items():
        add_group('mode', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in lf_runtime_domain_registry_DEN_GROUPS.items():
        add_group('den', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in lf_runtime_domain_registry_TECH_GROUPS.items():
        add_group('tech', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in lf_runtime_domain_registry_PKG_TYPE1_GROUPS.items():
        add_group('pkg_type1', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    for key, group in lf_runtime_domain_registry_PKG_TYPE2_GROUPS.items():
        add_group('pkg_type2', key, group.get('synonyms', []), group.get('actual_values', []), group.get('description', ''))
    registry['product_name'].append({'field': 'product_name', 'canonical': 'HBM_OR_3DS', 'synonyms': ['HBM_OR_3DS', 'HBM/3DS', *lf_runtime_domain_registry_SPECIAL_PRODUCT_ALIASES['HBM_OR_3DS']], 'values': ['HBM_OR_3DS'], 'description': 'TSV-based products such as HBM and 3DS.', 'source': 'builtin'})
    registry['product_name'].append({'field': 'product_name', 'canonical': 'AUTO_PRODUCT', 'synonyms': ['AUTO_PRODUCT', 'AUTO', *lf_runtime_domain_registry_SPECIAL_PRODUCT_ALIASES['AUTO_PRODUCT']], 'values': ['AUTO_PRODUCT'], 'description': 'Automotive products.', 'source': 'builtin'})
    return registry

def lf_runtime_domain_registry__build_builtin_dataset_keywords() -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_List[str]]:
    return {key: list(meta.get('keywords', [])) for key, meta in lf_runtime_domain_registry_DATASET_METADATA.items()}

def lf_runtime_domain_registry_get_dataset_keyword_map() -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_List[str]]:
    registry = lf_runtime_domain_registry_load_domain_registry()
    keyword_map = lf_runtime_domain_registry__build_builtin_dataset_keywords()
    for item in registry.get('dataset_keywords', []):
        dataset_key = item.get('dataset_key', '')
        keyword_map.setdefault(dataset_key, [])
        for keyword in item.get('keywords', []):
            if keyword not in keyword_map[dataset_key]:
                keyword_map[dataset_key].append(keyword)
    return keyword_map

def lf_runtime_domain_registry_get_registered_value_groups(field_name: str | None=None, include_builtin: bool=False) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]:
    registry = lf_runtime_domain_registry_load_domain_registry()
    groups: lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]] = []
    if include_builtin:
        builtin = lf_runtime_domain_registry__build_builtin_value_groups()
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

def lf_runtime_domain_registry_expand_registered_values(field_name: str, raw_values: lf_runtime_domain_registry_Any) -> lf_runtime_domain_registry_List[str] | None:
    requested = lf_runtime_domain_registry__as_list(raw_values)
    if not requested:
        return None
    normalized_field = lf_runtime_domain_registry__field_name(field_name)
    expanded: lf_runtime_domain_registry_List[str] = []
    for raw_value in requested:
        matched = False
        raw_key = lf_runtime_domain_registry_normalize_text(raw_value)
        for group in lf_runtime_domain_registry_get_registered_value_groups(normalized_field, include_builtin=True):
            aliases = [group.get('canonical', ''), *group.get('synonyms', []), *group.get('values', [])]
            if any((raw_key == lf_runtime_domain_registry_normalize_text(alias) for alias in aliases)):
                expanded.extend(group.get('values', []))
                matched = True
                break
        if not matched:
            expanded.append(raw_value)
    expanded = lf_runtime_domain_registry__dedupe(expanded)
    return expanded or None

def lf_runtime_domain_registry_detect_registered_values(field_name: str, text: str) -> lf_runtime_domain_registry_List[str] | None:
    normalized_field = lf_runtime_domain_registry__field_name(field_name)
    normalized_text_value = lf_runtime_domain_registry_normalize_text(text)
    detected: lf_runtime_domain_registry_List[str] = []
    for group in lf_runtime_domain_registry_get_registered_value_groups(normalized_field, include_builtin=True):
        aliases = [group.get('canonical', ''), *group.get('synonyms', []), *group.get('values', [])]
        if any((lf_runtime_domain_registry_normalize_text(alias) in normalized_text_value for alias in aliases if str(alias).strip())):
            detected.extend(group.get('values', []))
    detected = lf_runtime_domain_registry__dedupe(detected)
    return detected or None

def lf_runtime_domain_registry_get_registered_analysis_rules(include_builtin: bool=True) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]:
    registry = lf_runtime_domain_registry_load_domain_registry()
    return [*(lf_runtime_domain_registry_DEFAULT_ANALYSIS_RULES if include_builtin else []), *registry.get('analysis_rules', [])]

def lf_runtime_domain_registry_get_registered_join_rules(include_builtin: bool=True) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]:
    registry = lf_runtime_domain_registry_load_domain_registry()
    return [*(lf_runtime_domain_registry_DEFAULT_JOIN_RULES if include_builtin else []), *registry.get('join_rules', [])]

def lf_runtime_domain_registry__compact_text(value: lf_runtime_domain_registry_Any) -> str:
    return lf_runtime_domain_registry_normalize_text(str(value or '')).replace(' ', '')

def lf_runtime_domain_registry_match_registered_analysis_rules(query_text: str, include_builtin: bool=True) -> lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]]:
    normalized = lf_runtime_domain_registry__compact_text(query_text)
    matched: lf_runtime_domain_registry_List[lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]] = []
    for rule in lf_runtime_domain_registry_get_registered_analysis_rules(include_builtin=include_builtin):
        candidates = [rule.get('name', ''), rule.get('display_name', ''), *rule.get('synonyms', [])]
        if any((lf_runtime_domain_registry__compact_text(candidate) and lf_runtime_domain_registry__compact_text(candidate) in normalized for candidate in candidates)):
            matched.append(rule)
    return matched

def lf_runtime_domain_registry_format_analysis_rule_for_prompt(rule: lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]) -> str:
    return f"- name={rule.get('name', '')}, display_name={rule.get('display_name', '')}, required_datasets={rule.get('required_datasets', [])}, required_columns={rule.get('required_columns', [])}, calculation_mode={rule.get('calculation_mode', '')}, output_column={rule.get('output_column', '')}, default_group_by={rule.get('default_group_by', [])}, condition={rule.get('condition', '')}, decision_rule={rule.get('decision_rule', '')}, formula={rule.get('formula', '')}, source_columns={rule.get('source_columns', [])}"

def lf_runtime_domain_registry_build_registered_domain_prompt() -> str:
    registry = lf_runtime_domain_registry_load_domain_registry()
    lines = ['Custom domain registry summary:']
    if registry.get('domain_rules_text'):
        lines.append('Free-text domain rules:')
        lines.append(registry['domain_rules_text'])
    keyword_map = lf_runtime_domain_registry_get_dataset_keyword_map()
    if keyword_map:
        lines.append('Dataset keywords:')
        for dataset_key, keywords in keyword_map.items():
            if keywords:
                lines.append(f"- {dataset_key}: {', '.join(keywords)}")
    custom_groups = lf_runtime_domain_registry_get_registered_value_groups(include_builtin=False)
    if custom_groups:
        lines.append('Custom value groups:')
        for group in custom_groups:
            lines.append(f"- field={group.get('field')}, canonical={group.get('canonical')}, values={group.get('values', [])}, synonyms={group.get('synonyms', [])}")
    if registry.get('analysis_rules'):
        lines.append('Custom analysis rules:')
        for rule in registry['analysis_rules']:
            lines.append(lf_runtime_domain_registry_format_analysis_rule_for_prompt(rule))
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

def lf_runtime_domain_registry_get_domain_registry_summary() -> lf_runtime_domain_registry_Dict[str, lf_runtime_domain_registry_Any]:
    registry = lf_runtime_domain_registry_load_domain_registry()
    return {'custom_entry_count': len(registry['entries']), 'custom_dataset_keyword_count': len(registry['dataset_keywords']), 'custom_value_group_count': len(registry['value_groups']), 'custom_analysis_rule_count': len(registry['analysis_rules']), 'custom_join_rule_count': len(registry['join_rules']), 'domain_rules_text_length': len(str(registry.get('domain_rules_text', ''))), 'builtin_analysis_rule_count': len(lf_runtime_domain_registry_DEFAULT_ANALYSIS_RULES), 'builtin_join_rule_count': len(lf_runtime_domain_registry_DEFAULT_JOIN_RULES), 'builtin_value_group_count': sum((len(items) for items in lf_runtime_domain_registry__build_builtin_value_groups().values()))}

# ---- visible runtime: _runtime.graph.state ----
"""Shared state typing for standalone Langflow runtime."""
import typing as lf_runtime_graph_state_import_typing
lf_runtime_graph_state_Any = lf_runtime_graph_state_import_typing.Any
lf_runtime_graph_state_Dict = lf_runtime_graph_state_import_typing.Dict
lf_runtime_graph_state_List = lf_runtime_graph_state_import_typing.List
lf_runtime_graph_state_Literal = lf_runtime_graph_state_import_typing.Literal
lf_runtime_graph_state_TypedDict = lf_runtime_graph_state_import_typing.TypedDict
lf_runtime_graph_state_QueryMode = lf_runtime_graph_state_Literal['retrieval', 'followup_transform']

class lf_runtime_graph_state_AgentGraphState(lf_runtime_graph_state_TypedDict, total=False):
    user_input: str
    chat_history: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, str]]
    context: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    current_data: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any] | None
    domain_rules_text: str
    domain_registry_payload: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any] | lf_runtime_graph_state_List[lf_runtime_graph_state_Any]
    raw_extracted_params: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    extracted_params: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    query_mode: lf_runtime_graph_state_QueryMode
    retrieval_plan: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    retrieval_keys: lf_runtime_graph_state_List[str]
    retrieval_jobs: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]]
    source_results: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]]
    current_datasets: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]
    source_snapshots: lf_runtime_graph_state_List[lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]]
    result: lf_runtime_graph_state_Dict[str, lf_runtime_graph_state_Any]

# ---- visible runtime: _runtime.data.retrieval ----
import random as lf_runtime_data_retrieval_random
import typing as lf_runtime_data_retrieval_import_typing
lf_runtime_data_retrieval_Any = lf_runtime_data_retrieval_import_typing.Any
lf_runtime_data_retrieval_Dict = lf_runtime_data_retrieval_import_typing.Dict
lf_runtime_data_retrieval_List = lf_runtime_data_retrieval_import_typing.List
lf_runtime_data_retrieval_Optional = lf_runtime_data_retrieval_import_typing.Optional
lf_runtime_data_retrieval_AUTO_SUFFIXES = lf_runtime_domain_knowledge_AUTO_SUFFIXES
lf_runtime_data_retrieval_DATASET_METADATA = lf_runtime_domain_knowledge_DATASET_METADATA
lf_runtime_data_retrieval_PROCESS_SPECS = lf_runtime_domain_knowledge_PROCESS_SPECS
lf_runtime_data_retrieval_PRODUCTS = lf_runtime_domain_knowledge_PRODUCTS
lf_runtime_data_retrieval_PRODUCT_TECH_FAMILY = lf_runtime_domain_knowledge_PRODUCT_TECH_FAMILY
lf_runtime_data_retrieval_SPECIAL_PRODUCT_ALIASES = lf_runtime_domain_knowledge_SPECIAL_PRODUCT_ALIASES
lf_runtime_data_retrieval_get_dataset_keyword_map = lf_runtime_domain_registry_get_dataset_keyword_map
lf_runtime_data_retrieval_normalize_dataset_result_columns = lf_runtime_shared_column_resolver_normalize_dataset_result_columns
lf_runtime_data_retrieval_normalize_text = lf_runtime_shared_filter_utils_normalize_text
lf_runtime_data_retrieval_format_summary_quantity = lf_runtime_shared_number_format_format_summary_quantity
lf_runtime_data_retrieval_DEFECTS_BY_FAMILY = {'DP': ['particle', 'contamination', 'edge crack', 'surface stain'], 'DA': ['die shift', 'die tilt', 'void', 'epoxy bleed', 'missing die'], 'PCO': ['chip crack', 'pickup miss', 'warpage', 'edge chipping'], 'DC': ['mark misread', 'die crack', 'orientation miss', 'size mismatch'], 'DI': ['vision fail', 'foreign material', 'inspection miss'], 'DS': ['saw crack', 'burr', 'edge chip', 'trim miss'], 'FCB': ['bump open', 'bump short', 'underfill void', 'warpage', 'bridge'], 'BM': ['mask miss', 'offset', 'contamination', 'coverage fail'], 'PC': ['plating spot', 'void', 'surface scratch', 'color mismatch'], 'WB': ['nsop', 'lifted bond', 'heel crack', 'wire sweep', 'short wire'], 'QCSPC': ['inspection fail', 'dimension ng', 'scratch', 'contamination'], 'SAT': ['delamination', 'void', 'crack', 'acoustic ng'], 'PL': ['peel fail', 'label miss', 'surface damage'], 'ETC': ['visual ng', 'dimension ng', 'trace miss']}
lf_runtime_data_retrieval_EQUIPMENT_BY_FAMILY = {'DP': [('DP-01', 'Wet Cleaner'), ('DP-02', 'Back Grinder')], 'DA': [('DA-01', 'ASM AD830'), ('DA-02', 'Datacon 2200 evo')], 'PCO': [('PCO-01', 'Pick and Place'), ('PCO-02', 'Optical Sorter')], 'DC': [('DC-01', 'Dicing Saw'), ('DC-02', 'Vision Marker')], 'DI': [('DI-01', 'Inspection Station')], 'DS': [('DS-01', 'Sawing Station')], 'FCB': [('FCB-01', 'TC Bonder'), ('FCB-02', 'Reflow Oven')], 'BM': [('BM-01', 'Ball Mount Tool')], 'PC': [('PC-01', 'Plating Tool'), ('PC-02', 'Cleaning Station')], 'WB': [('WB-01', 'K&S IConn'), ('WB-02', 'K&S IConn Plus')], 'QCSPC': [('QC-01', 'AOI'), ('QC-02', '3D Inspector')], 'SAT': [('SAT-01', 'SAT Tool')], 'PL': [('PL-01', 'Pack Line')], 'ETC': [('ETC-01', 'General Station')]}
lf_runtime_data_retrieval_DOWNTIME_BY_FAMILY = {'DP': ['material hold', 'chemical change', 'tray feeder jam'], 'DA': ['PM overdue', 'vacuum leak', 'nozzle clog', 'vision align fail'], 'PCO': ['pickup arm alarm', 'vision mismatch', 'tray shortage'], 'DC': ['blade wear', 'camera alarm', 'setup change'], 'DI': ['inspection recipe hold', 'vision tuning'], 'DS': ['saw blade replace', 'coolant low', 'alignment fail'], 'FCB': ['reflow temp alarm', 'underfill clog', 'robot home error'], 'BM': ['mask change', 'alignment fail'], 'PC': ['bath exchange', 'temperature alarm'], 'WB': ['capillary wear', 'bond force drift', 'material shortage'], 'QCSPC': ['aoi calibration', 'review backlog'], 'SAT': ['scan setup hold', 'review hold'], 'PL': ['label printer fault', 'tray shortage'], 'ETC': ['operator wait', 'qa hold']}
lf_runtime_data_retrieval_WIP_STATUS_BY_FAMILY = {'DP': ['QUEUED', 'RUNNING', 'WAIT_DA', 'WAIT_MATERIAL', 'HOLD'], 'DA': ['QUEUED', 'RUNNING', 'WAIT_PCO', 'WAIT_WB', 'HOLD'], 'PCO': ['QUEUED', 'RUNNING', 'WAIT_DC', 'REWORK', 'HOLD'], 'DC': ['QUEUED', 'RUNNING', 'WAIT_DI', 'REWORK'], 'DI': ['QUEUED', 'RUNNING', 'WAIT_DS', 'HOLD'], 'DS': ['QUEUED', 'RUNNING', 'WAIT_FCB', 'WAIT_WB', 'HOLD'], 'FCB': ['QUEUED', 'RUNNING', 'WAIT_BM', 'WAIT_PC', 'HOLD'], 'BM': ['QUEUED', 'RUNNING', 'WAIT_PC', 'HOLD'], 'PC': ['QUEUED', 'RUNNING', 'WAIT_QCSPC', 'HOLD'], 'WB': ['QUEUED', 'RUNNING', 'WAIT_QCSPC', 'REWORK', 'HOLD'], 'QCSPC': ['QUEUED', 'RUNNING', 'WAIT_SAT', 'WAIT_PL'], 'SAT': ['QUEUED', 'RUNNING', 'WAIT_PL', 'REVIEW'], 'PL': ['QUEUED', 'RUNNING', 'SHIP_READY', 'COMPLETE'], 'ETC': ['QUEUED', 'RUNNING', 'REVIEW', 'HOLD']}
lf_runtime_data_retrieval_YIELD_FAIL_BINS_BY_FAMILY = {'DP': ['particle', 'alignment_ng', 'surface_ng'], 'DA': ['die_shift', 'void_fail', 'attach_miss'], 'PCO': ['chip_crack', 'pickup_ng', 'vision_ng'], 'DC': ['mark_ng', 'crack_ng', 'orientation_ng'], 'DI': ['visual_ng', 'inspection_ng', 'foreign_material'], 'DS': ['burr_ng', 'saw_crack', 'trim_ng'], 'FCB': ['bump_open', 'bridge', 'warpage'], 'BM': ['offset_ng', 'coverage_ng', 'mask_ng'], 'PC': ['surface_ng', 'void_ng', 'color_ng'], 'WB': ['nsop', 'wire_open', 'bond_lift'], 'QCSPC': ['inspection_ng', 'scratch', 'dimension_ng'], 'SAT': ['delamination', 'void', 'crack'], 'PL': ['label_ng', 'packing_ng', 'tray_mix'], 'ETC': ['visual_ng', 'dimension_ng', 'review_ng']}
lf_runtime_data_retrieval_HOLD_REASONS_BY_FAMILY = {'DP': ['incoming inspection hold', 'material moisture check', 'wafer ID mismatch'], 'DA': ['epoxy cure verification', 'die attach void review', 'recipe approval hold'], 'PCO': ['pickup review hold', 'tray setup hold'], 'DC': ['blade wear inspection', 'vision review hold'], 'DI': ['inspection review hold', 'recipe update hold'], 'DS': ['saw review hold', 'trim review hold'], 'FCB': ['bump coplanarity review', 'reflow profile hold', 'underfill void review'], 'BM': ['ball mount review', 'alignment review'], 'PC': ['plating review hold', 'chemistry review hold'], 'WB': ['bond pull outlier', 'capillary replacement hold', 'loop height review'], 'QCSPC': ['inspection review', 'dimension review'], 'SAT': ['scan review hold', 'customer review hold'], 'PL': ['label verification', 'shipping spec hold', 'QA final release'], 'ETC': ['operator review hold', 'qa disposition hold']}
lf_runtime_data_retrieval_SCRAP_REASONS_BY_FAMILY = {'DP': ['incoming damage', 'contamination', 'moisture exposure'], 'DA': ['die crack', 'missing die', 'epoxy overflow'], 'PCO': ['pickup damage', 'edge crack', 'vision reject'], 'DC': ['marking fail', 'die crack', 'dicing damage'], 'DI': ['inspection reject', 'foreign material'], 'DS': ['saw crack', 'burr', 'trim fail'], 'FCB': ['bump bridge', 'underfill void', 'warpage'], 'BM': ['offset', 'coverage fail', 'mask defect'], 'PC': ['surface damage', 'void', 'color fail'], 'WB': ['wire short', 'bond lift', 'pad damage'], 'QCSPC': ['inspection fail', 'dimension fail', 'scratch'], 'SAT': ['acoustic fail', 'crack', 'void'], 'PL': ['packing damage', 'label NG', 'qty mismatch'], 'ETC': ['visual fail', 'qa reject']}
lf_runtime_data_retrieval_RECIPE_BASE_BY_FAMILY = {'DP': {'temp_c': 115, 'pressure_kpa': 70, 'process_time_sec': 300}, 'DA': {'temp_c': 168, 'pressure_kpa': 112, 'process_time_sec': 510}, 'PCO': {'temp_c': 90, 'pressure_kpa': 45, 'process_time_sec': 240}, 'DC': {'temp_c': 40, 'pressure_kpa': 18, 'process_time_sec': 220}, 'DI': {'temp_c': 28, 'pressure_kpa': 0, 'process_time_sec': 180}, 'DS': {'temp_c': 35, 'pressure_kpa': 20, 'process_time_sec': 210}, 'FCB': {'temp_c': 238, 'pressure_kpa': 126, 'process_time_sec': 470}, 'BM': {'temp_c': 125, 'pressure_kpa': 65, 'process_time_sec': 260}, 'PC': {'temp_c': 78, 'pressure_kpa': 40, 'process_time_sec': 320}, 'WB': {'temp_c': 132, 'pressure_kpa': 88, 'process_time_sec': 360}, 'QCSPC': {'temp_c': 30, 'pressure_kpa': 0, 'process_time_sec': 200}, 'SAT': {'temp_c': 32, 'pressure_kpa': 0, 'process_time_sec': 260}, 'PL': {'temp_c': 28, 'pressure_kpa': 0, 'process_time_sec': 240}, 'ETC': {'temp_c': 30, 'pressure_kpa': 0, 'process_time_sec': 180}}
lf_runtime_data_retrieval_LOT_STATUS_FLOW = ['WAIT', 'RUNNING', 'MOVE_OUT', 'HOLD', 'REWORK', 'COMPLETE']
lf_runtime_data_retrieval_HOLD_OWNERS = ['PE', 'PIE', 'QA', 'Process', 'Equipment', 'Customer Quality']

def lf_runtime_data_retrieval__stable_seed(date_text: str, offset: int=0) -> int:
    normalized = str(date_text or '').strip()
    if normalized.isdigit():
        return int(normalized) + offset
    return sum((ord(ch) for ch in normalized)) + offset

def lf_runtime_data_retrieval__as_list(value: lf_runtime_data_retrieval_Any) -> lf_runtime_data_retrieval_List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []

def lf_runtime_data_retrieval__normalize_key(value: lf_runtime_data_retrieval_Any) -> str:
    text = lf_runtime_data_retrieval_normalize_text(value)
    return text.replace('/', '').replace('-', '').replace('_', '').replace(' ', '')

def lf_runtime_data_retrieval__match_exact(target: lf_runtime_data_retrieval_Any, allowed: lf_runtime_data_retrieval_Any) -> bool:
    values = lf_runtime_data_retrieval__as_list(allowed)
    if not values:
        return True
    target_key = lf_runtime_data_retrieval__normalize_key(target)
    return any((target_key == lf_runtime_data_retrieval__normalize_key(item) for item in values))

def lf_runtime_data_retrieval__match_mcp_no(target: lf_runtime_data_retrieval_Any, allowed: lf_runtime_data_retrieval_Any) -> bool:
    values = lf_runtime_data_retrieval__as_list(allowed)
    if not values:
        return True
    normalized_target = lf_runtime_data_retrieval_normalize_text(target)
    return any((normalized_target.startswith(lf_runtime_data_retrieval_normalize_text(item)) for item in values))

def lf_runtime_data_retrieval__is_auto_product(mcp_no: str) -> bool:
    suffix = str(mcp_no or '').strip()[-1:].upper()
    return suffix in lf_runtime_data_retrieval_AUTO_SUFFIXES

def lf_runtime_data_retrieval__matches_product(row: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any], product_name: lf_runtime_data_retrieval_Optional[str]) -> bool:
    if not product_name:
        return True
    query = lf_runtime_data_retrieval_normalize_text(product_name)
    hbm_or_3ds_tokens = ['HBM_OR_3DS', 'HBM/3DS', *lf_runtime_data_retrieval_SPECIAL_PRODUCT_ALIASES['HBM_OR_3DS']]
    auto_product_tokens = ['AUTO_PRODUCT', 'AUTO', *lf_runtime_data_retrieval_SPECIAL_PRODUCT_ALIASES['AUTO_PRODUCT']]
    if any((lf_runtime_data_retrieval_normalize_text(token) in query for token in hbm_or_3ds_tokens)):
        return str(row.get('TSV_DIE_TYP', '')).upper() == 'TSV'
    if any((lf_runtime_data_retrieval_normalize_text(token) in query for token in auto_product_tokens)):
        return lf_runtime_data_retrieval__is_auto_product(str(row.get('MCP_NO', '')))
    aliases: lf_runtime_data_retrieval_List[str] = [str(row.get('MODE', '')), str(row.get('DEN', '')), str(row.get('TECH', '')), str(row.get('MCP_NO', '')), str(row.get('LEAD', '')), str(row.get('PKG_TYPE1', '')), str(row.get('PKG_TYPE2', '')), str(row.get('TSV_DIE_TYP', '')), f"{row.get('MODE', '')} {row.get('DEN', '')} {row.get('TECH', '')}"]
    if str(row.get('TSV_DIE_TYP', '')).upper() == 'TSV':
        aliases.extend(['HBM_OR_3DS', 'HBM/3DS', *lf_runtime_data_retrieval_SPECIAL_PRODUCT_ALIASES['HBM_OR_3DS']])
    if lf_runtime_data_retrieval__is_auto_product(str(row.get('MCP_NO', ''))):
        aliases.extend(['AUTO_PRODUCT', 'AUTO', *lf_runtime_data_retrieval_SPECIAL_PRODUCT_ALIASES['AUTO_PRODUCT']])
    return any((query in lf_runtime_data_retrieval_normalize_text(value) for value in aliases if str(value).strip()))

def lf_runtime_data_retrieval__apply_common_filters(rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]], params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]]:
    filtered = []
    for row in rows:
        if not lf_runtime_data_retrieval__match_exact(row.get('OPER_NAME', ''), params.get('process_name')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('OPER_NUM', ''), params.get('oper_num')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('PKG_TYPE1', ''), params.get('pkg_type1')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('PKG_TYPE2', ''), params.get('pkg_type2')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('라인', ''), params.get('line_name')):
            continue
        if not lf_runtime_data_retrieval__matches_product(row, params.get('product_name')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('MODE', ''), params.get('mode')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('DEN', ''), params.get('den')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('TECH', ''), params.get('tech')):
            continue
        if not lf_runtime_data_retrieval__match_exact(row.get('LEAD', ''), params.get('lead')):
            continue
        if not lf_runtime_data_retrieval__match_mcp_no(row.get('MCP_NO', ''), params.get('mcp_no')):
            continue
        filtered.append(row)
    return filtered

def lf_runtime_data_retrieval_filter_rows_by_params(rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]], params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]]:
    """이미 조회한 row 목록에 공통 필터를 다시 적용한다.

    실제 조회 함수도 내부적으로 같은 필터를 사용하지만,
    실행 경로가 복잡해졌을 때 화면에 보여줄 최종 테이블에는
    필터가 확실히 반영되도록 마지막 안전장치로 한 번 더 사용한다.
    """
    if not isinstance(rows, list):
        return []
    safe_rows = [row for row in rows if isinstance(row, dict)]
    return lf_runtime_data_retrieval__apply_common_filters(safe_rows, params or {})

def lf_runtime_data_retrieval__iter_valid_process_product_pairs():
    for spec in lf_runtime_data_retrieval_PROCESS_SPECS:
        for product in lf_runtime_data_retrieval_PRODUCTS:
            if spec['family'] in lf_runtime_data_retrieval_PRODUCT_TECH_FAMILY.get(product['TECH'], set()):
                yield (spec, product)

def lf_runtime_data_retrieval__make_lot_id(date: str, family: str, index: int) -> str:
    family_code = family.replace('/', '').replace('_', '')[:4]
    return f'LOT-{date[-4:]}-{family_code}-{index:03d}'

def lf_runtime_data_retrieval__derive_business_family(product: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> str:
    if str(product.get('TSV_DIE_TYP', '')).upper() == 'TSV':
        return 'HBM'
    if str(product.get('MODE', '')) == 'LPDDR5':
        return 'MOBILE'
    if str(product.get('TECH', '')) == 'FC':
        return 'COMPUTE'
    return 'STANDARD'

def lf_runtime_data_retrieval__derive_factory(spec: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> str:
    family = str(spec.get('family', ''))
    if family in {'DP', 'DA', 'PCO', 'DC', 'DI', 'DS'}:
        return 'FAB1'
    if family in {'FCB', 'BM', 'PC', 'WB'}:
        return 'PKG1'
    return 'TEST1'

def lf_runtime_data_retrieval__derive_org(spec: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> str:
    family = str(spec.get('family', ''))
    if family in {'DP', 'DA', 'PCO', 'DC', 'DI', 'DS'}:
        return 'ASSEMBLY'
    if family in {'FCB', 'BM', 'PC', 'WB'}:
        return 'PACKAGE'
    if family in {'QCSPC', 'SAT', 'PL'}:
        return 'QUALITY'
    return 'SUPPORT'

def lf_runtime_data_retrieval__build_base_row(date: str, spec: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any], product: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    return {'WORK_DT': date, 'OPER_NAME': spec['OPER_NAME'], '공정군': spec['family'], 'OPER_NUM': spec['OPER_NUM'], 'PKG_TYPE1': product['PKG_TYPE1'], 'PKG_TYPE2': product['PKG_TYPE2'], 'TSV_DIE_TYP': product['TSV_DIE_TYP'], 'MODE': product['MODE'], 'DEN': product['DEN'], 'TECH': product['TECH'], 'LEAD': product['LEAD'], 'MCP_NO': product['MCP_NO'], 'FAMILY': lf_runtime_data_retrieval__derive_business_family(product), 'FACTORY': lf_runtime_data_retrieval__derive_factory(spec), 'ORG': lf_runtime_data_retrieval__derive_org(spec), '라인': spec['라인']}

def lf_runtime_data_retrieval__pick_equipment(family: str, process_name: str) -> tuple[str, str]:
    candidates = lf_runtime_data_retrieval_EQUIPMENT_BY_FAMILY.get(family) or lf_runtime_data_retrieval_EQUIPMENT_BY_FAMILY['ETC']
    index = abs(hash(f'{family}:{process_name}')) % len(candidates)
    return candidates[index]

def lf_runtime_data_retrieval__apply_signal_overrides(dataset_key: str, row: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    process_name = str(row.get('OPER_NAME', ''))
    mode = str(row.get('MODE', ''))
    den = str(row.get('DEN', ''))
    if dataset_key == 'production' and process_name == 'D/A3' and (mode == 'DDR5'):
        row['production'] = 2940 if den == '512G' else 2680
    elif dataset_key == 'target' and process_name == 'D/A3' and (mode == 'DDR5'):
        row['target'] = 3600 if den == '512G' else 3400
    elif dataset_key == 'equipment' and process_name == 'D/A3' and (mode == 'DDR5'):
        row['가동률'] = 82.0
        row['actual_hours'] = 19.7
        row['비가동사유'] = 'vision align fail'
    elif dataset_key == 'wip' and process_name == 'D/A3' and (mode == 'DDR5'):
        row['재공수량'] = 2100
        row['avg_wait_minutes'] = 185
        row['상태'] = 'HOLD'
    elif dataset_key == 'hold' and process_name == 'D/A3' and (mode == 'DDR5'):
        row['hold_qty'] = 980
        row['hold_reason'] = 'recipe approval hold'
        row['hold_status'] = 'OPEN'
    elif dataset_key == 'yield' and process_name == 'PLH' and (mode == 'LPDDR5'):
        row['yield_rate'] = 99.1
        row['pass_qty'] = int(row['tested_qty'] * row['yield_rate'] / 100)
        row['dominant_fail_bin'] = 'inspection_ng'
    return row

def lf_runtime_data_retrieval_get_production_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        base = 3200 if spec['family'] in {'DP', 'DA'} else 2400
        qty = int(base * lf_runtime_data_retrieval_random.uniform(0.55, 1.18))
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['production'] = qty
        row = lf_runtime_data_retrieval__apply_signal_overrides('production', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    total = sum((int(item['production']) for item in rows))
    return {'success': True, 'tool_name': 'get_production_data', 'data': rows, 'summary': f'총 {len(rows)}건, 총 생산량 {lf_runtime_data_retrieval_format_summary_quantity(total)}'}

def lf_runtime_data_retrieval_get_target_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        target = 3600 if spec['family'] in {'DP', 'DA'} else 2600
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['target'] = target
        row = lf_runtime_data_retrieval__apply_signal_overrides('target', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    total = sum((int(item['target']) for item in rows))
    return {'success': True, 'tool_name': 'get_target_data', 'data': rows, 'summary': f'총 {len(rows)}건, 총 목표량 {lf_runtime_data_retrieval_format_summary_quantity(total)}'}

def lf_runtime_data_retrieval_get_defect_rate(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 2000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        inspection_qty = lf_runtime_data_retrieval_random.randint(2500, 8000)
        family = spec['family']
        rate_floor = 0.004 if family in {'DP', 'PL'} else 0.008
        rate_ceiling = 0.018 if family in {'WB', 'FCB'} else 0.028
        defect_qty = int(inspection_qty * lf_runtime_data_retrieval_random.uniform(rate_floor, rate_ceiling))
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['inspection_qty'] = inspection_qty
        row['불량수량'] = defect_qty
        row['defect_rate'] = round(defect_qty / inspection_qty * 100, 2)
        row['주요불량유형'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_DEFECTS_BY_FAMILY.get(family, lf_runtime_data_retrieval_DEFECTS_BY_FAMILY['ETC']))
        row = lf_runtime_data_retrieval__apply_signal_overrides('defect', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    avg_rate = sum((float(item['defect_rate']) for item in rows)) / len(rows) if rows else 0.0
    return {'success': True, 'tool_name': 'get_defect_rate', 'data': rows, 'summary': f'총 {len(rows)}건, 평균 불량률 {avg_rate:.2f}%'}

def lf_runtime_data_retrieval_get_equipment_status(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 3000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        equip_id, equip_name = lf_runtime_data_retrieval__pick_equipment(spec['family'], spec['OPER_NAME'])
        util = round(lf_runtime_data_retrieval_random.uniform(62, 97), 1)
        planned = 24.0
        actual = round(planned * util / 100, 1)
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['설비ID'] = equip_id
        row['설비명'] = equip_name
        row['planned_hours'] = planned
        row['actual_hours'] = actual
        row['가동률'] = util
        row['비가동사유'] = 'none' if util > 90 else lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_DOWNTIME_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_DOWNTIME_BY_FAMILY['ETC']))
        row = lf_runtime_data_retrieval__apply_signal_overrides('equipment', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    avg_util = sum((float(item['가동률']) for item in rows)) / len(rows) if rows else 0.0
    return {'success': True, 'tool_name': 'get_equipment_status', 'data': rows, 'summary': f'총 {len(rows)}건, 평균 가동률 {avg_util:.1f}%'}

def lf_runtime_data_retrieval_get_wip_status(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 4000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['재공수량'] = lf_runtime_data_retrieval_random.randint(150, 2600)
        row['avg_wait_minutes'] = lf_runtime_data_retrieval_random.randint(10, 240)
        row['상태'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_WIP_STATUS_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_WIP_STATUS_BY_FAMILY['ETC']))
        row = lf_runtime_data_retrieval__apply_signal_overrides('wip', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    total = sum((int(item['재공수량']) for item in rows))
    delayed = sum((1 for item in rows if item['상태'] in {'HOLD', 'REWORK', 'WAIT_QA', 'WAIT_MATERIAL'}))
    return {'success': True, 'tool_name': 'get_wip_status', 'data': rows, 'summary': f'총 {len(rows)}건, 총 WIP {lf_runtime_data_retrieval_format_summary_quantity(total)} EA, 대기/보류 {delayed}건'}

def lf_runtime_data_retrieval_get_yield_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 5000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        tested_qty = lf_runtime_data_retrieval_random.randint(2200, 7800)
        base_yield = 98.8 if spec['family'] in {'DP', 'PL'} else 96.5
        if spec['family'] in {'WB', 'FCB'}:
            base_yield = 94.5
        yield_rate = round(max(82.0, min(99.9, lf_runtime_data_retrieval_random.uniform(base_yield - 4.5, base_yield + 1.2))), 2)
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['tested_qty'] = tested_qty
        row['pass_qty'] = int(tested_qty * yield_rate / 100)
        row['yield_rate'] = yield_rate
        row['dominant_fail_bin'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_YIELD_FAIL_BINS_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_YIELD_FAIL_BINS_BY_FAMILY['ETC']))
        row = lf_runtime_data_retrieval__apply_signal_overrides('yield', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    avg_yield = sum((float(item['yield_rate']) for item in rows)) / len(rows) if rows else 0.0
    return {'success': True, 'tool_name': 'get_yield_data', 'data': rows, 'summary': f'총 {len(rows)}건, 평균 수율 {avg_yield:.2f}%'}

def lf_runtime_data_retrieval_get_hold_lot_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 6000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for index, (spec, product) in enumerate(lf_runtime_data_retrieval__iter_valid_process_product_pairs(), start=1):
        if lf_runtime_data_retrieval_random.random() < 0.45:
            continue
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['lot_id'] = lf_runtime_data_retrieval__make_lot_id(date, spec['family'], index)
        row['hold_qty'] = lf_runtime_data_retrieval_random.randint(80, 1800)
        row['hold_reason'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_HOLD_REASONS_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_HOLD_REASONS_BY_FAMILY['ETC']))
        row['hold_owner'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_HOLD_OWNERS)
        row['hold_hours'] = round(lf_runtime_data_retrieval_random.uniform(1.5, 42.0), 1)
        row['hold_status'] = lf_runtime_data_retrieval_random.choice(['OPEN', 'REVIEW', 'WAIT_DISPOSITION'])
        row = lf_runtime_data_retrieval__apply_signal_overrides('hold', row)
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    total_hold = sum((int(item['hold_qty']) for item in rows))
    avg_hold_hours = sum((float(item['hold_hours']) for item in rows)) / len(rows) if rows else 0.0
    return {'success': True, 'tool_name': 'get_hold_lot_data', 'data': rows, 'summary': f'총 {len(rows)}건, 총 홀드수량 {lf_runtime_data_retrieval_format_summary_quantity(total_hold)}, 평균 홀드시간 {avg_hold_hours:.1f}h' if rows else '총 0건, 총 홀드수량 0'}

def lf_runtime_data_retrieval_get_scrap_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 7000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        input_qty = lf_runtime_data_retrieval_random.randint(1800, 7200)
        scrap_qty = int(input_qty * lf_runtime_data_retrieval_random.uniform(0.002, 0.028))
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['scrap_qty'] = scrap_qty
        row['scrap_rate'] = round(scrap_qty / input_qty * 100, 2)
        row['scrap_reason'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_SCRAP_REASONS_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_SCRAP_REASONS_BY_FAMILY['ETC']))
        row['loss_cost_usd'] = int(scrap_qty * lf_runtime_data_retrieval_random.uniform(1.8, 8.5))
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    total_scrap = sum((int(item['scrap_qty']) for item in rows))
    total_cost = sum((int(item['loss_cost_usd']) for item in rows))
    return {'success': True, 'tool_name': 'get_scrap_data', 'data': rows, 'summary': f'총 {len(rows)}건, 총 스크랩 {lf_runtime_data_retrieval_format_summary_quantity(total_scrap)}, 총 손실비용 ${total_cost:,}'}

def lf_runtime_data_retrieval_get_recipe_condition_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 8000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for spec, product in lf_runtime_data_retrieval__iter_valid_process_product_pairs():
        base = lf_runtime_data_retrieval_RECIPE_BASE_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_RECIPE_BASE_BY_FAMILY['ETC'])
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['recipe_id'] = f"RC-{spec['family'][:3]}-{lf_runtime_data_retrieval_random.randint(10, 99)}"
        row['recipe_version'] = f'v{lf_runtime_data_retrieval_random.randint(1, 3)}.{lf_runtime_data_retrieval_random.randint(0, 9)}'
        row['temp_c'] = round(base['temp_c'] + lf_runtime_data_retrieval_random.uniform(-6, 6), 1)
        row['pressure_kpa'] = round(max(0, base['pressure_kpa'] + lf_runtime_data_retrieval_random.uniform(-12, 12)), 1)
        row['process_time_sec'] = int(base['process_time_sec'] + lf_runtime_data_retrieval_random.uniform(-60, 60))
        row['operator_id'] = f'OP-{lf_runtime_data_retrieval_random.randint(100, 999)}'
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    return {'success': True, 'tool_name': 'get_recipe_condition_data', 'data': rows, 'summary': f'총 {len(rows)}건, 공정 조건/레시피 이력 조회 완료'}

def lf_runtime_data_retrieval_get_lot_trace_data(params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    date = str(params['date'])
    lf_runtime_data_retrieval_random.seed(lf_runtime_data_retrieval__stable_seed(date, 9000))
    rows: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for index, (spec, product) in enumerate(lf_runtime_data_retrieval__iter_valid_process_product_pairs(), start=1):
        if lf_runtime_data_retrieval_random.random() < 0.35:
            continue
        row = lf_runtime_data_retrieval__build_base_row(date, spec, product)
        row['lot_id'] = lf_runtime_data_retrieval__make_lot_id(date, spec['family'], index)
        row['wafer_id'] = f'WF-{lf_runtime_data_retrieval_random.randint(1000, 9999)}'
        row['route_step'] = lf_runtime_data_retrieval_random.randint(3, 28)
        row['current_status'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_LOT_STATUS_FLOW)
        row['elapsed_hours'] = round(lf_runtime_data_retrieval_random.uniform(2.0, 96.0), 1)
        row['next_process'] = lf_runtime_data_retrieval_random.choice([item['OPER_NAME'] for item in lf_runtime_data_retrieval_PROCESS_SPECS if item['family'] == spec['family']])
        row['hold_reason'] = lf_runtime_data_retrieval_random.choice(lf_runtime_data_retrieval_HOLD_REASONS_BY_FAMILY.get(spec['family'], lf_runtime_data_retrieval_HOLD_REASONS_BY_FAMILY['ETC'])) if lf_runtime_data_retrieval_random.random() < 0.25 else 'none'
        rows.append(row)
    rows = lf_runtime_data_retrieval__apply_common_filters(rows, params)
    avg_elapsed = sum((float(item['elapsed_hours']) for item in rows)) / len(rows) if rows else 0.0
    return {'success': True, 'tool_name': 'get_lot_trace_data', 'data': rows, 'summary': f'총 {len(rows)}건, 평균 체류 시간 {avg_elapsed:.1f}h'}
lf_runtime_data_retrieval_DATASET_TOOL_FUNCTIONS = {'production': lf_runtime_data_retrieval_get_production_data, 'target': lf_runtime_data_retrieval_get_target_data, 'defect': lf_runtime_data_retrieval_get_defect_rate, 'equipment': lf_runtime_data_retrieval_get_equipment_status, 'wip': lf_runtime_data_retrieval_get_wip_status, 'yield': lf_runtime_data_retrieval_get_yield_data, 'hold': lf_runtime_data_retrieval_get_hold_lot_data, 'scrap': lf_runtime_data_retrieval_get_scrap_data, 'recipe': lf_runtime_data_retrieval_get_recipe_condition_data, 'lot_trace': lf_runtime_data_retrieval_get_lot_trace_data}
lf_runtime_data_retrieval_DATASET_REQUIRED_PARAM_FIELDS = {'production': ['date'], 'target': ['date'], 'defect': ['date'], 'equipment': ['date'], 'wip': ['date'], 'yield': ['date'], 'hold': ['date'], 'scrap': ['date'], 'recipe': ['date'], 'lot_trace': ['date']}
lf_runtime_data_retrieval_DATASET_REGISTRY = {dataset_key: {'label': lf_runtime_data_retrieval_DATASET_METADATA[dataset_key]['label'], 'tool_name': tool_fn.__name__, 'tool': tool_fn, 'keywords': lf_runtime_data_retrieval_DATASET_METADATA[dataset_key]['keywords'], 'required_param_fields': list(lf_runtime_data_retrieval_DATASET_REQUIRED_PARAM_FIELDS.get(dataset_key, []))} for dataset_key, tool_fn in lf_runtime_data_retrieval_DATASET_TOOL_FUNCTIONS.items()}
lf_runtime_data_retrieval_RETRIEVAL_TOOL_MAP = {key: meta['tool'] for key, meta in lf_runtime_data_retrieval_DATASET_REGISTRY.items()}

def lf_runtime_data_retrieval_get_dataset_label(dataset_key: str) -> str:
    dataset_meta = lf_runtime_data_retrieval_DATASET_REGISTRY.get(dataset_key, {})
    return str(dataset_meta.get('label', dataset_key))

def lf_runtime_data_retrieval_list_available_dataset_labels() -> lf_runtime_data_retrieval_List[str]:
    return [str(meta.get('label', key)) for key, meta in lf_runtime_data_retrieval_DATASET_REGISTRY.items()]

def lf_runtime_data_retrieval_dataset_required_param_fields(dataset_key: str) -> lf_runtime_data_retrieval_List[str]:
    """이 데이터셋을 다시 조회할 때 값이 바뀌면 재조회가 필요한 필드를 반환한다."""
    dataset_meta = lf_runtime_data_retrieval_DATASET_REGISTRY.get(dataset_key, {})
    required_fields = dataset_meta.get('required_param_fields', [])
    if isinstance(required_fields, list):
        return [str(field) for field in required_fields if str(field).strip()]
    return []

def lf_runtime_data_retrieval_dataset_requires_param(dataset_key: str, field_name: str) -> bool:
    """특정 필드가 이 데이터셋의 필수 retrieval boundary 인지 확인한다."""
    normalized_field_name = str(field_name or '').strip()
    if not normalized_field_name:
        return False
    return normalized_field_name in lf_runtime_data_retrieval_dataset_required_param_fields(dataset_key)

def lf_runtime_data_retrieval_dataset_requires_date(dataset_key: str) -> bool:
    """기존 호출부 호환용 convenience wrapper.

    실제 기준 정보는 `dataset_required_param_fields`에 있고,
    이 함수는 그중 `date`만 자주 물어볼 때 쓰는 얇은 래퍼다.
    """
    return lf_runtime_data_retrieval_dataset_requires_param(dataset_key, 'date')

def lf_runtime_data_retrieval_pick_retrieval_tools(query_text: str) -> lf_runtime_data_retrieval_List[str]:
    """질문 키워드만 보고 dataset 후보를 빠르게 고른다.

    이 함수는 최종 planner를 대체하지 않는다.
    현재 코드에서는 주로 아래 용도로 사용된다.
    1. query mode 판단용 휴리스틱
    2. retrieval planner의 가산적 보조 신호
    3. LLM planner가 비었을 때 마지막 fallback
    """
    query = lf_runtime_data_retrieval_normalize_text(query_text)
    selected: lf_runtime_data_retrieval_List[str] = []
    keyword_map = lf_runtime_data_retrieval_get_dataset_keyword_map()
    for dataset_key, dataset_meta in lf_runtime_data_retrieval_DATASET_REGISTRY.items():
        keywords = keyword_map.get(dataset_key, dataset_meta.get('keywords', []))
        if any((lf_runtime_data_retrieval_normalize_text(token) in query for token in keywords)):
            selected.append(dataset_key)
    explicit_trace_tokens = ['trace', '이력', '추적', 'traceability']
    if 'hold' in selected and 'lot_trace' in selected and (not any((lf_runtime_data_retrieval_normalize_text(token) in query for token in explicit_trace_tokens))):
        selected = [item for item in selected if item != 'lot_trace']
    return selected

def lf_runtime_data_retrieval_pick_retrieval_tool(query_text: str) -> str | None:
    selected = lf_runtime_data_retrieval_pick_retrieval_tools(query_text)
    return selected[0] if selected else None

def lf_runtime_data_retrieval_execute_retrieval_tools(dataset_keys: lf_runtime_data_retrieval_List[str], params: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]) -> lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]]:
    results: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]] = []
    for dataset_key in dataset_keys:
        dataset_meta = lf_runtime_data_retrieval_DATASET_REGISTRY.get(dataset_key)
        if not dataset_meta:
            continue
        result = dataset_meta['tool'](params)
        if isinstance(result, dict):
            result = lf_runtime_data_retrieval_normalize_dataset_result_columns(result, dataset_key)
            result['dataset_key'] = dataset_key
            result['dataset_label'] = dataset_meta['label']
        results.append(result)
    return results

def lf_runtime_data_retrieval_build_current_datasets(tool_results: lf_runtime_data_retrieval_List[lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]]) -> lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any]:
    datasets: lf_runtime_data_retrieval_Dict[str, lf_runtime_data_retrieval_Any] = {}
    for result in tool_results:
        dataset_key = result.get('dataset_key')
        if not dataset_key:
            continue
        rows = result.get('data', [])
        first_row = rows[0] if isinstance(rows, list) and rows else {}
        datasets[dataset_key] = {'label': result.get('dataset_label', lf_runtime_data_retrieval_get_dataset_label(str(dataset_key))), 'tool_name': result.get('tool_name'), 'summary': result.get('summary', ''), 'row_count': len(rows) if isinstance(rows, list) else 0, 'columns': list(first_row.keys()) if isinstance(first_row, dict) else [], 'data': rows if isinstance(rows, list) else []}
    return datasets

# ---- visible runtime: node_utils ----
"""Local helpers shared by standalone Langflow component nodes."""
import json as lf_node_utils_json
import sys as lf_node_utils_sys
import pathlib as lf_node_utils_import_pathlib
lf_node_utils_Path = lf_node_utils_import_pathlib.Path
import typing as lf_node_utils_import_typing
lf_node_utils_Any = lf_node_utils_import_typing.Any
lf_node_utils_Dict = lf_node_utils_import_typing.Dict
lf_node_utils_List = lf_node_utils_import_typing.List
lf_node_utils_read_data_payload = lf_component_base_read_data_payload

def lf_node_utils_ensure_component_root() -> lf_node_utils_Path:
    """Ensure the package parent is importable when Langflow loads nodes by file path."""
    repo_root = lf_node_utils_Path(__file__).resolve().parent.parent
    repo_root_text = str(repo_root)
    if repo_root_text not in lf_node_utils_sys.path:
        lf_node_utils_sys.path.insert(0, repo_root_text)
    return repo_root

def lf_node_utils_coerce_json_field(value: lf_node_utils_Any, default: lf_node_utils_Any) -> lf_node_utils_Any:
    """Parse dict/list JSON-like input when the source passes plain text."""
    if value is None or value == '':
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return lf_node_utils_json.loads(str(value))
    except Exception:
        return default

def lf_node_utils_append_history(history: lf_node_utils_List[lf_node_utils_Dict[str, str]], role: str, content: str) -> lf_node_utils_List[lf_node_utils_Dict[str, str]]:
    """Append one chat turn without duplicating the latest identical entry."""
    cleaned = str(content or '').strip()
    if not cleaned:
        return history
    if history and history[-1].get('role') == role and (history[-1].get('content') == cleaned):
        return history
    history.append({'role': role, 'content': cleaned})
    return history

def lf_node_utils_read_message_text(message: lf_node_utils_Any) -> str:
    """Extract the visible user text from a Langflow Chat Input style payload."""
    if message is None:
        return ''
    text = getattr(message, 'text', None)
    if text is None and isinstance(message, dict):
        text = message.get('text')
    return str(text or '')

def lf_node_utils_read_domain_text_payload(value: lf_node_utils_Any) -> str:
    """Extract raw domain-rules text from a node payload."""
    payload = lf_node_utils_read_data_payload(value)
    text = payload.get('domain_rules_text')
    return str(text or '').strip()

def lf_node_utils_read_domain_registry_payload(value: lf_node_utils_Any) -> lf_node_utils_Dict[str, lf_node_utils_Any] | lf_node_utils_List[lf_node_utils_Any]:
    """Extract parsed domain-registry JSON from a node payload."""
    payload = lf_node_utils_read_data_payload(value)
    registry_payload = payload.get('domain_registry_payload')
    if isinstance(registry_payload, (dict, list)):
        return registry_payload
    return lf_node_utils_coerce_json_field(registry_payload, {})

def lf_node_utils_activate_domain_context_from_state(state: lf_node_utils_Dict[str, lf_node_utils_Any]) -> None:
    """Push the current state's runtime inputs into the standalone runtime layer."""
    set_active_domain_context = lf_runtime_domain_registry_set_active_domain_context
    set_active_llm_config = lf_runtime_shared_config_set_active_llm_config
    set_active_domain_context(domain_rules_text=state.get('domain_rules_text', ''), domain_registry_payload=state.get('domain_registry_payload', {}))
    set_active_llm_config(state.get('llm_config', {}))

# ---- visible runtime: _runtime.services ----
"""그래프 노드와 외부 래퍼가 공통으로 사용하는 서비스 함수 모음."""

# ---- visible runtime: _runtime.services.request_context ----
"""그래프 노드들이 공통으로 쓰는 요청/결과 보조 함수 모음.

이 파일의 목적은 다음 두 가지다.

1. 현재 질문과 이전 결과를 해석할 때 반복되는 작은 로직을 모아 둔다.
2. 그래프 노드 파일이 너무 커지지 않도록, 맥락 관련 유틸리티를 분리한다.
"""
import json as lf_runtime_services_request_context_json
import typing as lf_runtime_services_request_context_import_typing
lf_runtime_services_request_context_Any = lf_runtime_services_request_context_import_typing.Any
lf_runtime_services_request_context_Dict = lf_runtime_services_request_context_import_typing.Dict
lf_runtime_services_request_context_List = lf_runtime_services_request_context_import_typing.List
import langchain_core.messages as lf_runtime_services_request_context_import_langchain_core_messages
lf_runtime_services_request_context_HumanMessage = lf_runtime_services_request_context_import_langchain_core_messages.HumanMessage
lf_runtime_services_request_context_SystemMessage = lf_runtime_services_request_context_import_langchain_core_messages.SystemMessage
lf_runtime_services_request_context_DATASET_REGISTRY = lf_runtime_data_retrieval_DATASET_REGISTRY
lf_runtime_services_request_context_dataset_required_param_fields = lf_runtime_data_retrieval_dataset_required_param_fields
lf_runtime_services_request_context_get_dataset_label = lf_runtime_data_retrieval_get_dataset_label
lf_runtime_services_request_context_list_available_dataset_labels = lf_runtime_data_retrieval_list_available_dataset_labels
lf_runtime_services_request_context_pick_retrieval_tools = lf_runtime_data_retrieval_pick_retrieval_tools
lf_runtime_services_request_context_build_registered_domain_prompt = lf_runtime_domain_registry_build_registered_domain_prompt
lf_runtime_services_request_context_detect_registered_values = lf_runtime_domain_registry_detect_registered_values
lf_runtime_services_request_context_get_dataset_keyword_map = lf_runtime_domain_registry_get_dataset_keyword_map
lf_runtime_services_request_context_match_registered_analysis_rules = lf_runtime_domain_registry_match_registered_analysis_rules
lf_runtime_services_request_context_QueryMode = lf_runtime_graph_state_QueryMode
lf_runtime_services_request_context_SYSTEM_PROMPT = lf_runtime_shared_config_SYSTEM_PROMPT
lf_runtime_services_request_context_get_llm = lf_runtime_shared_config_get_llm
lf_runtime_services_request_context_normalize_text = lf_runtime_shared_filter_utils_normalize_text
lf_runtime_services_request_context_APPLIED_PARAM_FIELDS = ['date', 'process_name', 'oper_num', 'pkg_type1', 'pkg_type2', 'product_name', 'line_name', 'mode', 'den', 'tech', 'lead', 'mcp_no', 'group_by']
lf_runtime_services_request_context_POST_PROCESSING_KEYWORDS = ['비교', '정렬', '순위', '상위', '하위', '요약', '집계', '그룹', '그룹핑', '목록', '추세', '분석', '기준', '별', 'list', 'top', 'rank', 'group by']
lf_runtime_services_request_context_FILTER_REMOVAL_KEYWORDS = ['전체', 'all', '모두', '빼고', '제거', '제외', '없이']

def lf_runtime_services_request_context_get_llm_for_task(task: str, temperature: float=0.0):
    """모델 생성 함수를 안전하게 감싼다.

    테스트에서는 `get_llm` 이 단순 monkeypatch 로 바뀌는 경우가 많아서
    인자 시그니처가 조금 달라도 동작하도록 방어적으로 작성했다.
    """
    try:
        return lf_runtime_services_request_context_get_llm(task=task, temperature=temperature)
    except TypeError:
        try:
            return lf_runtime_services_request_context_get_llm(temperature=temperature)
        except TypeError:
            return lf_runtime_services_request_context_get_llm()

def lf_runtime_services_request_context_build_recent_chat_text(chat_history: lf_runtime_services_request_context_List[lf_runtime_services_request_context_Dict[str, str]], max_messages: int=6) -> str:
    """최근 대화를 사람이 읽기 쉬운 텍스트로 압축한다."""
    if not chat_history:
        return '(최근 대화 없음)'
    lines = []
    for message in chat_history[-max_messages:]:
        content = str(message.get('content', '')).strip()
        if content:
            lines.append(f"- {message.get('role', 'unknown')}: {content}")
    return '\n'.join(lines) if lines else '(최근 대화 없음)'

def lf_runtime_services_request_context_get_current_table_columns(current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> lf_runtime_services_request_context_List[str]:
    """현재 결과 테이블에 어떤 컬럼이 있는지 모아 반환한다."""
    if not isinstance(current_data, dict):
        return []
    rows = current_data.get('data', [])
    if not isinstance(rows, list):
        return []
    columns = set()
    for row in rows:
        if isinstance(row, dict):
            columns.update(row.keys())
    return sorted(columns)

def lf_runtime_services_request_context_has_current_data(current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> bool:
    """현재 테이블이 실제로 존재하는지 빠르게 확인한다."""
    return bool(isinstance(current_data, dict) and isinstance(current_data.get('data'), list) and current_data.get('data'))

def lf_runtime_services_request_context_raw_dataset_key(dataset_key: str) -> str:
    """`production__today` 같은 키에서 원본 데이터셋 키만 꺼낸다."""
    return str(dataset_key or '').split('__', 1)[0]

def lf_runtime_services_request_context_collect_applied_params(extracted_params: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]) -> lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]:
    """파라미터 추출 결과 중 실제로 값이 있는 필드만 남긴다."""
    return {field: extracted_params.get(field) for field in lf_runtime_services_request_context_APPLIED_PARAM_FIELDS if extracted_params.get(field)}

def lf_runtime_services_request_context_attach_result_metadata(result: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any], extracted_params: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any], original_tool_name: str) -> lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]:
    """결과 딕셔너리에 추적용 메타데이터를 붙인다.

    이후 follow-up 질문에서 "이 결과가 어떤 조건으로 조회됐는지" 판단할 때 사용한다.
    """
    if result.get('success'):
        result['original_tool_name'] = original_tool_name
        result['applied_params'] = lf_runtime_services_request_context_collect_applied_params(extracted_params)
        if 'source_dataset_keys' not in result:
            dataset_key = str(result.get('dataset_key', '')).strip()
            result['source_dataset_keys'] = [lf_runtime_services_request_context_raw_dataset_key(dataset_key)] if dataset_key else []
        result['available_columns'] = lf_runtime_services_request_context_get_current_table_columns(result)
    return result

def lf_runtime_services_request_context_collect_current_source_dataset_keys(current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> lf_runtime_services_request_context_List[str]:
    """현재 결과가 어떤 원천 데이터셋에서 왔는지 추적한다."""
    if not isinstance(current_data, dict):
        return []
    explicit_keys = [lf_runtime_services_request_context_raw_dataset_key(item) for item in current_data.get('source_dataset_keys', []) if item]
    if explicit_keys:
        return list(dict.fromkeys(explicit_keys))
    source_snapshots = current_data.get('source_snapshots', [])
    if isinstance(source_snapshots, list):
        dataset_keys = [lf_runtime_services_request_context_raw_dataset_key(str(item.get('dataset_key', ''))) for item in source_snapshots if isinstance(item, dict) and item.get('dataset_key')]
        if dataset_keys:
            return list(dict.fromkeys(dataset_keys))
    current_datasets = current_data.get('current_datasets', {})
    if isinstance(current_datasets, list):
        dataset_keys = [lf_runtime_services_request_context_raw_dataset_key(str(item.get('dataset_key', ''))) for item in current_datasets if isinstance(item, dict) and item.get('dataset_key')]
        if dataset_keys:
            return list(dict.fromkeys(dataset_keys))
    if isinstance(current_datasets, dict):
        dataset_keys = [lf_runtime_services_request_context_raw_dataset_key(key) for key in current_datasets.keys() if str(key).strip()]
        if dataset_keys:
            return list(dict.fromkeys(dataset_keys))
    dataset_key = str(current_data.get('dataset_key', '')).strip()
    if dataset_key:
        return [lf_runtime_services_request_context_raw_dataset_key(dataset_key)]
    return []

def lf_runtime_services_request_context_collect_source_snapshots(current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> lf_runtime_services_request_context_List[lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]]:
    """현재 결과에 연결된 raw source snapshot 목록을 반환한다."""
    if not isinstance(current_data, dict):
        return []
    source_snapshots = current_data.get('source_snapshots', [])
    if isinstance(source_snapshots, list):
        return [item for item in source_snapshots if isinstance(item, dict)]
    current_datasets = current_data.get('current_datasets', {})
    if isinstance(current_datasets, dict):
        snapshots: lf_runtime_services_request_context_List[lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]] = []
        for dataset_key, snapshot in current_datasets.items():
            if not isinstance(snapshot, dict):
                continue
            snapshots.append({'dataset_key': dataset_key, 'dataset_label': snapshot.get('label', lf_runtime_services_request_context_get_dataset_label(str(dataset_key))), 'tool_name': snapshot.get('tool_name', ''), 'summary': snapshot.get('summary', ''), 'row_count': snapshot.get('row_count', 0), 'columns': snapshot.get('columns', []), 'required_params': snapshot.get('required_params', {}), 'data': snapshot.get('data', [])})
        return snapshots
    return []

def lf_runtime_services_request_context_collect_requested_dataset_keys(user_input: str) -> lf_runtime_services_request_context_List[str]:
    """질문이 필요로 하는 데이터셋 후보를 모은다.

    기본 키워드 매칭 결과에 더해, 사용자 정의 분석 규칙이 요구하는 데이터셋도 같이 포함한다.
    """
    dataset_keys = [key for key in lf_runtime_services_request_context_pick_retrieval_tools(user_input) if key in lf_runtime_services_request_context_DATASET_REGISTRY]
    for rule in lf_runtime_services_request_context_match_registered_analysis_rules(user_input):
        for dataset_key in rule.get('required_datasets', []):
            if dataset_key in lf_runtime_services_request_context_DATASET_REGISTRY and dataset_key not in dataset_keys:
                dataset_keys.append(dataset_key)
    return dataset_keys

def lf_runtime_services_request_context_normalize_filter_value(value: lf_runtime_services_request_context_Any) -> lf_runtime_services_request_context_Any:
    """필터 비교를 쉽게 하기 위해 값을 문자열/정렬 리스트 형태로 맞춘다."""
    if isinstance(value, list):
        return sorted((str(item) for item in value))
    return str(value) if value not in (None, '', []) else None

def lf_runtime_services_request_context__inherited_flag_name(field_name: str) -> str:
    """필드명에 대응하는 inherited 플래그 이름을 반환한다."""
    custom_flags = {'process_name': 'process_inherited', 'product_name': 'product_inherited', 'line_name': 'line_inherited'}
    return custom_flags.get(field_name, f'{field_name}_inherited')

def lf_runtime_services_request_context_user_explicitly_mentions_filter(field_name: str, user_input: str) -> bool:
    """사용자가 특정 필터를 직접 언급했는지 확인한다."""
    normalized = lf_runtime_services_request_context_normalize_text(user_input)
    keyword_map = {'date': ['오늘', '어제', 'date', '일자', '날짜'], 'process_name': ['공정', 'process', 'wb', 'da', 'wet', 'lt', 'bg', 'hs', 'ws', 'sat', 'fcb'], 'oper_num': ['oper', '공정번호', 'operation'], 'pkg_type1': ['pkg', 'fcbga', 'lfbga'], 'pkg_type2': ['stack', 'odp', '16dp', 'sdp'], 'product_name': ['제품', 'product', 'hbm', '3ds', 'auto'], 'line_name': ['라인', 'line'], 'mode': ['mode', 'ddr', 'lpddr'], 'den': ['den', '용량', '256g', '512g', '1t'], 'tech': ['tech', 'lc', 'fo', 'fc'], 'lead': ['lead'], 'mcp_no': ['mcp']}
    return any((token in normalized for token in keyword_map.get(field_name, [])))

def lf_runtime_services_request_context_has_explicit_filter_change(user_input: str, extracted_params: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any], current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> bool:
    """현재 결과와 비교했을 때 사용자가 새 필터를 요구했는지 판단한다."""
    current_filters = {}
    if isinstance(current_data, dict):
        current_filters = current_data.get('retrieval_applied_params') or current_data.get('applied_params', {}) or {}
    normalized_user_input = lf_runtime_services_request_context_normalize_text(user_input)
    for field_name in lf_runtime_services_request_context_APPLIED_PARAM_FIELDS:
        if field_name == 'group_by':
            continue
        new_value = extracted_params.get(field_name)
        current_value = current_filters.get(field_name)
        if lf_runtime_services_request_context_normalize_filter_value(new_value) == lf_runtime_services_request_context_normalize_filter_value(current_value):
            continue
        if extracted_params.get(lf_runtime_services_request_context__inherited_flag_name(field_name)):
            continue
        if current_value not in (None, '', []) and new_value in (None, '', []) and lf_runtime_services_request_context_user_explicitly_mentions_filter(field_name, user_input):
            if any((token in normalized_user_input for token in lf_runtime_services_request_context_FILTER_REMOVAL_KEYWORDS)):
                return True
        if new_value and lf_runtime_services_request_context_user_explicitly_mentions_filter(field_name, user_input):
            return True
        if lf_runtime_services_request_context_detect_registered_values(field_name, user_input):
            return True
    return False

def lf_runtime_services_request_context_has_required_param_change(extracted_params: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any], current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None, dataset_keys: lf_runtime_services_request_context_List[str]) -> bool:
    """질문에 필요한 필수 파라미터가 바뀌었는지 확인한다.

    예를 들어 날짜가 필수인 테이블은 날짜가 바뀌는 순간 raw source 자체가 달라진다.
    이 경우는 단순 follow-up 이 아니라 새 조회 경로로 보내야 한다.
    """
    if not isinstance(current_data, dict):
        return False
    current_filters = current_data.get('retrieval_applied_params') or current_data.get('applied_params', {}) or {}
    effective_dataset_keys = dataset_keys or lf_runtime_services_request_context_collect_current_source_dataset_keys(current_data)
    required_fields: lf_runtime_services_request_context_List[str] = []
    for dataset_key in effective_dataset_keys:
        for field_name in lf_runtime_services_request_context_dataset_required_param_fields(lf_runtime_services_request_context_raw_dataset_key(dataset_key)):
            if field_name not in required_fields:
                required_fields.append(field_name)
    for field_name in required_fields:
        new_value = extracted_params.get(field_name)
        current_value = current_filters.get(field_name)
        if lf_runtime_services_request_context_normalize_filter_value(new_value) == lf_runtime_services_request_context_normalize_filter_value(current_value):
            continue
        if new_value not in (None, '', []):
            return True
    return False

def lf_runtime_services_request_context_is_summary_result(current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> bool:
    """현재 결과가 raw source가 아니라 요약/집계 결과인지 빠르게 판단한다."""
    if not isinstance(current_data, dict):
        return False
    tool_name = str(current_data.get('tool_name', '') or '')
    if tool_name == 'multi_dataset_overview':
        return True
    if current_data.get('analysis_base_info'):
        return True
    return False

def lf_runtime_services_request_context_build_current_data_profile(current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None) -> lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]:
    """현재 테이블 상태를 LLM 검토에 넘기기 좋은 작은 요약으로 만든다."""
    return {'tool_name': str((current_data or {}).get('tool_name', '')), 'source_dataset_keys': lf_runtime_services_request_context_collect_current_source_dataset_keys(current_data), 'applied_params': dict((current_data or {}).get('retrieval_applied_params') or (current_data or {}).get('applied_params', {}) or {}), 'columns': lf_runtime_services_request_context_get_current_table_columns(current_data)}

def lf_runtime_services_request_context_attach_source_dataset_metadata(result: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any], source_results: lf_runtime_services_request_context_List[lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]]) -> None:
    """최종 결과에 원천 데이터셋 목록을 붙인다."""
    result['source_dataset_keys'] = list(dict.fromkeys((lf_runtime_services_request_context_raw_dataset_key(str(item.get('dataset_key', ''))) for item in source_results if item.get('dataset_key'))))

def lf_runtime_services_request_context_review_query_mode_with_llm(user_input: str, current_data: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any] | None, extracted_params: lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any], requested_dataset_keys: lf_runtime_services_request_context_List[str]) -> lf_runtime_services_request_context_QueryMode:
    """규칙만으로 애매할 때 LLM에게 마지막 판단을 맡긴다.

    이미 현재 데이터가 충분해 보일 때만 호출한다.
    즉, 명확하게 새 조회가 필요한 경우에는 이 함수까지 오지 않는다.
    """
    if not lf_runtime_services_request_context_has_current_data(current_data):
        return 'retrieval'
    profile = lf_runtime_services_request_context_build_current_data_profile(current_data)
    prompt = f'You are deciding whether a manufacturing follow-up question should reuse the current table\nor fetch fresh source data. Return JSON only.\n\nRules:\n- Choose `retrieval` when the user is asking for a different raw dataset, a different process/date/product filter,\n  or a new source table that is not already included in the current result.\n- Choose `followup_transform` when the current table is enough and the user is mainly asking for grouping,\n  sorting, ranking, filtering, comparison, or a light recomputation on the same scope.\n\nUser question:\n{user_input}\n\nCurrent table profile:\n{lf_runtime_services_request_context_json.dumps(profile, ensure_ascii=False)}\n\nExtracted filters:\n{lf_runtime_services_request_context_json.dumps(lf_runtime_services_request_context_collect_applied_params(extracted_params), ensure_ascii=False)}\n\nRequested dataset keys:\n{lf_runtime_services_request_context_json.dumps(requested_dataset_keys, ensure_ascii=False)}\n\nReturn only:\n{{\n  "query_mode": "retrieval",\n  "reason": "short reason"\n}}'
    try:
        llm = lf_runtime_services_request_context_get_llm_for_task('query_mode_review')
        response = llm.invoke([lf_runtime_services_request_context_SystemMessage(content=lf_runtime_services_request_context_SYSTEM_PROMPT), lf_runtime_services_request_context_HumanMessage(content=prompt)])
        parsed = lf_runtime_services_request_context_parse_json_block(lf_runtime_services_request_context_extract_text_from_response(response.content))
        if parsed.get('query_mode') == 'followup_transform':
            return 'followup_transform'
    except Exception:
        pass
    return 'retrieval'

def lf_runtime_services_request_context_build_unknown_retrieval_message() -> str:
    """어떤 데이터셋을 봐야 할지 찾지 못했을 때의 안내 문구를 만든다."""
    available_labels = lf_runtime_services_request_context_list_available_dataset_labels()
    if not available_labels:
        return '질문과 맞는 데이터셋을 바로 찾지 못했습니다. 어떤 데이터를 보고 싶은지 조금 더 구체적으로 말씀해 주세요.'
    return '질문과 맞는 데이터셋을 바로 찾지 못했습니다. 현재 조회 가능한 데이터는 ' + ', '.join(available_labels) + ' 입니다.'

def lf_runtime_services_request_context_extract_text_from_response(content: lf_runtime_services_request_context_Any) -> str:
    """LLM 응답이 문자열/리스트 어느 형태든 텍스트로 평탄화한다."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: lf_runtime_services_request_context_List[str] = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                parts.append(str(item['text']))
            elif isinstance(item, str):
                parts.append(item)
        return '\n'.join(parts)
    return str(content)

def lf_runtime_services_request_context_parse_json_block(text: str) -> lf_runtime_services_request_context_Dict[str, lf_runtime_services_request_context_Any]:
    """마크다운 코드블록이 섞여 있어도 JSON 객체만 꺼내 파싱한다."""
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
        return lf_runtime_services_request_context_json.loads(cleaned[start:end + 1])
    except Exception:
        return {}

def lf_runtime_services_request_context_build_dataset_catalog_text() -> str:
    """등록된 데이터셋과 키워드 목록을 LLM 프롬프트용 텍스트로 만든다."""
    lines: lf_runtime_services_request_context_List[str] = []
    keyword_map = lf_runtime_services_request_context_get_dataset_keyword_map()
    for dataset_key, meta in lf_runtime_services_request_context_DATASET_REGISTRY.items():
        keywords = ', '.join((str(keyword) for keyword in keyword_map.get(dataset_key, meta.get('keywords', []))))
        lines.append(f"- {dataset_key}: label={meta.get('label', dataset_key)}, keywords={keywords}")
    return '\n'.join(lines)

def lf_runtime_services_request_context_get_dataset_labels_for_message(dataset_keys: lf_runtime_services_request_context_List[str]) -> lf_runtime_services_request_context_List[str]:
    """사용자 안내 메시지에 넣을 표시용 데이터셋 이름을 반환한다."""
    return [lf_runtime_services_request_context_get_dataset_label(key) for key in dataset_keys]

# ---- visible runtime: _runtime.services.query_mode ----
"""질문을 새 조회로 처리할지, 현재 테이블 후처리로 처리할지 판단하는 서비스."""
import re as lf_runtime_services_query_mode_re
import typing as lf_runtime_services_query_mode_import_typing
lf_runtime_services_query_mode_Any = lf_runtime_services_query_mode_import_typing.Any
lf_runtime_services_query_mode_Dict = lf_runtime_services_query_mode_import_typing.Dict
lf_runtime_services_query_mode_pick_retrieval_tools = lf_runtime_data_retrieval_pick_retrieval_tools
lf_runtime_services_query_mode_QUERY_MODE_SIGNAL_SPECS = lf_runtime_domain_knowledge_QUERY_MODE_SIGNAL_SPECS
lf_runtime_services_query_mode_QueryMode = lf_runtime_graph_state_QueryMode
lf_runtime_services_query_mode_normalize_text = lf_runtime_shared_filter_utils_normalize_text
lf_runtime_services_query_mode_POST_PROCESSING_KEYWORDS = lf_runtime_services_request_context_POST_PROCESSING_KEYWORDS
lf_runtime_services_query_mode_collect_current_source_dataset_keys = lf_runtime_services_request_context_collect_current_source_dataset_keys
lf_runtime_services_query_mode_collect_requested_dataset_keys = lf_runtime_services_request_context_collect_requested_dataset_keys
lf_runtime_services_query_mode_has_current_data = lf_runtime_services_request_context_has_current_data
lf_runtime_services_query_mode_has_explicit_filter_change = lf_runtime_services_request_context_has_explicit_filter_change
lf_runtime_services_query_mode_has_required_param_change = lf_runtime_services_request_context_has_required_param_change
lf_runtime_services_query_mode_is_summary_result = lf_runtime_services_request_context_is_summary_result
lf_runtime_services_query_mode_review_query_mode_with_llm = lf_runtime_services_request_context_review_query_mode_with_llm

def lf_runtime_services_query_mode__matches_query_mode_signal(query_text: str, signal_name: str) -> bool:
    """도메인에 정의된 query mode 신호 스펙으로 표현을 감지한다."""
    signal_spec = lf_runtime_services_query_mode_QUERY_MODE_SIGNAL_SPECS.get(signal_name, {})
    normalized = lf_runtime_services_query_mode_normalize_text(query_text)
    if any((token in normalized for token in signal_spec.get('keywords', []))):
        return True
    return any((lf_runtime_services_query_mode_re.search(pattern, str(query_text or ''), flags=lf_runtime_services_query_mode_re.IGNORECASE) for pattern in signal_spec.get('patterns', [])))

def lf_runtime_services_query_mode_has_explicit_date_reference(query_text: str) -> bool:
    """질문 안에 날짜가 직접 언급됐는지 확인한다."""
    return lf_runtime_services_query_mode__matches_query_mode_signal(query_text, 'explicit_date_reference')

def lf_runtime_services_query_mode_mentions_grouping_expression(query_text: str) -> bool:
    """`MODE별`, `공정 기준`, `by line` 같은 그룹화 의도를 찾는다."""
    return lf_runtime_services_query_mode__matches_query_mode_signal(query_text, 'grouping_expression')

def lf_runtime_services_query_mode_needs_post_processing(query_text: str, extracted_params: lf_runtime_services_query_mode_Dict[str, lf_runtime_services_query_mode_Any] | None=None, retrieval_plan: lf_runtime_services_query_mode_Dict[str, lf_runtime_services_query_mode_Any] | None=None) -> bool:
    """조회 후에 pandas 후처리가 필요한 질문인지 판단한다."""
    match_registered_analysis_rules = lf_runtime_domain_registry_match_registered_analysis_rules
    extracted_params = extracted_params or {}
    normalized = lf_runtime_services_query_mode_normalize_text(query_text)
    if retrieval_plan and retrieval_plan.get('needs_post_processing'):
        return True
    if match_registered_analysis_rules(query_text):
        return True
    if extracted_params.get('group_by'):
        return True
    if lf_runtime_services_query_mode_mentions_grouping_expression(query_text):
        return True
    return any((token in normalized for token in lf_runtime_services_query_mode_POST_PROCESSING_KEYWORDS))

def lf_runtime_services_query_mode_looks_like_new_data_request(query_text: str) -> bool:
    """사용자 의도가 새 원천 데이터를 가져오는 쪽에 가까운지 판단한다."""
    retrieval_keys = lf_runtime_services_query_mode_pick_retrieval_tools(query_text)
    if lf_runtime_services_query_mode_has_explicit_date_reference(query_text):
        return True
    if len(retrieval_keys) >= 2:
        return True
    if retrieval_keys and lf_runtime_services_query_mode__matches_query_mode_signal(query_text, 'fresh_retrieval_hint'):
        return True
    return lf_runtime_services_query_mode__matches_query_mode_signal(query_text, 'retrieval_request') and (not lf_runtime_services_query_mode_needs_post_processing(query_text))

def lf_runtime_services_query_mode_prune_followup_params(user_input: str, extracted_params: lf_runtime_services_query_mode_Dict[str, lf_runtime_services_query_mode_Any]) -> lf_runtime_services_query_mode_Dict[str, lf_runtime_services_query_mode_Any]:
    """후속 분석에서 꼭 필요하지 않은 필터만 남기고 나머지는 걷어낸다."""
    cleaned = dict(extracted_params or {})
    filter_fields = ['process_name', 'oper_num', 'pkg_type1', 'pkg_type2', 'product_name', 'line_name', 'mode', 'den', 'tech', 'lead', 'mcp_no']
    explicit_filter_intent = lf_runtime_services_query_mode__matches_query_mode_signal(user_input, 'followup_filter_intent')
    if not explicit_filter_intent:
        for field in filter_fields:
            cleaned[field] = None
    return cleaned

def lf_runtime_services_query_mode_choose_query_mode(user_input: str, current_data: lf_runtime_services_query_mode_Dict[str, lf_runtime_services_query_mode_Any] | None, extracted_params: lf_runtime_services_query_mode_Dict[str, lf_runtime_services_query_mode_Any]) -> lf_runtime_services_query_mode_QueryMode:
    """질문을 `retrieval`과 `followup_transform` 중 어디로 보낼지 결정한다."""
    if not lf_runtime_services_query_mode_has_current_data(current_data):
        return 'retrieval'
    requested_dataset_keys = lf_runtime_services_query_mode_collect_requested_dataset_keys(user_input)
    current_dataset_keys = lf_runtime_services_query_mode_collect_current_source_dataset_keys(current_data)
    if requested_dataset_keys and (not set(requested_dataset_keys).issubset(set(current_dataset_keys))):
        return 'retrieval'
    if lf_runtime_services_query_mode_has_required_param_change(extracted_params, current_data, requested_dataset_keys):
        return 'retrieval'
    if lf_runtime_services_query_mode_has_explicit_filter_change(user_input, extracted_params, current_data):
        return 'retrieval'
    if lf_runtime_services_query_mode_is_summary_result(current_data) and lf_runtime_services_query_mode_looks_like_new_data_request(user_input):
        return 'retrieval'
    if not lf_runtime_services_query_mode_looks_like_new_data_request(user_input):
        return 'followup_transform'
    if requested_dataset_keys and set(requested_dataset_keys).issubset(set(current_dataset_keys)):
        return lf_runtime_services_query_mode_review_query_mode_with_llm(user_input, current_data, extracted_params, requested_dataset_keys)
    return 'retrieval'

# ---- visible runtime: _runtime.services.retrieval_planner ----
"""원천 데이터 조회 계획과 실제 실행 job 생성을 담당하는 서비스."""
import copy as lf_runtime_services_retrieval_planner_copy
import json as lf_runtime_services_retrieval_planner_json
import re as lf_runtime_services_retrieval_planner_re
import concurrent.futures as lf_runtime_services_retrieval_planner_import_concurrent_futures
lf_runtime_services_retrieval_planner_ThreadPoolExecutor = lf_runtime_services_retrieval_planner_import_concurrent_futures.ThreadPoolExecutor
import datetime as lf_runtime_services_retrieval_planner_import_datetime
lf_runtime_services_retrieval_planner_datetime = lf_runtime_services_retrieval_planner_import_datetime.datetime
lf_runtime_services_retrieval_planner_timedelta = lf_runtime_services_retrieval_planner_import_datetime.timedelta
import typing as lf_runtime_services_retrieval_planner_import_typing
lf_runtime_services_retrieval_planner_Any = lf_runtime_services_retrieval_planner_import_typing.Any
lf_runtime_services_retrieval_planner_Dict = lf_runtime_services_retrieval_planner_import_typing.Dict
lf_runtime_services_retrieval_planner_List = lf_runtime_services_retrieval_planner_import_typing.List
import langchain_core.messages as lf_runtime_services_retrieval_planner_import_langchain_core_messages
lf_runtime_services_retrieval_planner_HumanMessage = lf_runtime_services_retrieval_planner_import_langchain_core_messages.HumanMessage
lf_runtime_services_retrieval_planner_SystemMessage = lf_runtime_services_retrieval_planner_import_langchain_core_messages.SystemMessage
lf_runtime_services_retrieval_planner_DATASET_REGISTRY = lf_runtime_data_retrieval_DATASET_REGISTRY
lf_runtime_services_retrieval_planner_dataset_requires_date = lf_runtime_data_retrieval_dataset_requires_date
lf_runtime_services_retrieval_planner_execute_retrieval_tools = lf_runtime_data_retrieval_execute_retrieval_tools
lf_runtime_services_retrieval_planner_pick_retrieval_tools = lf_runtime_data_retrieval_pick_retrieval_tools
lf_runtime_services_retrieval_planner_build_registered_domain_prompt = lf_runtime_domain_registry_build_registered_domain_prompt
lf_runtime_services_retrieval_planner_format_analysis_rule_for_prompt = lf_runtime_domain_registry_format_analysis_rule_for_prompt
lf_runtime_services_retrieval_planner_get_registered_analysis_rules = lf_runtime_domain_registry_get_registered_analysis_rules
lf_runtime_services_retrieval_planner_match_registered_analysis_rules = lf_runtime_domain_registry_match_registered_analysis_rules
lf_runtime_services_retrieval_planner_SYSTEM_PROMPT = lf_runtime_shared_config_SYSTEM_PROMPT
lf_runtime_services_retrieval_planner_normalize_text = lf_runtime_shared_filter_utils_normalize_text
lf_runtime_services_retrieval_planner_mentions_grouping_expression = lf_runtime_services_query_mode_mentions_grouping_expression
lf_runtime_services_retrieval_planner_POST_PROCESSING_KEYWORDS = lf_runtime_services_request_context_POST_PROCESSING_KEYWORDS
lf_runtime_services_retrieval_planner_build_dataset_catalog_text = lf_runtime_services_request_context_build_dataset_catalog_text
lf_runtime_services_retrieval_planner_build_recent_chat_text = lf_runtime_services_request_context_build_recent_chat_text
lf_runtime_services_retrieval_planner_extract_text_from_response = lf_runtime_services_request_context_extract_text_from_response
lf_runtime_services_retrieval_planner_get_current_table_columns = lf_runtime_services_request_context_get_current_table_columns
lf_runtime_services_retrieval_planner_get_dataset_labels_for_message = lf_runtime_services_request_context_get_dataset_labels_for_message
lf_runtime_services_retrieval_planner_get_llm_for_task = lf_runtime_services_request_context_get_llm_for_task
lf_runtime_services_retrieval_planner_parse_json_block = lf_runtime_services_request_context_parse_json_block
lf_runtime_services_retrieval_planner_EXPLICIT_DATASET_KEYWORDS = {'production': ['생산', '생산량', '실적', 'production'], 'target': ['목표', '목표량', '계획', 'target'], 'wip': ['재공', 'wip', '대기'], 'equipment': ['설비', '가동률', 'equipment'], 'defect': ['불량', '결함', 'defect'], 'yield': ['수율', 'yield'], 'hold': ['홀드', '보류', 'hold'], 'scrap': ['스크랩', '폐기', 'scrap'], 'recipe': ['레시피', '공정 조건', 'recipe'], 'lot_trace': ['lot', '로트', '이력', '추적', 'trace']}
lf_runtime_services_retrieval_planner_RETRIEVAL_RESULT_CACHE: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]] = {}

def lf_runtime_services_retrieval_planner__normalize_merge_hints(raw_hints: lf_runtime_services_retrieval_planner_Any) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """LLM이 준 merge 힌트를 실행기가 바로 쓸 수 있는 형태로 정리한다."""
    if not isinstance(raw_hints, dict):
        return {}
    group_dimensions: lf_runtime_services_retrieval_planner_List[str] = []
    for column in raw_hints.get('group_dimensions', []) or []:
        column_name = str(column).strip()
        if column_name and column_name not in group_dimensions:
            group_dimensions.append(column_name)
    dataset_metrics: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_List[str]] = {}
    for dataset_key, columns in (raw_hints.get('dataset_metrics', {}) or {}).items():
        normalized_dataset_key = lf_runtime_services_retrieval_planner_normalize_text(dataset_key)
        if normalized_dataset_key not in lf_runtime_services_retrieval_planner_DATASET_REGISTRY:
            continue
        metric_list: lf_runtime_services_retrieval_planner_List[str] = []
        for column in columns or []:
            column_name = str(column).strip()
            if column_name and column_name not in metric_list:
                metric_list.append(column_name)
        if metric_list:
            dataset_metrics[normalized_dataset_key] = metric_list
    aggregation = str(raw_hints.get('aggregation', 'sum')).strip().lower() or 'sum'
    if aggregation not in {'sum', 'mean', 'max', 'min', 'count'}:
        aggregation = 'sum'
    return {'pre_aggregate_before_join': bool(raw_hints.get('pre_aggregate_before_join')), 'group_dimensions': group_dimensions, 'dataset_metrics': dataset_metrics, 'aggregation': aggregation, 'reason': str(raw_hints.get('reason', '')).strip()}

def lf_runtime_services_retrieval_planner__dedupe_dataset_keys(dataset_keys: lf_runtime_services_retrieval_planner_List[str]) -> lf_runtime_services_retrieval_planner_List[str]:
    """등록된 dataset key만 남기면서 순서를 유지해 중복을 제거한다."""
    ordered: lf_runtime_services_retrieval_planner_List[str] = []
    for dataset_key in dataset_keys:
        if dataset_key in lf_runtime_services_retrieval_planner_DATASET_REGISTRY and dataset_key not in ordered:
            ordered.append(dataset_key)
    return ordered

def lf_runtime_services_retrieval_planner__infer_explicit_dataset_keys(user_input: str) -> lf_runtime_services_retrieval_planner_List[str]:
    """질문에 직접 언급된 dataset 키를 규칙 기반으로 읽어낸다."""
    normalized_query = lf_runtime_services_retrieval_planner_normalize_text(user_input)
    detected_keys: lf_runtime_services_retrieval_planner_List[str] = []
    for dataset_key, keywords in lf_runtime_services_retrieval_planner_EXPLICIT_DATASET_KEYWORDS.items():
        if any((lf_runtime_services_retrieval_planner_normalize_text(keyword) in normalized_query for keyword in keywords)):
            detected_keys.append(dataset_key)
    return lf_runtime_services_retrieval_planner__dedupe_dataset_keys(detected_keys)

def lf_runtime_services_retrieval_planner__build_analysis_rule_catalog_text() -> str:
    """LLM review 에 넘길 분석 rule 요약 텍스트를 만든다."""
    rules = lf_runtime_services_retrieval_planner_get_registered_analysis_rules()
    if not rules:
        return '(none)'
    return '\n'.join((lf_runtime_services_retrieval_planner_format_analysis_rule_for_prompt(rule) for rule in rules))

def lf_runtime_services_retrieval_planner__review_missing_base_dataset_keys(user_input: str, chat_history: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, str]], current_columns: lf_runtime_services_retrieval_planner_List[str], planned_dataset_keys: lf_runtime_services_retrieval_planner_List[str]) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """LLM에게 부족한 base dataset만 다시 확인받는다."""
    prompt = f"""You are reviewing whether the planned manufacturing datasets miss any base datasets.\nReturn JSON only.\n\nRules:\n- Add only missing base datasets needed for the user's final answer.\n- Do not repeat already planned datasets.\n- Use the registered dataset list and analysis rule list.\n- If the current plan is already enough, return an empty list.\n- Do not invent dataset keys.\n\nRegistered dataset list:\n{lf_runtime_services_retrieval_planner_build_dataset_catalog_text()}\n\nRegistered analysis rules:\n{lf_runtime_services_retrieval_planner__build_analysis_rule_catalog_text()}\n\nCustom domain registry:\n{lf_runtime_services_retrieval_planner_build_registered_domain_prompt()}\n\nRecent chat:\n{lf_runtime_services_retrieval_planner_build_recent_chat_text(chat_history)}\n\nCurrent data columns:\n{(', '.join(current_columns) if current_columns else '(none)')}\n\nCurrent planned dataset keys:\n{lf_runtime_services_retrieval_planner_json.dumps(planned_dataset_keys, ensure_ascii=False)}\n\nUser question:\n{user_input}\n\nReturn only:\n{{\n  "missing_dataset_keys": [],\n  "needs_post_processing": false,\n  "reason": "short explanation"\n}}"""
    try:
        llm = lf_runtime_services_retrieval_planner_get_llm_for_task('retrieval_plan')
        response = llm.invoke([lf_runtime_services_retrieval_planner_SystemMessage(content=lf_runtime_services_retrieval_planner_SYSTEM_PROMPT), lf_runtime_services_retrieval_planner_HumanMessage(content=prompt)])
        parsed = lf_runtime_services_retrieval_planner_parse_json_block(lf_runtime_services_retrieval_planner_extract_text_from_response(response.content))
    except Exception:
        parsed = {}
    missing_dataset_keys = lf_runtime_services_retrieval_planner__dedupe_dataset_keys([key for key in parsed.get('missing_dataset_keys', []) if key not in planned_dataset_keys])
    return {'missing_dataset_keys': missing_dataset_keys, 'needs_post_processing': bool(parsed.get('needs_post_processing', False)), 'reason': str(parsed.get('reason', '')).strip()}

def lf_runtime_services_retrieval_planner__finalize_merge_hints(raw_hints: lf_runtime_services_retrieval_planner_Any, final_dataset_keys: lf_runtime_services_retrieval_planner_List[str]) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """최종 dataset 조합에 맞게 merge hint를 정리해 불일치를 막는다."""
    normalized_hints = lf_runtime_services_retrieval_planner__normalize_merge_hints(raw_hints)
    if not normalized_hints:
        return {}
    allowed_dataset_keys = {lf_runtime_services_retrieval_planner_normalize_text(dataset_key) for dataset_key in final_dataset_keys}
    dataset_metrics = {dataset_key: columns for dataset_key, columns in normalized_hints.get('dataset_metrics', {}).items() if dataset_key in allowed_dataset_keys}
    if not dataset_metrics:
        return {}
    return {**normalized_hints, 'dataset_metrics': dataset_metrics}

def lf_runtime_services_retrieval_planner__is_explicit_dataset_listing_query(user_input: str, explicit_dataset_keys: lf_runtime_services_retrieval_planner_List[str], matched_rules: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]], needs_post_processing: bool=False) -> bool:
    """질문이 파생 분석이 아니라 dataset 자체를 나열해서 보여 달라는 요청인지 판단한다."""
    normalized_query = lf_runtime_services_retrieval_planner_normalize_text(user_input)
    if matched_rules:
        return False
    if needs_post_processing:
        return False
    if len(explicit_dataset_keys) < 2:
        return False
    if any((token in normalized_query for token in lf_runtime_services_retrieval_planner_POST_PROCESSING_KEYWORDS)):
        return False
    return any((token in str(user_input or '') for token in ['/', ',', ' 및 ', '와 ', '값']))

def lf_runtime_services_retrieval_planner_plan_retrieval_request(user_input: str, chat_history: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, str]], current_data: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any] | None, retry_context: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any] | None=None) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """질문에 필요한 원천 dataset 조합을 결정한다.

    기본 흐름은 LLM 계획을 먼저 받아오되, 아래 규칙 기반 보강을 반드시 거친다.
    1. 질문에 직접 등장한 dataset 키워드 보강
    2. 등록된 분석 규칙이 요구하는 dataset 보강
    3. 달성률/포화율 같은 파생 지표의 필수 dataset 보강
    4. 명시적 dataset 나열 질문이면 LLM보다 규칙 결과를 우선
    """
    current_columns = lf_runtime_services_retrieval_planner_get_current_table_columns(current_data)
    retry_section = ''
    if retry_context:
        retry_section = f"\n\nPrevious selection review:\n- already selected datasets: {', '.join(retry_context.get('selected_dataset_keys', [])) or '(none)'}\n- currently available columns: {', '.join(retry_context.get('available_columns', [])) or '(none)'}\n- current analysis outcome: {retry_context.get('analysis_outcome', '')}\n- current analysis goal: {retry_context.get('analysis_goal', '')}\n\nIf the previous selection was not enough to answer the user's real question,\nadd the missing base datasets this time.\n"
    prompt = f"""You are planning which registered datasets should be retrieved for a manufacturing assistant.\nReturn JSON only.\n\nRules:\n- Choose only dataset keys from the registered dataset list.\n- If the user asks for a derived metric or comparison, include every base dataset needed for that final answer.\n- Set `needs_post_processing` to true when the final answer requires grouping, joining, comparing, ranking, or creating a derived column after retrieval.\n- If the question needs a multi-dataset ratio or comparison, decide whether each dataset should be aggregated before join.\n- Use `merge_hints` to describe only execution hints, not final prose.\n- Do not invent dataset keys.\n\nRegistered dataset list:\n{lf_runtime_services_retrieval_planner_build_dataset_catalog_text()}\n\nCustom domain registry:\n{lf_runtime_services_retrieval_planner_build_registered_domain_prompt()}\n\nRecent chat:\n{lf_runtime_services_retrieval_planner_build_recent_chat_text(chat_history)}\n\nCurrent data columns:\n{(', '.join(current_columns) if current_columns else '(none)')}\n\nUser question:\n{user_input}\n{retry_section}\n\nReturn only:\n{{\n  "dataset_keys": ["production"],\n  "needs_post_processing": false,\n  "analysis_goal": "short description",\n  "merge_hints": {{\n    "pre_aggregate_before_join": false,\n    "group_dimensions": [],\n    "dataset_metrics": {{\n      "production": ["production"]\n    }},\n    "aggregation": "sum",\n    "reason": "short explanation"\n  }}\n}}"""
    try:
        llm = lf_runtime_services_retrieval_planner_get_llm_for_task('retrieval_plan')
        response = llm.invoke([lf_runtime_services_retrieval_planner_SystemMessage(content=lf_runtime_services_retrieval_planner_SYSTEM_PROMPT), lf_runtime_services_retrieval_planner_HumanMessage(content=prompt)])
        parsed = lf_runtime_services_retrieval_planner_parse_json_block(lf_runtime_services_retrieval_planner_extract_text_from_response(response.content))
    except Exception:
        parsed = {}
    dataset_keys = [key for key in parsed.get('dataset_keys', []) if key in lf_runtime_services_retrieval_planner_DATASET_REGISTRY]
    matched_rules = lf_runtime_services_retrieval_planner_match_registered_analysis_rules(user_input)
    explicit_dataset_keys = lf_runtime_services_retrieval_planner__infer_explicit_dataset_keys(user_input)
    keyword_dataset_keys = lf_runtime_services_retrieval_planner__dedupe_dataset_keys([*lf_runtime_services_retrieval_planner_pick_retrieval_tools(user_input), *explicit_dataset_keys, *[dataset_key for rule in matched_rules for dataset_key in rule.get('required_datasets', [])]])
    coverage_review = lf_runtime_services_retrieval_planner__review_missing_base_dataset_keys(user_input=user_input, chat_history=chat_history, current_columns=current_columns, planned_dataset_keys=dataset_keys)
    dataset_keys = lf_runtime_services_retrieval_planner__dedupe_dataset_keys([*dataset_keys, *coverage_review.get('missing_dataset_keys', []), *[dataset_key for rule in matched_rules for dataset_key in rule.get('required_datasets', [])]])
    normalized_query = lf_runtime_services_retrieval_planner_normalize_text(user_input)
    if not dataset_keys:
        dataset_keys = list(keyword_dataset_keys)
    elif keyword_dataset_keys and len(keyword_dataset_keys) == 1 and (len(dataset_keys) <= 1) and (not parsed.get('needs_post_processing', False)) and (not coverage_review.get('needs_post_processing', False)):
        dataset_keys = list(keyword_dataset_keys)
    elif len(keyword_dataset_keys) >= 2 and len(dataset_keys) <= 1:
        dataset_keys = lf_runtime_services_retrieval_planner__dedupe_dataset_keys([*dataset_keys, *keyword_dataset_keys])
    simple_single_dataset_request = len(dataset_keys) == 1 and (not matched_rules) and (not lf_runtime_services_retrieval_planner_mentions_grouping_expression(user_input)) and (not any((token in normalized_query for token in lf_runtime_services_retrieval_planner_POST_PROCESSING_KEYWORDS)))
    reviewed_needs_post_processing = bool(parsed.get('needs_post_processing', False) or coverage_review.get('needs_post_processing', False) or matched_rules)
    explicit_dataset_listing_request = lf_runtime_services_retrieval_planner__is_explicit_dataset_listing_query(user_input, explicit_dataset_keys, matched_rules, needs_post_processing=reviewed_needs_post_processing)
    merge_hints = lf_runtime_services_retrieval_planner__finalize_merge_hints(parsed.get('merge_hints'), dataset_keys)
    return {'dataset_keys': dataset_keys, 'needs_post_processing': False if simple_single_dataset_request or explicit_dataset_listing_request else reviewed_needs_post_processing, 'analysis_goal': str(parsed.get('analysis_goal', '')).strip() or ', '.join((str(rule.get('display_name') or rule.get('name')) for rule in matched_rules[:2])), 'merge_hints': merge_hints}

def lf_runtime_services_retrieval_planner_review_retrieval_sufficiency(user_input: str, source_results: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]], retrieval_plan: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any] | None) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """현재 선택한 dataset만으로 최종 질문을 답할 수 있는지 재검토한다."""
    if not source_results:
        return {'is_sufficient': True, 'missing_dataset_keys': [], 'reason': ''}
    selected_dataset_keys = [str(result.get('dataset_key', '')) for result in source_results if result.get('dataset_key')]
    available_columns = lf_runtime_services_retrieval_planner_get_current_table_columns(source_results[-1])
    prompt = f"""You are reviewing whether the currently selected manufacturing datasets are sufficient.\nReturn JSON only.\n\nRules:\n- Judge sufficiency based on the user's real question, not on what is already available.\n- If the final answer needs a comparison, ratio, achievement rate, or multi-source calculation, make sure every raw dataset needed for that answer is selected.\n- If the current selection is insufficient, list the missing dataset keys from the registered dataset list.\n- Do not invent dataset keys.\n\nRegistered dataset list:\n{lf_runtime_services_retrieval_planner_build_dataset_catalog_text()}\n\nUser question:\n{user_input}\n\nCurrent retrieval plan:\n{retrieval_plan}\n\nCurrently selected dataset keys:\n{(', '.join(selected_dataset_keys) if selected_dataset_keys else '(none)')}\n\nCurrently available columns:\n{(', '.join(available_columns) if available_columns else '(none)')}\n\nReturn only:\n{{\n  "is_sufficient": true,\n  "missing_dataset_keys": [],\n  "reason": "short explanation"\n}}"""
    try:
        llm = lf_runtime_services_retrieval_planner_get_llm_for_task('sufficiency_review')
        response = llm.invoke([lf_runtime_services_retrieval_planner_SystemMessage(content=lf_runtime_services_retrieval_planner_SYSTEM_PROMPT), lf_runtime_services_retrieval_planner_HumanMessage(content=prompt)])
        parsed = lf_runtime_services_retrieval_planner_parse_json_block(lf_runtime_services_retrieval_planner_extract_text_from_response(response.content))
    except Exception:
        parsed = {}
    missing_dataset_keys = [key for key in parsed.get('missing_dataset_keys', []) if key in lf_runtime_services_retrieval_planner_DATASET_REGISTRY]
    return {'is_sufficient': bool(parsed.get('is_sufficient', True)), 'missing_dataset_keys': missing_dataset_keys, 'reason': str(parsed.get('reason', '')).strip()}

def lf_runtime_services_retrieval_planner_build_missing_date_message(retrieval_keys: lf_runtime_services_retrieval_planner_List[str]) -> str:
    """날짜가 빠졌을 때 사용자에게 보여줄 안내 문구를 만든다."""
    labels = lf_runtime_services_retrieval_planner_get_dataset_labels_for_message([key for key in retrieval_keys if lf_runtime_services_retrieval_planner_dataset_requires_date(key)])
    if labels:
        return f"이 질문은 날짜 기준이 필요한 조회입니다 ({', '.join(labels)}). 예를 들어 오늘, 어제, 20260324 처럼 날짜를 함께 적어 주세요."
    return '조회에 필요한 날짜 조건이 없어 실행할 수 없습니다.'

def lf_runtime_services_retrieval_planner_extract_date_slices(user_input: str, default_date: str | None) -> lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, str]]:
    """질문 속 날짜 표현을 retrieval job 단위로 분해한다."""
    normalized = lf_runtime_services_retrieval_planner_normalize_text(user_input)
    slices: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, str]] = []
    now = lf_runtime_services_retrieval_planner_datetime.now()
    if '어제' in normalized or 'yesterday' in normalized:
        slices.append({'label': '어제', 'date': (now - lf_runtime_services_retrieval_planner_timedelta(days=1)).strftime('%Y%m%d')})
    if '오늘' in normalized or 'today' in normalized:
        slices.append({'label': '오늘', 'date': now.strftime('%Y%m%d')})
    import re
    for explicit_date in lf_runtime_services_retrieval_planner_re.findall('\\b(20\\d{6})\\b', str(user_input or '')):
        if explicit_date not in {item['date'] for item in slices}:
            slices.append({'label': explicit_date, 'date': explicit_date})
    if not slices and default_date:
        slices.append({'label': default_date, 'date': default_date})
    return slices

def lf_runtime_services_retrieval_planner_build_retrieval_jobs(user_input: str, extracted_params: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any], retrieval_keys: lf_runtime_services_retrieval_planner_List[str]) -> lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]]:
    """조회 계획을 실제 실행 가능한 job 목록으로 바꾼다."""
    jobs: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]] = []
    date_slices = lf_runtime_services_retrieval_planner_extract_date_slices(user_input, extracted_params.get('date'))
    use_repeated_date_slices = len(retrieval_keys) == 1 and len(date_slices) > 1
    for dataset_key in retrieval_keys:
        if use_repeated_date_slices:
            for date_slice in date_slices:
                job_params = dict(extracted_params)
                job_params['date'] = date_slice['date']
                jobs.append({'dataset_key': dataset_key, 'params': job_params, 'result_label': date_slice['label']})
            continue
        job_params = dict(extracted_params)
        if len(date_slices) == 1:
            job_params['date'] = date_slices[0]['date']
        jobs.append({'dataset_key': dataset_key, 'params': job_params, 'result_label': None})
    return jobs

def lf_runtime_services_retrieval_planner__build_retrieval_cache_key(dataset_key: str, params: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any], result_label: str | None) -> str:
    """같은 dataset/필터 조합을 캐시에서 재사용할 수 있게 고유 key를 만든다."""
    normalized_params = lf_runtime_services_retrieval_planner_json.dumps(params or {}, ensure_ascii=False, sort_keys=True)
    return f"{dataset_key}|{result_label or ''}|{normalized_params}"

def lf_runtime_services_retrieval_planner__clone_cached_result(result: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """캐시 객체를 그대로 돌려주지 않도록 깊은 복사본을 만든다."""
    return lf_runtime_services_retrieval_planner_copy.deepcopy(result)

def lf_runtime_services_retrieval_planner__execute_single_retrieval_job(job: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any], repeated_dataset_keys: bool, index: int) -> lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]:
    """job 하나를 실행하고 source tag, cache metadata까지 정리한다."""
    cache_key = lf_runtime_services_retrieval_planner__build_retrieval_cache_key(job['dataset_key'], job['params'], job.get('result_label'))
    cached_result = lf_runtime_services_retrieval_planner_RETRIEVAL_RESULT_CACHE.get(cache_key)
    if cached_result is not None:
        result = lf_runtime_services_retrieval_planner__clone_cached_result(cached_result)
        result['from_cache'] = True
        return result
    result = lf_runtime_services_retrieval_planner_execute_retrieval_tools([job['dataset_key']], job['params'])[0]
    result_label = job.get('result_label')
    if result_label:
        result['result_label'] = result_label
    if repeated_dataset_keys and result_label:
        result['dataset_key'] = f"{job['dataset_key']}__{result_label}"
        dataset_label = str(result.get('dataset_label', job['dataset_key']))
        result['dataset_label'] = f'{dataset_label} ({result_label})'
    normalized = lf_runtime_services_retrieval_planner_re.sub('\\W+', '_', str(result.get('result_label') or result.get('dataset_label') or result.get('tool_name', ''))).strip('_')
    result['source_tag'] = normalized or f'source_{index}'
    result['from_cache'] = False
    lf_runtime_services_retrieval_planner_RETRIEVAL_RESULT_CACHE[cache_key] = lf_runtime_services_retrieval_planner__clone_cached_result(result)
    return result

def lf_runtime_services_retrieval_planner_execute_retrieval_jobs(jobs: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]]) -> lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]]:
    """job 목록을 실제 retrieval 함수 실행 결과로 바꾼다."""
    if not jobs:
        return []
    repeated_dataset_keys = len({job['dataset_key'] for job in jobs}) != len(jobs)
    if len(jobs) == 1:
        return [lf_runtime_services_retrieval_planner__execute_single_retrieval_job(jobs[0], repeated_dataset_keys, 1)]
    indexed_results: lf_runtime_services_retrieval_planner_List[tuple[int, lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]]] = []
    with lf_runtime_services_retrieval_planner_ThreadPoolExecutor(max_workers=min(4, len(jobs))) as executor:
        futures = {executor.submit(lf_runtime_services_retrieval_planner__execute_single_retrieval_job, job, repeated_dataset_keys, index): index for index, job in enumerate(jobs, start=1)}
        for future, index in futures.items():
            indexed_results.append((index, future.result()))
    indexed_results.sort(key=lambda item: item[0])
    return [result for _index, result in indexed_results]

def lf_runtime_services_retrieval_planner_should_retry_retrieval_plan(retrieval_plan: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any] | None, source_results: lf_runtime_services_retrieval_planner_List[lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]], analysis_result: lf_runtime_services_retrieval_planner_Dict[str, lf_runtime_services_retrieval_planner_Any]) -> bool:
    """초기 조회 계획이 부족해 다시 planning 해야 하는지 판단한다."""
    if not retrieval_plan or not retrieval_plan.get('needs_post_processing'):
        return False
    if len(source_results) != 1:
        return False
    analysis_logic = str(analysis_result.get('analysis_logic', '')).strip()
    if analysis_logic == 'minimal_fallback':
        return True
    if not analysis_result.get('success') and analysis_result.get('missing_columns'):
        return True
    return False

# ---- node component ----
import sys
from pathlib import Path

Component = lf_component_base_Component
DataInput = lf_component_base_DataInput
Output = lf_component_base_Output
make_data = lf_component_base_make_data
read_state_payload = lf_component_base_read_state_payload
activate_domain_context_from_state = lf_node_utils_activate_domain_context_from_state
pick_retrieval_tools = lf_runtime_data_retrieval_pick_retrieval_tools
plan_retrieval_request = lf_runtime_services_retrieval_planner_plan_retrieval_request


class PlanDatasetsComponent(Component):
    display_name = "Plan Datasets"
    description = "Select which manufacturing datasets are needed for the current question."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "TableProperties"
    name = "plan_datasets"

    inputs = [DataInput(name="state", display_name="State", info="State after query mode has been decided")]
    outputs = [Output(name="state_out", display_name="State", method="plan_datasets", types=["Data"], selected="Data")]

    def plan_datasets(self):
        state = read_state_payload(getattr(self, "state", None))
        if not state:
            self.status = "No input state; skipped"
            return None

        activate_domain_context_from_state(state)
        retrieval_plan = plan_retrieval_request(
            state.get("user_input", ""),
            state.get("chat_history", []),
            state.get("current_data"),
        )
        retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(state.get("user_input", ""))
        updated_state = {**state, "retrieval_plan": retrieval_plan, "retrieval_keys": retrieval_keys}
        self.status = f"Planned {len(retrieval_keys)} dataset key(s)"
        return make_data({"state": updated_state})
