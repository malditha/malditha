import json
import tempfile
import unittest
from pathlib import Path

from retry_error_map import InputError, analyze, format_text, load_workflow


def good():
    return {"name": "Lead intake", "nodes": [
        {"id": "webhook", "kind": "trigger", "next": ["validate"]},
        {"id": "validate", "kind": "action", "next": ["send"], "on_error": "failed"},
        {"id": "send", "kind": "action", "next": [], "on_error": "retry_send"},
        {"id": "retry_send", "kind": "retry", "next": ["send"], "on_error": "failed"},
        {"id": "failed", "kind": "error_handler", "next": []},
    ]}


class MapTests(unittest.TestCase):
    def test_ready_workflow(self):
        report = analyze(good())
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["counts"], {"nodes": 5, "reachable": 5, "issues": 0})

    def test_missing_error_path(self):
        data = good(); data["nodes"][1].pop("on_error")
        self.assertIn("missing_error_path", {x["code"] for x in analyze(data)["issues"]})

    def test_invalid_error_target(self):
        data = good(); data["nodes"][1]["on_error"] = "send"
        self.assertIn("invalid_error_target", {x["code"] for x in analyze(data)["issues"]})

    def test_unreachable_node(self):
        data = good(); data["nodes"].append({"id": "orphan", "kind": "error_handler", "next": []})
        self.assertIn("unreachable", {x["code"] for x in analyze(data)["issues"]})

    def test_retry_must_return_to_action(self):
        data = good(); data["nodes"][3]["next"] = ["failed"]
        self.assertIn("retry_without_action", {x["code"] for x in analyze(data)["issues"]})

    def test_handler_is_terminal(self):
        data = good(); data["nodes"][4]["next"] = ["send"]
        self.assertIn("handler_not_terminal", {x["code"] for x in analyze(data)["issues"]})

    def test_requires_one_trigger(self):
        data = good(); data["nodes"][0]["kind"] = "action"; data["nodes"][0]["on_error"] = "failed"
        self.assertIn("trigger_count", {x["code"] for x in analyze(data)["issues"]})

    def test_text_lists_paths_without_values(self):
        output = format_text(analyze(good()))
        self.assertIn("send [action]", output)
        self.assertIn("Issues:\n- none", output)

    def test_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "x.json"
            path.write_text('{"name":"x","name":"y","nodes":[]}', encoding="utf-8")
            with self.assertRaises(InputError): load_workflow(path)

    def test_unknown_reference_rejected(self):
        data = good(); data["nodes"][0]["next"] = ["missing"]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "x.json"; path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(InputError): load_workflow(path)


if __name__ == "__main__":
    unittest.main()
