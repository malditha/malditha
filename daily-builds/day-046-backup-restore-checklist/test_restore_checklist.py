import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from restore_checklist import CHECKS, MAX_BYTES, load_record, review


def complete():
    return {"checks": {key: {"status": "pass", "evidence_recorded": True} for key in CHECKS}}


class ChecklistTests(unittest.TestCase):
    def test_complete_record(self):
        self.assertEqual(review(complete())["overall"], "record_complete")

    def test_missing_checks_are_unverified(self):
        self.assertEqual(review({"checks": {}})["summary"]["unverified"], 6)

    def test_pass_without_evidence_is_unverified(self):
        r = complete(); r["checks"]["data_validated"]["evidence_recorded"] = False
        self.assertEqual(review(r)["next_checks"], ["data_validated"])

    def test_failure_blocks(self):
        r = complete(); r["checks"]["restore_completed"]["status"] = "fail"
        self.assertEqual(review(r)["overall"], "blocked")

    def test_explicit_unverified(self):
        r = complete(); r["checks"]["integrity_checked"]["status"] = "unverified"
        self.assertEqual(review(r)["overall"], "incomplete")

    def test_unknown_check_rejected(self):
        with self.assertRaises(ValueError): review({"checks": {"typo": {}}})

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError): review({"checks": {"data_validated": {"status": "yes"}}})

    def test_evidence_must_be_boolean(self):
        with self.assertRaises(ValueError): review({"checks": {"data_validated": {"status": "pass", "evidence_recorded": "true"}}})

    def test_private_fields_omitted(self):
        r = complete(); r["secret"] = "private-value"; r["checks"]["data_validated"]["notes"] = "private-value"
        self.assertNotIn("private-value", json.dumps(review(r)))

    def test_file_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "record.json"; p.write_bytes(b" " * (MAX_BYTES + 1))
            with self.assertRaises(ValueError): load_record(p)

    def test_cli_json(self):
        p = subprocess.run([sys.executable, "restore_checklist.py", "sample.json", "--json"], cwd=Path(__file__).parent, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stdout)["overall"], "incomplete")


if __name__ == "__main__": unittest.main()
