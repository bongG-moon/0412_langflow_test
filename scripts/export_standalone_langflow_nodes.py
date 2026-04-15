from __future__ import annotations

import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_langflow_import import COMPONENT_DIR, NODE_MODULES, RUNTIME_PACKAGE, _bootstrap_prefix, _runtime_sources


OUTPUT_DIR = COMPONENT_DIR / "paste_ready"
IMPORT_MARKER = f"from {RUNTIME_PACKAGE}.component_base import"
BINDING_PATTERN = rf"(=\s*)sys\.modules\[(?P<quote>['\"])(?P<module>{RUNTIME_PACKAGE}[^'\"]*)(?P=quote)\]"


def _extract_node_logic(module_name: str) -> str:
    text = (COMPONENT_DIR / f"{module_name}.py").read_text(encoding="utf-8")

    if "_bootstrap_runtime()" in text:
        return text.rsplit("_bootstrap_runtime()", 1)[-1].lstrip()

    marker_index = text.find(IMPORT_MARKER)
    if marker_index == -1:
        raise RuntimeError(f"Could not find standalone import marker in {module_name}.py")

    import_block_start = text.rfind("\nimport ", 0, marker_index)
    if import_block_start == -1:
        import_block_start = text.rfind("\nfrom ", 0, marker_index)
    if import_block_start == -1:
        import_block_start = marker_index
    else:
        import_block_start += 1

    return text[import_block_start:].lstrip()


def _replace_runtime_imports_with_bindings(source: str) -> str:
    """Replace runtime package imports with direct sys.modules bindings.

    Langflow Desktop validates custom-component code before it executes the
    file body. If a node still contains `from manufacturing_langflow_runtime`
    imports, validation can fail before the embedded bootstrap has a chance to
    register that package in `sys.modules`.

    To keep each node truly standalone, we rewrite those imports into plain
    assignments that read already-bootstrapped modules from `sys.modules`.
    """

    tree = ast.parse(source)
    lines = source.splitlines()
    replacements: list[tuple[int, int, str]] = []
    binding_index = 0

    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module or not node.module.startswith(RUNTIME_PACKAGE):
            continue

        binding_index += 1
        binding_name = f"__runtime_module_{binding_index}"
        replacement_lines = [f"{binding_name} = _require_runtime_module({node.module!r})"]
        for alias in node.names:
            target_name = alias.asname or alias.name
            replacement_lines.append(f"{target_name} = {binding_name}.{alias.name}")
        replacements.append((node.lineno, node.end_lineno or node.lineno, "\n".join(replacement_lines)))

    if replacements:
        rebuilt_lines: list[str] = []
        current_line = 1
        for start_line, end_line, replacement_text in replacements:
            rebuilt_lines.extend(lines[current_line - 1 : start_line - 1])
            rebuilt_lines.append(replacement_text)
            current_line = end_line + 1
        rebuilt_lines.extend(lines[current_line - 1 :])
        source = "\n".join(rebuilt_lines).lstrip()

    source = re.sub(
        BINDING_PATTERN,
        lambda match: f"{match.group(1)}_require_runtime_module({match.group('quote')}{match.group('module')}{match.group('quote')})",
        source,
    )
    return source.lstrip()


def _build_standalone_node_source(module_name: str, runtime_sources: dict[str, str]) -> str:
    logic_source = _extract_node_logic(module_name)
    standalone_logic = _replace_runtime_imports_with_bindings(logic_source)
    return _bootstrap_prefix(runtime_sources) + "\n" + standalone_logic


def _readme_text() -> str:
    lines = [
        "# Paste-Ready Langflow Nodes",
        "",
        "이 폴더의 `.py` 파일은 Langflow Desktop의 custom component 코드 편집기에",
        "그대로 붙여넣을 수 있도록 standalone 형태로 생성한 버전입니다.",
        "",
        "주의:",
        "- 현재 `langflow_custom_component/*.py` 자체가 standalone 정본입니다.",
        "- 이 폴더는 그 정본을 다시 모아둔 mirror 입니다.",
        "- 파일이 크기 때문에 저장 후 Langflow가 다시 로드하는 데 시간이 조금 걸릴 수 있습니다.",
        "- `LLM_API_KEY` 같은 환경변수는 Langflow Desktop 실행 환경에 따로 넣어야 합니다.",
        "",
        "생성 스크립트:",
        "- `python scripts/export_standalone_langflow_nodes.py`",
        "",
        "대상 노드:",
    ]
    for module_name in NODE_MODULES:
        lines.append(f"- `{module_name}.py`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    runtime_sources = _runtime_sources()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for module_name in NODE_MODULES:
        source = _build_standalone_node_source(module_name, runtime_sources)
        root_path = COMPONENT_DIR / f"{module_name}.py"
        mirror_path = OUTPUT_DIR / f"{module_name}.py"
        root_path.write_text(source, encoding="utf-8")
        mirror_path.write_text(source, encoding="utf-8")
        print(f"Wrote {root_path}")
        print(f"Wrote {mirror_path}")

    (OUTPUT_DIR / "README.md").write_text(_readme_text(), encoding="utf-8")
    print(f"Wrote {OUTPUT_DIR / 'README.md'}")


if __name__ == "__main__":
    main()
