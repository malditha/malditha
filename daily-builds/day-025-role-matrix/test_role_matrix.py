import json
import tempfile
import unittest
from pathlib import Path

from role_matrix import InputError, build_report, main, render_text, validate_rows


def row(**changes):
    value = {"doctype": "Issue", "role": "Support Agent", "permlevel": 0, "read": 1}
    value.update(changes)
    return value


class RoleMatrixTests(unittest.TestCase):
    def test_rejects_non_array(self):
        with self.assertRaisesRegex(InputError, "JSON array"):
            validate_rows({})

    def test_rejects_missing_identity(self):
        with self.assertRaisesRegex(InputError, "role"):
            validate_rows([{"doctype": "Issue"}])

    def test_rejects_negative_permission_level(self):
        with self.assertRaisesRegex(InputError, "non-negative"):
            validate_rows([row(permlevel=-1)])

    def test_rejects_ambiguous_action_value(self):
        with self.assertRaisesRegex(InputError, "write"):
            validate_rows([row(write="yes")])

    def test_defaults_missing_actions_to_false(self):
        parsed = validate_rows([row()])
        self.assertFalse(parsed[0]["write"])

    def test_aggregates_actions_across_permission_levels(self):
        rows = validate_rows([row(read=1), row(permlevel=1, write=1)])
        report = build_report(rows)
        self.assertEqual(report["matrix"][0]["permlevels"], [0, 1])
        self.assertTrue(report["matrix"][0]["actions"]["read"])
        self.assertTrue(report["matrix"][0]["actions"]["write"])

    def test_detects_identical_duplicate_rows(self):
        report = build_report(validate_rows([row(), row()]))
        self.assertEqual(report["summary"]["duplicate_groups"], 1)
        self.assertEqual(report["summary"]["conflicting_groups"], 0)

    def test_detects_conflicting_rows(self):
        report = build_report(validate_rows([row(write=0), row(write=1)]))
        self.assertEqual(report["summary"]["conflicting_groups"], 1)

    def test_text_report_has_no_unrecognized_input_properties(self):
        parsed = validate_rows([row(owner_email="private@example.invalid")])
        output = render_text(build_report(parsed))
        self.assertNotIn("owner_email", output)
        self.assertNotIn("private@example.invalid", output)

    def test_main_returns_two_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("not-json", encoding="utf-8")
            self.assertEqual(main([str(path)]), 2)

    def test_main_returns_one_for_review_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.json"
            path.write_text(json.dumps([row(), row()]), encoding="utf-8")
            self.assertEqual(main([str(path), "--json"]), 1)


if __name__ == "__main__":
    unittest.main()
