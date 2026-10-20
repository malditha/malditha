import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validator import InputError, load_json_file, validate_payload


ROOT = Path(__file__).parent


class WorkflowInputValidatorTests(unittest.TestCase):
    def contract(self):
        return {
            "unknown_fields": "reject",
            "fields": {
                "ticket_id": {"type": "string", "required": True, "min_length": 3, "max_length": 32},
                "priority": {"type": "string", "required": True, "enum": ["low", "normal", "high"]},
                "notify": {"type": "boolean", "required": False},
                "tags": {"type": "array", "required": False, "max_items": 3, "item_type": "string"},
                "attempt": {"type": "integer", "required": False, "minimum": 0, "maximum": 5},
            },
        }

    def test_accepts_payload_that_matches_contract(self):
        report = validate_payload(
            self.contract(),
            {"ticket_id": "HD-104", "priority": "high", "notify": True, "tags": ["sla"], "attempt": 1},
        )
        self.assertEqual("valid", report["status"])
        self.assertEqual([], report["issues"])

    def test_reports_missing_required_field_without_values(self):
        report = validate_payload(self.contract(), {"ticket_id": "HD-104"})
        self.assertEqual("invalid", report["status"])
        self.assertEqual(
            [{"field": "priority", "code": "required", "message": "required field is missing"}],
            report["issues"],
        )

    def test_rejects_unknown_fields(self):
        report = validate_payload(
            self.contract(),
            {"ticket_id": "HD-104", "priority": "normal", "password": "secret"},
        )
        self.assertEqual("unknown_field", report["issues"][0]["code"])
        self.assertNotIn("secret", json.dumps(report))

    def test_reports_type_mismatch_without_echoing_value(self):
        report = validate_payload(self.contract(), {"ticket_id": 104, "priority": "normal"})
        self.assertEqual("type", report["issues"][0]["code"])
        self.assertNotIn("104", json.dumps(report))

    def test_enforces_string_length(self):
        report = validate_payload(self.contract(), {"ticket_id": "HD", "priority": "normal"})
        self.assertEqual("min_length", report["issues"][0]["code"])

    def test_enforces_enum_without_listing_supplied_value(self):
        report = validate_payload(self.contract(), {"ticket_id": "HD-104", "priority": "urgent"})
        self.assertEqual("enum", report["issues"][0]["code"])
        self.assertNotIn("urgent", json.dumps(report))

    def test_enforces_array_item_count_and_item_type(self):
        report = validate_payload(
            self.contract(),
            {"ticket_id": "HD-104", "priority": "normal", "tags": ["one", "two", "three", 4]},
        )
        codes = [issue["code"] for issue in report["issues"]]
        self.assertEqual(["max_items", "item_type"], codes)

    def test_boolean_is_not_accepted_as_integer(self):
        report = validate_payload(
            self.contract(),
            {"ticket_id": "HD-104", "priority": "normal", "attempt": True},
        )
        self.assertEqual("type", report["issues"][0]["code"])

    def test_enforces_integer_range(self):
        report = validate_payload(
            self.contract(),
            {"ticket_id": "HD-104", "priority": "normal", "attempt": 9},
        )
        self.assertEqual("maximum", report["issues"][0]["code"])

    def test_rejects_malformed_contract(self):
        with self.assertRaises(InputError):
            validate_payload({"fields": {"name": {"type": "mystery"}}}, {"name": "Ada"})

    def test_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payload.json"
            path.write_text('{"ticket_id":"A","ticket_id":"B"}', encoding="utf-8")
            with self.assertRaises(InputError):
                load_json_file(path)

    def test_cli_returns_expected_exit_codes_and_json(self):
        valid = subprocess.run(
            [sys.executable, "validator.py", "contract.json", "payload.json", "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, valid.returncode)
        self.assertEqual("valid", json.loads(valid.stdout)["status"])

        with tempfile.TemporaryDirectory() as directory:
            payload_path = Path(directory) / "invalid.json"
            payload_path.write_text('{"ticket_id":"HD-104"}', encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, "validator.py", "contract.json", str(payload_path), "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(1, invalid.returncode)
        self.assertEqual("invalid", json.loads(invalid.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
