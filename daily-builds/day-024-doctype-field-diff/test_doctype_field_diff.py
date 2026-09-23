import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from doctype_field_diff import InputError, compare_documents, format_text, has_differences, normalize_fields


def doc(*fields):
    return {"name": "Work Order", "fields": list(fields)}


def field(name, fieldtype="Data", **properties):
    return {"fieldname": name, "fieldtype": fieldtype, **properties}


class DocTypeFieldDiffTests(unittest.TestCase):
    def test_reports_added_and_removed_fields(self):
        report = compare_documents(doc(field("title"), field("old")), doc(field("title"), field("new")))
        self.assertEqual(report["added"], ["new"])
        self.assertEqual(report["removed"], ["old"])

    def test_reports_safe_property_changes(self):
        report = compare_documents(doc(field("status", reqd=0)), doc(field("status", reqd=1, read_only=1)))
        names = [item["property"] for item in report["changed"][0]["changes"]]
        self.assertEqual(names, ["reqd", "read_only"])

    def test_ignores_labels_descriptions_and_defaults(self):
        baseline = doc(field("token", label="Old", description="private", default="secret-a"))
        candidate = doc(field("token", label="New", description="changed", default="secret-b"))
        self.assertFalse(has_differences(compare_documents(baseline, candidate)))

    def test_reports_reordered_fields(self):
        report = compare_documents(doc(field("a"), field("b")), doc(field("b"), field("a")))
        self.assertEqual(len(report["reordered"]), 2)

    def test_identical_documents_have_no_differences(self):
        report = compare_documents(doc(field("title", reqd=1)), doc(field("title", reqd=1)))
        self.assertFalse(has_differences(report))

    def test_rejects_missing_fields_array(self):
        with self.assertRaisesRegex(InputError, "fields"):
            normalize_fields({}, "baseline")

    def test_rejects_duplicate_fieldnames(self):
        with self.assertRaisesRegex(InputError, "duplicate"):
            normalize_fields(doc(field("title"), field("title")), "baseline")

    def test_rejects_missing_fieldtype(self):
        with self.assertRaisesRegex(InputError, "fieldtype"):
            normalize_fields({"fields": [{"fieldname": "title"}]}, "baseline")

    def test_text_report_does_not_include_ignored_values(self):
        baseline = doc(field("title", reqd=0, default="private-a"))
        candidate = doc(field("title", reqd=1, default="private-b"))
        output = format_text(compare_documents(baseline, candidate))
        self.assertIn("reqd", output)
        self.assertNotIn("private", output)

    def test_cli_json_and_exit_code(self):
        script = Path(__file__).with_name("doctype_field_diff.py")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "base.json"
            new = Path(directory) / "new.json"
            base.write_text(json.dumps(doc(field("title"))), encoding="utf-8")
            new.write_text(json.dumps(doc(field("title", reqd=1))), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), str(base), str(new), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["summary"]["changed"], 1)


if __name__ == "__main__":
    unittest.main()
