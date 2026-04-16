from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW_PATH = ROOT / "langflow_custom_component" / "manufacturing_langflow_import.json"


class LangflowImportJsonStep9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flow = json.loads(FLOW_PATH.read_text(encoding="utf-8"))
        cls.nodes = cls.flow["data"]["nodes"]
        cls.edges = cls.flow["data"]["edges"]
        cls.node_by_id = {node["id"]: node for node in cls.nodes}

    def _display_name(self, node):
        return node["data"].get("display_name") or node["data"]["node"].get("display_name")

    def _find_node(self, display_name: str, x: int):
        for node in self.nodes:
            if self._display_name(node) == display_name and int(node["position"]["x"]) == x:
                return node
        self.fail(f"Could not find node {display_name} at x={x}")

    def test_flow_has_expected_root_shape(self):
        self.assertEqual(self.flow["name"], "Manufacturing Agent (Custom Components)")
        self.assertIn("nodes", self.flow["data"])
        self.assertIn("edges", self.flow["data"])
        self.assertIn("viewport", self.flow["data"])

    def test_flow_has_expected_node_and_edge_counts(self):
        self.assertEqual(len(self.nodes), 22)
        self.assertEqual(len(self.edges), 29)

    def test_required_nodes_exist(self):
        display_names = [self._display_name(node) for node in self.nodes]
        expected_counts = {
            "Domain Rules": 1,
            "Domain Registry": 1,
            "Chat Input": 1,
            "Session Memory": 2,
            "Extract Params": 1,
            "Decide Mode": 1,
            "Route Mode": 1,
            "Run Followup": 1,
            "Plan Datasets": 1,
            "Build Jobs": 1,
            "Route Plan": 1,
            "Execute Jobs": 2,
            "Route Single": 1,
            "Build Single": 1,
            "Analyze Single": 1,
            "Route Multi": 1,
            "Build Multi": 1,
            "Analyze Multi": 1,
            "Merge Result": 1,
            "Chat Output": 1,
        }
        for name, count in expected_counts.items():
            self.assertEqual(display_names.count(name), count, name)

    def test_custom_node_code_is_embedded_and_local_import_free(self):
        for node in self.nodes:
            display_name = self._display_name(node)
            code = node["data"]["node"]["template"].get("code", {}).get("value", "")
            self.assertTrue(code, display_name)
            if display_name in {"Chat Input", "Chat Output"}:
                continue
            self.assertIn("# VISIBLE_STANDALONE_RUNTIME", code, display_name)
            self.assertNotIn("_RUNTIME_SOURCES", code, display_name)
            self.assertNotIn("_RUNTIME_ORDER", code, display_name)
            self.assertNotIn("_PACKAGE_NAMES", code, display_name)
            self.assertNotIn("_bootstrap_runtime", code, display_name)
            self.assertNotIn("langflow_custom_component", code, display_name)
            compile(code, f"<{display_name}>", "exec")

    def test_key_edges_follow_branch_visible_contract(self):
        chat_input = self._find_node("Chat Input", 80)
        session_load = self._find_node("Session Memory", 430)
        route_mode = self._find_node("Route Mode", 1130)
        run_followup = self._find_node("Run Followup", 1480)
        plan_datasets = self._find_node("Plan Datasets", 1480)
        route_plan = self._find_node("Route Plan", 1480)
        session_save = self._find_node("Session Memory", 3230)
        chat_output = self._find_node("Chat Output", 3580)

        expected_pairs = {
            (chat_input["id"], "message", session_load["id"], "message"),
            (route_mode["id"], "followup_out", run_followup["id"], "state"),
            (route_mode["id"], "retrieval_out", plan_datasets["id"], "state"),
            (route_plan["id"], "finish_out", self._find_node("Merge Result", 2880)["id"], "finish_result"),
            (self._find_node("Merge Result", 2880)["id"], "result_out", session_save["id"], "result"),
            (session_save["id"], "saved_out", chat_output["id"], "input_value"),
        }

        actual_pairs = set()
        for edge in self.edges:
            actual_pairs.add(
                (
                    edge["source"],
                    edge["data"]["sourceHandle"]["name"],
                    edge["target"],
                    edge["data"]["targetHandle"]["fieldName"],
                )
            )
        self.assertTrue(expected_pairs.issubset(actual_pairs))


if __name__ == "__main__":
    unittest.main()
