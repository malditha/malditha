import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from config_diff import Difference, compare, main, render_json, render_text


class CompareTests(unittest.TestCase):
    def test_equal_documents_have_no_differences(self):
        self.assertEqual(compare({"port": 443}, {"port": 443}), [])

    def test_reports_added_and_removed_paths(self):
        result = compare({"old": True}, {"new": True})
        self.assertEqual([(item.path, item.status) for item in result], [("new", "added"), ("old", "removed")])

    def test_reports_changed_scalar_without_value(self):
        result = compare({"token": "alpha"}, {"token": "bravo"})
        self.assertEqual(result, [Difference("token", "changed", "string", "string")])
        self.assertNotIn("alpha", render_text(result))
        self.assertNotIn("bravo", render_text(result))

    def test_reports_type_change(self):
        self.assertEqual(compare({"retries": 3}, {"retries": "3"}), [Difference("retries", "type_changed", "number", "string")])

    def test_compares_nested_objects_and_arrays(self):
        result = compare({"servers": [{"enabled": True}]}, {"servers": [{"enabled": False}, "backup"]})
        self.assertEqual([(item.path, item.status) for item in result], [("servers[0].enabled", "changed"), ("servers[1]", "added")])

    def test_ignore_path_skips_a_whole_branch(self):
        result = compare({"runtime": {"token": "old", "port": 80}}, {"runtime": {"token": "new", "port": 443}}, ["runtime"])
        self.assertEqual(result, [])

    def test_output_order_is_deterministic(self):
        result = compare({"z": 1, "a": 1}, {"z": 2, "a": 2})
        self.assertEqual([item.path for item in result], ["a", "z"])

    def test_json_report_contains_paths_but_not_values(self):
        report = render_json(compare({"password": "first-secret"}, {"password": "second-secret"}))
        parsed = json.loads(report)
        self.assertTrue(parsed["different"])
        self.assertEqual(parsed["differences"][0]["path"], "password")
        self.assertNotIn("secret", report)

    def test_cli_exit_codes_for_match_difference_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = root / "before.json"
            after = root / "after.json"
            before.write_text('{"port": 80}', encoding="utf-8")
            after.write_text('{"port": 80}', encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(before), str(after)]), 0)
            after.write_text('{"port": 443}', encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(before), str(after)]), 1)
            after.write_text("not-json", encoding="utf-8")
            with redirect_stderr(StringIO()):
                self.assertEqual(main([str(before), str(after)]), 2)


if __name__ == "__main__":
    unittest.main()
