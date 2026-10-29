import json
import tempfile
import unittest
from pathlib import Path

from workflow_documenter import DocumentError, build_document, load_export, main, to_json, to_markdown


class WorkflowDocumenterTests(unittest.TestCase):
    def workflow(self):
        return {
            "name": "Lead follow-up",
            "active": False,
            "nodes": [
                {"name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "parameters": {"path": "hidden", "httpMethod": "POST"}},
                {"name": "Create task", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "parameters": {"url": "secret"}, "credentials": {"httpHeaderAuth": {"id": "private", "name": "private"}}},
                {"name": "Note", "type": "n8n-nodes-base.noOp", "typeVersion": 1, "parameters": {}},
            ],
            "connections": {"Webhook": {"main": [[{"node": "Create task", "type": "main", "index": 0}]]}},
            "settings": {"executionOrder": "v1"},
        }

    def test_builds_nodes_and_edges(self):
        doc = build_document(self.workflow())
        self.assertEqual(3, len(doc.nodes))
        self.assertEqual(("Webhook", "Create task"), (doc.edges[0].source, doc.edges[0].target))

    def test_detects_trigger(self):
        self.assertTrue(build_document(self.workflow()).nodes[0].is_trigger)

    def test_lists_keys_not_parameter_values(self):
        text = to_markdown(build_document(self.workflow()))
        self.assertIn("httpMethod, path", text)
        self.assertNotIn("hidden", text)
        self.assertNotIn("secret", text)

    def test_lists_credential_type_not_identifier(self):
        text = to_json(build_document(self.workflow()))
        self.assertIn("httpHeaderAuth", text)
        self.assertNotIn("private", text)

    def test_finds_disconnected_node(self):
        self.assertEqual(("Note",), build_document(self.workflow()).disconnected)

    def test_finds_broken_target(self):
        flow = self.workflow()
        flow["connections"]["Webhook"]["main"][0].append({"node": "Missing", "index": 0})
        self.assertEqual(("Missing",), build_document(flow).broken_targets)

    def test_rejects_unknown_source(self):
        flow = self.workflow()
        flow["connections"]["Ghost"] = {"main": []}
        with self.assertRaisesRegex(DocumentError, "source is not a node"):
            build_document(flow)

    def test_rejects_duplicate_node_names(self):
        flow = self.workflow()
        flow["nodes"].append(dict(flow["nodes"][0]))
        with self.assertRaisesRegex(DocumentError, "duplicate node name"):
            build_document(flow)

    def test_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "flow.json"
            path.write_text('{"name":"a","name":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(DocumentError, "duplicate key"):
                load_export(path)

    def test_markdown_has_review_sections(self):
        text = to_markdown(build_document(self.workflow()))
        self.assertIn("## Nodes", text)
        self.assertIn("## Connections", text)
        self.assertIn("## Review notes", text)

    def test_json_summary(self):
        payload = json.loads(to_json(build_document(self.workflow())))
        self.assertEqual({"nodes": 3, "connections": 1, "triggers": 1, "disabled": 0}, payload["summary"])

    def test_main_writes_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "flow.json"
            output = Path(directory) / "flow.md"
            source.write_text(json.dumps(self.workflow()), encoding="utf-8")
            self.assertEqual(0, main([str(source), "--output", str(output)]))
            self.assertIn("# Lead follow-up", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
