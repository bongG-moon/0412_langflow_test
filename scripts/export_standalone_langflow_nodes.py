from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Set


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_langflow_import import (  # noqa: E402
    COMPONENT_DIR,
    NODE_MODULES,
    PACKAGE_NAMES,
    RUNTIME_ORDER,
    RUNTIME_PACKAGE,
    _runtime_sources,
)


OUTPUT_DIR = COMPONENT_DIR / "paste_ready"
VISIBLE_STANDALONE_MARKER = "# VISIBLE_STANDALONE_RUNTIME"
RUNTIME_BINDING_RE = re.compile(
    rf"^(?P<var>__runtime_module_\d+)\s*=\s*_require_runtime_module\((?P<quote>['\"])(?P<module>{re.escape(RUNTIME_PACKAGE)}[^'\"]*)(?P=quote)\)\s*$"
)
RUNTIME_ATTR_RE = re.compile(r"^(?P<target>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<var>__runtime_module_\d+)\.(?P<attr>[A-Za-z_][A-Za-z0-9_]*)\s*$")


def _prefix_for_module(module_name: str) -> str:
    relative_name = module_name.removeprefix(RUNTIME_PACKAGE).strip(".") or "root"
    safe_name = re.sub(r"[^0-9A-Za-z_]", "_", relative_name).strip("_")
    return f"lf_{safe_name}_"


def _legacy_prefix_for_module(module_name: str) -> str:
    relative_name = module_name.removeprefix(RUNTIME_PACKAGE).strip(".") or "root"
    safe_name = re.sub(r"[^0-9A-Za-z_]", "_", relative_name).strip("_")
    return f"__lf_{safe_name}__"


def _prefixed_name(module_name: str, name: str) -> str:
    return f"{_prefix_for_module(module_name)}{name}"


def _external_import_alias(module_name: str, imported_module: str) -> str:
    safe_module = re.sub(r"[^0-9A-Za-z_]", "_", imported_module).strip("_")
    return _prefixed_name(module_name, f"import_{safe_module}")


def _is_internal_module(module_name: str | None, sources: Dict[str, str]) -> bool:
    return bool(module_name and module_name.startswith(RUNTIME_PACKAGE) and module_name in sources)


def _is_package_module(module_name: str) -> bool:
    return module_name in PACKAGE_NAMES


def _resolve_import_module(current_module: str, level: int, imported_module: str | None) -> str | None:
    if level == 0:
        return imported_module

    package_parts = current_module.split(".") if _is_package_module(current_module) else current_module.split(".")[:-1]
    base_parts = package_parts[: max(0, len(package_parts) - (level - 1))]
    if imported_module:
        base_parts.extend(imported_module.split("."))
    return ".".join(base_parts) if base_parts else None


def _iter_bound_names_in_target(target: ast.AST) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for child in target.elts:
            yield from _iter_bound_names_in_target(child)


class _TopLevelBindingCollector(ast.NodeVisitor):
    """Collect module-level names without descending into function/class bodies."""

    def __init__(self) -> None:
        self.names: Set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split(".", 1)[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                continue
            self.names.add(alias.asname or alias.name)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self.names.update(_iter_bound_names_in_target(target))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.names.update(_iter_bound_names_in_target(node.target))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.names.update(_iter_bound_names_in_target(node.target))
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.names.update(_iter_bound_names_in_target(node.target))
        self.generic_visit(node)


def _collect_top_level_bindings(module_name: str, source: str) -> Set[str]:
    tree = ast.parse(source, filename=f"<{module_name}>")
    collector = _TopLevelBindingCollector()
    for statement in tree.body:
        collector.visit(statement)
    return collector.names


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    left = test.left
    right = test.comparators[0]
    return (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )


def _internal_import_dependencies(module_name: str, source: str, sources: Dict[str, str]) -> Set[str]:
    dependencies: Set[str] = set()
    tree = ast.parse(source, filename=f"<{module_name}>")
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        imported_module = _resolve_import_module(module_name, node.level, node.module)
        if _is_internal_module(imported_module, sources):
            dependencies.add(str(imported_module))
    return dependencies


class _VisibleRuntimeTransformer(ast.NodeTransformer):
    def __init__(self, module_name: str, top_level_names: Set[str], sources: Dict[str, str]) -> None:
        self.module_name = module_name
        self.top_level_names = top_level_names
        self.sources = sources
        self.scope_depth = 0

    def _rename_if_module_level_name(self, name: str) -> str:
        if name in self.top_level_names:
            return _prefixed_name(self.module_name, name)
        return name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if self.scope_depth == 0 and node.name in self.top_level_names:
            node.name = _prefixed_name(self.module_name, node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        if self.scope_depth == 0 and node.name in self.top_level_names:
            node.name = _prefixed_name(self.module_name, node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        if self.scope_depth == 0 and node.name in self.top_level_names:
            node.name = _prefixed_name(self.module_name, node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1
        return node

    def visit_Global(self, node: ast.Global) -> ast.AST:
        node.names = [self._rename_if_module_level_name(name) for name in node.names]
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = self._rename_if_module_level_name(node.id)
        return node

    def visit_Import(self, node: ast.Import) -> ast.AST:
        if self.scope_depth != 0:
            return node
        for alias in node.names:
            local_name = alias.asname or alias.name.split(".", 1)[0]
            if local_name in self.top_level_names:
                alias.asname = _prefixed_name(self.module_name, local_name)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST | List[ast.stmt] | None:
        if node.module == "__future__":
            return None

        imported_module = _resolve_import_module(self.module_name, node.level, node.module)
        if not _is_internal_module(imported_module, self.sources):
            if self.scope_depth != 0 or not imported_module:
                return node

            module_alias = _external_import_alias(self.module_name, imported_module)
            replacements: List[ast.stmt] = [
                ast.Import(names=[ast.alias(name=imported_module, asname=module_alias)])
            ]
            for alias in node.names:
                if alias.name == "*":
                    return node
                local_name = alias.asname or alias.name
                target_name = self._rename_if_module_level_name(local_name)
                replacements.append(
                    ast.Assign(
                        targets=[ast.Name(id=target_name, ctx=ast.Store())],
                        value=ast.Attribute(
                            value=ast.Name(id=module_alias, ctx=ast.Load()),
                            attr=alias.name,
                            ctx=ast.Load(),
                        ),
                    )
                )
            return replacements

        replacements: List[ast.stmt] = []
        for alias in node.names:
            if alias.name == "*":
                raise RuntimeError(f"Wildcard internal imports are not supported in {self.module_name}.")
            local_name = alias.asname or alias.name
            target_name = _prefixed_name(self.module_name, local_name) if self.scope_depth == 0 and local_name in self.top_level_names else local_name
            replacements.append(
                ast.Assign(
                    targets=[ast.Name(id=target_name, ctx=ast.Store())],
                    value=ast.Name(id=_prefixed_name(str(imported_module), alias.name), ctx=ast.Load()),
                )
            )
        return replacements


def _flatten_module(module_name: str, source: str, sources: Dict[str, str]) -> str:
    tree = ast.parse(source, filename=f"<{module_name}>")
    tree.body = [statement for statement in tree.body if not _is_main_guard(statement)]
    top_level_names = _collect_top_level_bindings(module_name, source)
    transformer = _VisibleRuntimeTransformer(module_name, top_level_names, sources)
    flattened = transformer.visit(tree)
    ast.fix_missing_locations(flattened)
    rendered = ast.unparse(flattened).strip()
    section = module_name.removeprefix(f"{RUNTIME_PACKAGE}.") or "root"
    return f"# ---- visible runtime: {section} ----\n{rendered}\n"


def _direct_node_dependencies(logic_source: str, sources: Dict[str, str]) -> Set[str]:
    dependencies: Set[str] = set()
    for line in logic_source.splitlines():
        match = RUNTIME_BINDING_RE.match(line.strip())
        if match:
            dependencies.add(match.group("module"))
    for module_name in sources:
        if _prefix_for_module(module_name) in logic_source or _legacy_prefix_for_module(module_name) in logic_source:
            dependencies.add(module_name)
    return dependencies


def _expand_dependencies(direct_dependencies: Iterable[str], sources: Dict[str, str]) -> List[str]:
    needed: Set[str] = set()

    def visit(module_name: str) -> None:
        if module_name in needed or module_name not in sources:
            return
        needed.add(module_name)
        for dependency in _internal_import_dependencies(module_name, sources[module_name], sources):
            visit(dependency)

    for dependency in direct_dependencies:
        visit(dependency)

    ordered = [module_name for module_name in RUNTIME_ORDER if module_name in needed]
    remaining = sorted(module_name for module_name in needed if module_name not in set(ordered))
    return [*ordered, *remaining]


def _extract_node_logic(module_name: str) -> str:
    text = (COMPONENT_DIR / f"{module_name}.py").read_text(encoding="utf-8")

    if "_bootstrap_runtime()" in text:
        return text.rsplit("_bootstrap_runtime()", 1)[-1].lstrip()

    marker_index = text.find(VISIBLE_STANDALONE_MARKER)
    if marker_index != -1:
        node_marker = "\n# ---- node component ----\n"
        if node_marker not in text:
            raise RuntimeError(f"Could not find node component marker in {module_name}.py")
        return text.split(node_marker, 1)[1].lstrip()

    return text.lstrip()


def _replace_node_runtime_bindings(logic_source: str) -> str:
    runtime_vars: Dict[str, str] = {}
    rewritten_lines: List[str] = []
    rewritten_source = logic_source
    for module_name in RUNTIME_ORDER:
        rewritten_source = rewritten_source.replace(_legacy_prefix_for_module(module_name), _prefix_for_module(module_name))

    for line in rewritten_source.splitlines():
        stripped = line.strip()
        binding_match = RUNTIME_BINDING_RE.match(stripped)
        if binding_match:
            runtime_vars[binding_match.group("var")] = binding_match.group("module")
            continue

        attr_match = RUNTIME_ATTR_RE.match(stripped)
        if attr_match and attr_match.group("var") in runtime_vars:
            module_name = runtime_vars[attr_match.group("var")]
            rewritten_lines.append(f"{attr_match.group('target')} = {_prefixed_name(module_name, attr_match.group('attr'))}")
            continue

        rewritten_lines.append(line)

    return "\n".join(rewritten_lines).lstrip()


def _build_visible_standalone_node_source(module_name: str, runtime_sources: Dict[str, str]) -> str:
    logic_source = _extract_node_logic(module_name)
    dependencies = _expand_dependencies(_direct_node_dependencies(logic_source, runtime_sources), runtime_sources)
    flattened_sections = [_flatten_module(dependency, runtime_sources[dependency], runtime_sources) for dependency in dependencies]
    node_logic = _replace_node_runtime_bindings(logic_source)
    return (
        "from __future__ import annotations\n\n"
        f"{VISIBLE_STANDALONE_MARKER}: visible per-node standalone code with no hidden source bundle.\n\n"
        + "\n".join(flattened_sections)
        + "\n# ---- node component ----\n"
        + node_logic
        + "\n"
    )


def _readme_text() -> str:
    lines = [
        "# Paste-Ready Langflow Nodes",
        "",
        "This folder mirrors the root custom-node files in a visible standalone form.",
        "",
        "Key points:",
        "- Each node keeps the Langflow graph shape but contains the Python helpers it needs directly in the file.",
        "- The files avoid hidden string-bundle runtime bootstrapping.",
        "- No local repository package import is required when pasting a node into Langflow Desktop.",
        "- External runtime packages such as pandas, langchain-core, langchain-google-genai, python-dotenv, and typing-extensions still need to exist in the Langflow environment.",
        "",
        "Regenerate with:",
        "- `python scripts/export_standalone_langflow_nodes.py`",
        "",
        "Nodes:",
    ]
    for module_name in NODE_MODULES:
        lines.append(f"- `{module_name}.py`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    runtime_sources = _runtime_sources()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for module_name in NODE_MODULES:
        source = _build_visible_standalone_node_source(module_name, runtime_sources)
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
