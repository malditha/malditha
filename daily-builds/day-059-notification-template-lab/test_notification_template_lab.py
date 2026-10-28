import json
import tempfile
import unittest
from pathlib import Path

from notification_template_lab import LabError, as_json, as_text, evaluate, load_plan, main


class NotificationTemplateLabTests(unittest.TestCase):
    def plan(self, **overrides):
        item = {"id": "welcome", "channel": "email", "subject": "Hi {{name}}", "body": "Ticket {{ticket}} is ready.", "data": {"name": "Mina", "ticket": 42}}
        item.update(overrides)
        return {"templates": [item]}

    def test_renders_ready_template(self):
        result = evaluate(self.plan())[0]
        self.assertEqual("ready", result.status)
        self.assertEqual("Hi Mina", result.subject)
        self.assertEqual("Ticket 42 is ready.", result.body)

    def test_preserves_first_seen_placeholder_order(self):
        result = evaluate(self.plan(subject="{{ticket}} {{name}}", body="{{ticket}}"))[0]
        self.assertEqual(("ticket", "name"), result.placeholders)

    def test_blocks_preview_when_variable_is_missing(self):
        result = evaluate(self.plan(data={"name": "Mina"}))[0]
        self.assertEqual("blocked", result.status)
        self.assertEqual(("ticket",), result.missing)
        self.assertIsNone(result.body)

    def test_reports_unused_keys_without_values(self):
        result = evaluate(self.plan(data={"name": "Mina", "ticket": 42, "secret": "hidden"}))[0]
        self.assertEqual(("secret",), result.unused)
        self.assertNotIn("hidden", as_text([result]))

    def test_rejects_duplicate_template_ids(self):
        plan = self.plan()
        plan["templates"].append(dict(plan["templates"][0]))
        with self.assertRaisesRegex(LabError, "duplicate template id"):
            evaluate(plan)

    def test_rejects_unknown_template_fields(self):
        with self.assertRaisesRegex(LabError, "unknown fields"):
            evaluate(self.plan(send=True))

    def test_rejects_nested_data(self):
        with self.assertRaisesRegex(LabError, "string or number"):
            evaluate(self.plan(data={"name": {"first": "Mina"}}))

    def test_rejects_invalid_variable_names(self):
        with self.assertRaisesRegex(LabError, "invalid variable name"):
            evaluate(self.plan(data={"bad name": "x"}))

    def test_json_summary_counts_statuses(self):
        results = evaluate({"templates": [self.plan()["templates"][0], {"id": "alert", "channel": "chat", "body": "{{missing}}", "data": {}}]})
        payload = json.loads(as_json(results))
        self.assertEqual({"templates": 2, "ready": 1, "blocked": 1}, payload["summary"])

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text('{"templates": [], "templates": []}', encoding="utf-8")
            with self.assertRaisesRegex(LabError, "duplicate key"):
                load_plan(path)

    def test_main_returns_one_for_blocked_template(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(self.plan(data={})), encoding="utf-8")
            self.assertEqual(1, main([str(path)]))


if __name__ == "__main__":
    unittest.main()
