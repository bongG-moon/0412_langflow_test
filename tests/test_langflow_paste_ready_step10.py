from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = ROOT / "langflow_custom_component"
PASTE_READY_DIR = ROOT / "langflow_custom_component" / "paste_ready"
NODE_FILES = {
    "domain_rules.py",
    "domain_registry.py",
    "session_memory.py",
    "extract_params.py",
    "decide_mode.py",
    "route_mode.py",
    "run_followup.py",
    "plan_datasets.py",
    "build_jobs.py",
    "route_plan.py",
    "exec_jobs.py",
    "route_single.py",
    "route_multi.py",
    "build_single.py",
    "analyze_single.py",
    "build_multi.py",
    "analyze_multi.py",
    "merge_final.py",
}


class LangflowPasteReadyStep10Tests(unittest.TestCase):
    def test_root_node_files_are_standalone(self):
        self.assertTrue(NODE_FILES.issubset({path.name for path in COMPONENT_DIR.glob("*.py")}))
        for filename in sorted(NODE_FILES):
            path = COMPONENT_DIR / filename
            text = path.read_text(encoding="utf-8")
            self.assertIn("# VISIBLE_STANDALONE_RUNTIME", text, path.name)
            self.assertNotIn("_RUNTIME_SOURCES", text, path.name)
            self.assertNotIn("_RUNTIME_ORDER", text, path.name)
            self.assertNotIn("_PACKAGE_NAMES", text, path.name)
            self.assertNotIn("_bootstrap_runtime", text, path.name)
            self.assertNotIn("langflow_custom_component", text, path.name)
            self.assertNotIn("from manufacturing_langflow_runtime", text, path.name)
            self.assertNotIn("import manufacturing_langflow_runtime", text, path.name)
            compile(text, str(path), "exec")

    def test_representative_root_nodes_import_successfully(self):
        for filename in ["domain_rules.py", "plan_datasets.py", "session_memory.py"]:
            path = COMPONENT_DIR / filename
            spec = importlib.util.spec_from_file_location(f"standalone_{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            self.assertIsNotNone(spec.loader, filename)
            sys.modules[spec.name] = module
            try:
                spec.loader.exec_module(module)
            finally:
                sys.modules.pop(spec.name, None)

    def test_import_ignores_stale_runtime_state(self):
        runtime_prefix = "manufacturing_langflow_runtime"
        stale_names = [name for name in list(sys.modules) if name == runtime_prefix or name.startswith(f"{runtime_prefix}.")]
        original_modules = {name: sys.modules[name] for name in stale_names}
        try:
            for name in stale_names:
                sys.modules.pop(name, None)

            root = types.ModuleType(runtime_prefix)
            root.__embedded_bootstrap_loaded__ = True
            sys.modules[runtime_prefix] = root

            path = COMPONENT_DIR / "domain_rules.py"
            spec = importlib.util.spec_from_file_location("standalone_domain_rules_partial", path)
            module = importlib.util.module_from_spec(spec)
            self.assertIsNotNone(spec.loader, path.name)
            sys.modules[spec.name] = module
            try:
                spec.loader.exec_module(module)
            finally:
                sys.modules.pop(spec.name, None)
            self.assertNotIn("manufacturing_langflow_runtime.component_base", sys.modules)
        finally:
            for name in [name for name in list(sys.modules) if name == runtime_prefix or name.startswith(f"{runtime_prefix}.")]:
                sys.modules.pop(name, None)
            sys.modules.update(original_modules)

    def test_paste_ready_folder_mirrors_root_nodes(self):
        expected = {*(NODE_FILES), "README.md"}
        self.assertEqual(expected, {path.name for path in PASTE_READY_DIR.iterdir() if path.is_file()})
        for filename in sorted(NODE_FILES):
            root_text = (COMPONENT_DIR / filename).read_text(encoding="utf-8")
            mirror_text = (PASTE_READY_DIR / filename).read_text(encoding="utf-8")
            self.assertEqual(root_text, mirror_text, filename)


if __name__ == "__main__":
    unittest.main()
