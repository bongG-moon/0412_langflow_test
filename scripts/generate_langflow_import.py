from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = ROOT / "langflow_custom_component"
OUTPUT_PATH = COMPONENT_DIR / "manufacturing_langflow_import.json"
RUNTIME_PACKAGE = "manufacturing_langflow_runtime"
VISIBLE_STANDALONE_MARKER = "# VISIBLE_STANDALONE_RUNTIME"
STARTER_URL = (
    "https://raw.githubusercontent.com/langflow-ai/langflow/main/"
    "src/backend/base/langflow/initial_setup/starter_projects/Basic%20Prompting.json"
)
LANGFLOW_VERSION = "1.7.0"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NODE_MODULES = [
    "domain_rules",
    "domain_registry",
    "session_memory",
    "extract_params",
    "decide_mode",
    "route_mode",
    "run_followup",
    "plan_datasets",
    "build_jobs",
    "route_plan",
    "exec_jobs",
    "route_single",
    "route_multi",
    "build_single",
    "analyze_single",
    "build_multi",
    "analyze_multi",
    "merge_final",
]

INSTANCE_SPECS = [
    {"key": "domain_rules", "module": "domain_rules", "label": "Domain Rules", "x": 80, "y": 60},
    {"key": "domain_registry", "module": "domain_registry", "label": "Domain Registry", "x": 80, "y": 350},
    {"key": "chat_input", "module": None, "label": "Chat Input", "x": 80, "y": 680},
    {"key": "session_load", "module": "session_memory", "label": "Session Memory", "x": 430, "y": 470},
    {"key": "extract_params", "module": "extract_params", "label": "Extract Params", "x": 430, "y": 760},
    {"key": "decide_mode", "module": "decide_mode", "label": "Decide Mode", "x": 780, "y": 760},
    {"key": "route_mode", "module": "route_mode", "label": "Route Mode", "x": 1130, "y": 760},
    {"key": "run_followup", "module": "run_followup", "label": "Run Followup", "x": 1480, "y": 180},
    {"key": "plan_datasets", "module": "plan_datasets", "label": "Plan Datasets", "x": 1480, "y": 560},
    {"key": "build_jobs", "module": "build_jobs", "label": "Build Jobs", "x": 1480, "y": 860},
    {"key": "route_plan", "module": "route_plan", "label": "Route Plan", "x": 1480, "y": 1140},
    {"key": "exec_jobs_single", "module": "exec_jobs", "label": "Execute Jobs", "x": 1830, "y": 940},
    {"key": "route_single", "module": "route_single", "label": "Route Single", "x": 2180, "y": 940},
    {"key": "build_single", "module": "build_single", "label": "Build Single", "x": 2530, "y": 820},
    {"key": "analyze_single", "module": "analyze_single", "label": "Analyze Single", "x": 2530, "y": 1080},
    {"key": "exec_jobs_multi", "module": "exec_jobs", "label": "Execute Jobs", "x": 1830, "y": 1360},
    {"key": "route_multi", "module": "route_multi", "label": "Route Multi", "x": 2180, "y": 1360},
    {"key": "build_multi", "module": "build_multi", "label": "Build Multi", "x": 2530, "y": 1240},
    {"key": "analyze_multi", "module": "analyze_multi", "label": "Analyze Multi", "x": 2530, "y": 1500},
    {"key": "merge_final", "module": "merge_final", "label": "Merge Result", "x": 2880, "y": 1120},
    {"key": "session_save", "module": "session_memory", "label": "Session Memory", "x": 3230, "y": 1120},
    {"key": "chat_output", "module": None, "label": "Chat Output", "x": 3580, "y": 1120},
]

EDGE_SPECS = [
    ("domain_rules", "rules", "session_load", "domain_rules"),
    ("domain_registry", "registry", "session_load", "domain_registry"),
    ("chat_input", "message", "session_load", "message"),
    ("session_load", "state_out", "extract_params", "state"),
    ("extract_params", "state_out", "decide_mode", "state"),
    ("decide_mode", "state_out", "route_mode", "state"),
    ("route_mode", "followup_out", "run_followup", "state"),
    ("run_followup", "state_out", "merge_final", "followup_result"),
    ("route_mode", "retrieval_out", "plan_datasets", "state"),
    ("plan_datasets", "state_out", "build_jobs", "state"),
    ("build_jobs", "state_out", "route_plan", "state"),
    ("route_plan", "finish_out", "merge_final", "finish_result"),
    ("route_plan", "single_out", "exec_jobs_single", "state"),
    ("exec_jobs_single", "state_out", "route_single", "state"),
    ("route_single", "direct_out", "build_single", "state"),
    ("build_single", "state_out", "merge_final", "single_direct_result"),
    ("route_single", "analysis_out", "analyze_single", "state"),
    ("analyze_single", "state_out", "merge_final", "single_analysis_result"),
    ("route_plan", "multi_out", "exec_jobs_multi", "state"),
    ("exec_jobs_multi", "state_out", "route_multi", "state"),
    ("route_multi", "overview_out", "build_multi", "state"),
    ("build_multi", "state_out", "merge_final", "multi_overview_result"),
    ("route_multi", "analysis_out", "analyze_multi", "state"),
    ("analyze_multi", "state_out", "merge_final", "multi_analysis_result"),
    ("merge_final", "result_out", "session_save", "result"),
    ("domain_rules", "rules", "session_save", "domain_rules"),
    ("domain_registry", "registry", "session_save", "domain_registry"),
    ("chat_input", "message", "session_save", "message"),
    ("session_save", "saved_out", "chat_output", "input_value"),
]

PACKAGE_BLOCK_RE = re.compile(
    r"_PACKAGE_PARENT = Path\(__file__\)\.resolve\(\)\.parent\.parent\n"
    r"if str\(_PACKAGE_PARENT\) not in sys\.path:\n"
    r"    sys\.path\.insert\(0, str\(_PACKAGE_PARENT\)\)\n\n",
    re.MULTILINE,
)

RUNTIME_ORDER = [
    RUNTIME_PACKAGE,
    f"{RUNTIME_PACKAGE}.component_base",
    f"{RUNTIME_PACKAGE}.llm_settings",
    f"{RUNTIME_PACKAGE}.workflow",
    f"{RUNTIME_PACKAGE}._runtime",
    f"{RUNTIME_PACKAGE}._runtime.shared",
    f"{RUNTIME_PACKAGE}._runtime.shared.filter_utils",
    f"{RUNTIME_PACKAGE}._runtime.domain",
    f"{RUNTIME_PACKAGE}._runtime.domain.knowledge",
    f"{RUNTIME_PACKAGE}._runtime.shared.column_resolver",
    f"{RUNTIME_PACKAGE}._runtime.shared.number_format",
    f"{RUNTIME_PACKAGE}._runtime.shared.text_sanitizer",
    f"{RUNTIME_PACKAGE}._runtime.shared.config",
    f"{RUNTIME_PACKAGE}._runtime.domain.registry",
    f"{RUNTIME_PACKAGE}._runtime.graph",
    f"{RUNTIME_PACKAGE}._runtime.graph.state",
    f"{RUNTIME_PACKAGE}._runtime.graph.builder",
    f"{RUNTIME_PACKAGE}._runtime.analysis",
    f"{RUNTIME_PACKAGE}._runtime.analysis.contracts",
    f"{RUNTIME_PACKAGE}._runtime.analysis.helpers",
    f"{RUNTIME_PACKAGE}._runtime.analysis.safe_executor",
    f"{RUNTIME_PACKAGE}._runtime.analysis.llm_planner",
    f"{RUNTIME_PACKAGE}._runtime.analysis.engine",
    f"{RUNTIME_PACKAGE}._runtime.data.retrieval",
    f"{RUNTIME_PACKAGE}.node_utils",
    f"{RUNTIME_PACKAGE}._runtime.services",
    f"{RUNTIME_PACKAGE}._runtime.services.request_context",
    f"{RUNTIME_PACKAGE}._runtime.services.merge_service",
    f"{RUNTIME_PACKAGE}._runtime.services.parameter_service",
    f"{RUNTIME_PACKAGE}._runtime.services.query_mode",
    f"{RUNTIME_PACKAGE}._runtime.services.retrieval_planner",
    f"{RUNTIME_PACKAGE}._runtime.services.response_service",
    f"{RUNTIME_PACKAGE}._runtime.services.runtime_service",
]

PACKAGE_NAMES = [
    RUNTIME_PACKAGE,
    f"{RUNTIME_PACKAGE}._runtime",
    f"{RUNTIME_PACKAGE}._runtime.analysis",
    f"{RUNTIME_PACKAGE}._runtime.data",
    f"{RUNTIME_PACKAGE}._runtime.domain",
    f"{RUNTIME_PACKAGE}._runtime.graph",
    f"{RUNTIME_PACKAGE}._runtime.services",
    f"{RUNTIME_PACKAGE}._runtime.shared",
]


def _starter_chat_nodes() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with urlopen(STARTER_URL, timeout=30) as response:
        starter = json.load(response)
    chat_input = None
    chat_output = None
    for node in starter["data"]["nodes"]:
        data = node.get("data", {})
        display_name = data.get("display_name") or data.get("node", {}).get("display_name")
        if display_name == "Chat Input":
            chat_input = node
        elif display_name == "Chat Output":
            chat_output = node
    if not chat_input or not chat_output:
        raise RuntimeError("Could not find Chat Input / Chat Output in official starter flow.")
    return chat_input, chat_output


def _sanitize_source(source: str) -> str:
    source = source.lstrip("\ufeff")
    source = re.sub(r"^from __future__ import annotations\s*\n", "", source, count=1)
    source = PACKAGE_BLOCK_RE.sub("", source)
    source = source.replace("langflow_custom_component", RUNTIME_PACKAGE)
    return source.lstrip("\n")


def _runtime_sources() -> Dict[str, str]:
    sources: Dict[str, str] = {}
    for path in sorted(COMPONENT_DIR.rglob("*.py")):
        relative = path.relative_to(COMPONENT_DIR)
        module_name = _module_name_from_path(relative)
        if relative.parts and relative.parts[0] != "_runtime" and relative.stem in NODE_MODULES:
            continue
        sources[module_name] = _sanitize_source(path.read_text(encoding="utf-8"))
    return sources


def _module_name_from_path(relative: Path) -> str:
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = relative.stem
    if not parts:
        return RUNTIME_PACKAGE
    return ".".join([RUNTIME_PACKAGE, *parts])


def _bootstrap_prefix(runtime_sources: Dict[str, str]) -> str:
    return (
        "from __future__ import annotations\n\n"
        "import sys\n"
        "import types\n\n"
        f"_RUNTIME_PACKAGE = {RUNTIME_PACKAGE!r}\n"
        f"_PACKAGE_NAMES = {PACKAGE_NAMES!r}\n"
        f"_RUNTIME_ORDER = {RUNTIME_ORDER!r}\n"
        f"_RUNTIME_SOURCES = {runtime_sources!r}\n\n"
        "def _ensure_package(name: str):\n"
        "    module = sys.modules.get(name)\n"
        "    if module is None:\n"
        "        module = types.ModuleType(name)\n"
        "        module.__package__ = name\n"
        "        module.__path__ = []\n"
        "        module.__file__ = f'<{name}>'\n"
        "        sys.modules[name] = module\n"
        "    parent_name, _, child_name = name.rpartition('.')\n"
        "    if parent_name:\n"
        "        parent = _ensure_package(parent_name)\n"
        "        setattr(parent, child_name, module)\n"
        "    return module\n\n"
        "def _ensure_module(name: str):\n"
        "    module = sys.modules.get(name)\n"
        "    if module is None:\n"
        "        parent_name, _, child_name = name.rpartition('.')\n"
        "        if parent_name:\n"
        "            parent = _ensure_package(parent_name)\n"
        "        else:\n"
        "            parent = None\n"
        "        module = types.ModuleType(name)\n"
        "        module.__package__ = parent_name\n"
        "        module.__file__ = f'<{name}>'\n"
        "        sys.modules[name] = module\n"
        "        if parent is not None:\n"
        "            setattr(parent, child_name, module)\n"
        "    return module\n\n"
        "def _runtime_is_complete():\n"
        "    root = sys.modules.get(_RUNTIME_PACKAGE)\n"
        "    if root is None or not getattr(root, '__embedded_bootstrap_loaded__', False):\n"
        "        return False\n"
        "    for module_name in _RUNTIME_ORDER:\n"
        "        if _RUNTIME_SOURCES.get(module_name, '') and module_name not in sys.modules:\n"
        "            return False\n"
        "    return True\n\n"
        "def _bootstrap_runtime():\n"
        "    if _runtime_is_complete():\n"
        "        return sys.modules[_RUNTIME_PACKAGE]\n"
        "    for package_name in _PACKAGE_NAMES:\n"
        "        _ensure_package(package_name)\n"
        "    for module_name in _RUNTIME_ORDER:\n"
        "        source = _RUNTIME_SOURCES.get(module_name, '')\n"
        "        module = _ensure_package(module_name) if module_name in _PACKAGE_NAMES else _ensure_module(module_name)\n"
        "        if source and not module.__dict__.get('__embedded_bootstrap_loaded__', False):\n"
        "            module.__dict__.setdefault('__builtins__', __builtins__)\n"
        "            exec(source, module.__dict__)\n"
        "            module.__dict__['__embedded_bootstrap_loaded__'] = True\n"
        "    sys.modules[_RUNTIME_PACKAGE].__embedded_bootstrap_loaded__ = True\n"
        "    return sys.modules[_RUNTIME_PACKAGE]\n\n"
        "def _require_runtime_module(name: str):\n"
        "    _bootstrap_runtime()\n"
        "    module = sys.modules.get(name)\n"
        "    if module is not None:\n"
        "        return module\n"
        "    source = _RUNTIME_SOURCES.get(name, '')\n"
        "    if source:\n"
        "        module = _ensure_package(name) if name in _PACKAGE_NAMES else _ensure_module(name)\n"
        "        if not module.__dict__.get('__embedded_bootstrap_loaded__', False):\n"
        "            module.__dict__.setdefault('__builtins__', __builtins__)\n"
        "            exec(source, module.__dict__)\n"
        "            module.__dict__['__embedded_bootstrap_loaded__'] = True\n"
        "        sys.modules[_RUNTIME_PACKAGE].__embedded_bootstrap_loaded__ = True\n"
        "        return module\n"
        "    raise RuntimeError(f'Embedded runtime module is missing: {name}')\n\n"
        "_bootstrap_runtime()\n"
    )


def _is_standalone_node_source(source: str) -> bool:
    return VISIBLE_STANDALONE_MARKER in source or ("_bootstrap_runtime()" in source and RUNTIME_PACKAGE in source)


def _compose_node_code(module_name: str, runtime_sources: Dict[str, str]) -> str:
    raw_source = (COMPONENT_DIR / f"{module_name}.py").read_text(encoding="utf-8")
    if _is_standalone_node_source(raw_source):
        return raw_source
    component_source = _sanitize_source(raw_source)
    return _bootstrap_prefix(runtime_sources) + "\n" + component_source


def _component_class(module_name: str):
    module = importlib.import_module(f"langflow_custom_component.{module_name}")
    classes = []
    for name in dir(module):
        if name.startswith("__lf_"):
            continue
        obj = getattr(module, name)
        if (
            inspect.isclass(obj)
            and getattr(obj, "__module__", "") == module.__name__
            and bool(str(getattr(obj, "display_name", "")).strip())
        ):
            classes.append(obj)
    if not classes:
        raise RuntimeError(f"No component class found in {module_name}.")
    return classes[0]


def _code_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _component_type(component_cls) -> str:
    return str(getattr(component_cls, "name", "") or component_cls.__name__).strip()


def _make_node_id(base: str, key: str) -> str:
    token = hashlib.sha1(f"{base}:{key}".encode("utf-8")).hexdigest()[:5]
    return f"{base}-{token}"


def _input_kind(module_name: str, input_name: str) -> str:
    if input_name == "llm_api_key":
        return "secret"
    if input_name in {"llm_fast_model", "llm_strong_model"}:
        return "text"
    if module_name == "domain_rules" and input_name == "domain_rules_text":
        return "multiline"
    if module_name == "domain_registry" and input_name == "registry_json":
        return "multiline"
    if module_name == "session_memory" and input_name == "message":
        return "message"
    if module_name == "session_memory" and input_name in {"domain_rules", "domain_registry", "result"}:
        return "data"
    if module_name == "session_memory" and input_name in {"session_id_override", "storage_subdir"}:
        return "text"
    return "data"


def _default_value(module_name: str, input_name: str, raw_value: Any) -> Any:
    if raw_value not in (None, ""):
        return raw_value
    if module_name == "domain_rules" and input_name == "domain_rules_text":
        return "예: HBM/3DS는 TSV 제품으로 간주하고, AUTO 제품 별칭을 추가합니다."
    if module_name == "domain_registry" and input_name == "registry_json":
        return '{\n  "entries": []\n}'
    return ""


def _template_field(module_name: str, input_obj) -> Dict[str, Any]:
    input_name = str(getattr(input_obj, "name", ""))
    input_kind = _input_kind(module_name, input_name)
    info = str(getattr(input_obj, "info", "") or "")
    display_name = str(getattr(input_obj, "display_name", input_name) or input_name)
    value = _default_value(module_name, input_name, getattr(input_obj, "value", ""))
    advanced = bool(getattr(input_obj, "advanced", False))

    base = {
        "advanced": advanced,
        "display_name": display_name,
        "dynamic": False,
        "info": info,
        "list": False,
        "load_from_db": False,
        "name": input_name,
        "placeholder": "",
        "required": False,
        "show": True,
        "title_case": False,
        "trace_as_input": True,
        "trace_as_metadata": True,
        "value": value,
    }

    if input_kind == "data":
        return {
            **base,
            "_input_type": "HandleInput",
            "input_types": ["Data"],
            "type": "other",
            "tool_mode": False,
        }
    if input_kind == "message":
        return {
            **base,
            "_input_type": "HandleInput",
            "input_types": ["Message"],
            "type": "str",
            "tool_mode": False,
        }
    if input_kind == "multiline":
        return {
            **base,
            "_input_type": "MultilineInput",
            "input_types": [],
            "multiline": True,
            "type": "str",
        }
    if input_kind == "secret":
        return {
            **base,
            "_input_type": "SecretStrInput",
            "input_types": [],
            "password": True,
            "type": "str",
        }
    return {
        **base,
        "_input_type": "MessageTextInput",
        "input_types": [],
        "type": "str",
    }


def _code_template(code: str) -> Dict[str, Any]:
    return {
        "advanced": True,
        "dynamic": True,
        "fileTypes": [],
        "file_path": "",
        "info": "",
        "list": False,
        "load_from_db": False,
        "multiline": True,
        "name": "code",
        "password": False,
        "placeholder": "",
        "required": True,
        "show": True,
        "title_case": False,
        "type": "code",
        "value": code,
    }


def _output_payload(output_obj) -> Dict[str, Any]:
    types = list(getattr(output_obj, "types", None) or ["Data"])
    return {
        "allows_loop": False,
        "cache": True,
        "display_name": str(getattr(output_obj, "display_name", getattr(output_obj, "name", "Output"))),
        "group_outputs": bool(getattr(output_obj, "group_outputs", False)),
        "method": str(getattr(output_obj, "method", "")),
        "name": str(getattr(output_obj, "name", "")),
        "selected": str(getattr(output_obj, "selected", types[0])),
        "tool_mode": True,
        "types": types,
        "value": "__UNDEFINED__",
    }


def _build_custom_node(instance_spec: Dict[str, Any], runtime_sources: Dict[str, str]) -> Dict[str, Any]:
    module_name = instance_spec["module"]
    component_cls = _component_class(module_name)
    node_code = _compose_node_code(module_name, runtime_sources)
    node_id = _make_node_id(_component_type(component_cls), instance_spec["key"])
    outputs = [_output_payload(item) for item in getattr(component_cls, "outputs", [])]
    template = {"_type": "Component", "code": _code_template(node_code)}
    field_order: List[str] = []
    for input_obj in getattr(component_cls, "inputs", []):
        template[str(getattr(input_obj, "name"))] = _template_field(module_name, input_obj)
        field_order.append(str(getattr(input_obj, "name")))

    height = max(220, 150 + 56 * (len(field_order) + max(len(outputs), 1)))
    width = 360
    return {
        "data": {
            "description": str(getattr(component_cls, "description", "")),
            "display_name": str(getattr(component_cls, "display_name", instance_spec["label"])),
            "id": node_id,
            "node": {
                "base_classes": ["Data"],
                "beta": False,
                "conditional_paths": [],
                "custom_fields": {},
                "description": str(getattr(component_cls, "description", "")),
                "display_name": str(getattr(component_cls, "display_name", instance_spec["label"])),
                "documentation": str(getattr(component_cls, "documentation", "")),
                "edited": True,
                "field_order": field_order,
                "frozen": False,
                "icon": str(getattr(component_cls, "icon", "Component")),
                "legacy": False,
                "lf_version": LANGFLOW_VERSION,
                "metadata": {
                    "code_hash": _code_hash(node_code),
                    "dependencies": {"dependencies": [], "total_dependencies": 0},
                    "module": f"embedded.{module_name}",
                },
                "name": _component_type(component_cls),
                "output_types": [],
                "outputs": outputs,
                "pinned": False,
                "template": template,
            },
            "selected_output": outputs[0]["name"] if outputs else "",
            "type": _component_type(component_cls),
        },
        "dragging": False,
        "height": height,
        "id": node_id,
        "measured": {"height": height, "width": width},
        "position": {"x": instance_spec["x"], "y": instance_spec["y"]},
        "positionAbsolute": {"x": instance_spec["x"], "y": instance_spec["y"]},
        "selected": False,
        "type": "genericNode",
        "width": width,
    }


def _build_chat_node(base_node: Dict[str, Any], instance_spec: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    node = json.loads(json.dumps(base_node))
    node["id"] = node_id
    node["data"]["id"] = node_id
    node["data"]["node"]["template"]["input_value"]["value"] = ""
    node["position"] = {"x": instance_spec["x"], "y": instance_spec["y"]}
    node["positionAbsolute"] = {"x": instance_spec["x"], "y": instance_spec["y"]}
    return node


def _build_instance_nodes() -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    chat_input_base, chat_output_base = _starter_chat_nodes()
    runtime_sources = _runtime_sources()
    nodes: List[Dict[str, Any]] = []
    by_key: Dict[str, Dict[str, Any]] = {}
    for instance_spec in INSTANCE_SPECS:
        if instance_spec["key"] == "chat_input":
            node_id = _make_node_id("ChatInput", instance_spec["key"])
            node = _build_chat_node(chat_input_base, instance_spec, node_id)
        elif instance_spec["key"] == "chat_output":
            node_id = _make_node_id("ChatOutput", instance_spec["key"])
            node = _build_chat_node(chat_output_base, instance_spec, node_id)
        else:
            node = _build_custom_node(instance_spec, runtime_sources)
        nodes.append(node)
        by_key[instance_spec["key"]] = node
    return nodes, by_key


def _handle_string(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(", ", ": ")).replace('"', "ŠŤ")


def _target_input_types(target_node: Dict[str, Any], field_name: str) -> Tuple[List[str], str]:
    template = target_node["data"]["node"]["template"][field_name]
    input_types = list(template.get("input_types", []))
    input_type = str(template.get("type", "str"))
    return input_types, input_type


def _source_output_types(source_node: Dict[str, Any], output_name: str) -> List[str]:
    for output in source_node["data"]["node"]["outputs"]:
        if output["name"] == output_name:
            return list(output.get("types", []))
    return ["Data"]


def _build_edge(
    source_key: str,
    source_output: str,
    target_key: str,
    target_input: str,
    node_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    source_node = node_map[source_key]
    target_node = node_map[target_key]
    source_payload = {
        "dataType": source_node["data"]["type"],
        "id": source_node["id"],
        "name": source_output,
        "output_types": _source_output_types(source_node, source_output),
    }
    input_types, input_type = _target_input_types(target_node, target_input)
    target_payload = {
        "fieldName": target_input,
        "id": target_node["id"],
        "inputTypes": input_types,
        "type": input_type,
    }
    source_handle = _handle_string(source_payload)
    target_handle = _handle_string(target_payload)
    return {
        "animated": False,
        "className": "",
        "data": {
            "sourceHandle": source_payload,
            "targetHandle": target_payload,
        },
        "id": f"reactflow__edge-{source_node['id']}{source_handle}-{target_node['id']}{target_handle}",
        "selected": False,
        "source": source_node["id"],
        "sourceHandle": source_handle,
        "target": target_node["id"],
        "targetHandle": target_handle,
    }


def _build_flow() -> Dict[str, Any]:
    nodes, node_map = _build_instance_nodes()
    edges = [_build_edge(*edge_spec, node_map=node_map) for edge_spec in EDGE_SPECS]
    return {
        "data": {
            "nodes": nodes,
            "edges": edges,
            "viewport": {"x": -28.0, "y": -38.0, "zoom": 0.58},
        },
        "description": "Branch-visible manufacturing agent flow with embedded standalone custom-component code.",
        "endpoint_name": None,
        "id": str(uuid.uuid4()),
        "is_component": False,
        "last_tested_version": LANGFLOW_VERSION,
        "name": "Manufacturing Agent (Custom Components)",
        "tags": ["manufacturing", "langflow", "custom-components"],
    }


def main() -> None:
    flow = _build_flow()
    OUTPUT_PATH.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
