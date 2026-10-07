import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from data_shape_profiler import profile_records, render_text


SCRIPT = Path(__file__).with_name("data_shape_profiler.py")


class DataShapeProfilerTests(unittest.TestCase):
    def test_counts_presence_missing_and_types(self):
        report = profile_records([{"id": 1, "name": "Ana"}, {"id": 2}])
        self.assertEqual(report["fields"]["name"], {
            "present": 1, "missing": 1, "null": 0, "types": {"string": 1}
        })

    def test_distinguishes_boolean_from_integer(self):
        report = profile_records([{"active": True}, {"active": 1}])
        self.assertEqual(report["fields"]["active"]["types"], {"boolean": 1, "integer": 1})

    def test_counts_null_separately(self):
        report = profile_records([{"email": None}, {"email": "a@example.test"}])
        self.assertEqual(report["fields"]["email"]["null"], 1)
        self.assertEqual(report["fields"]["email"]["types"], {"null": 1, "string": 1})

    def test_profiles_nested_object_paths(self):
        report = profile_records([{"profile": {"city": "Manila"}}, {"profile": {}}])
        self.assertEqual(report["fields"]["profile.city"]["present"], 1)
        self.assertEqual(report["fields"]["profile.city"]["missing"], 1)

    def test_treats_arrays_as_a_type_boundary(self):
        report = profile_records([{"tags": ["python", "json"]}])
        self.assertEqual(report["fields"]["tags"]["types"], {"array": 1})
        self.assertNotIn("tags[]", report["fields"])

    def test_empty_array_returns_zero_records_and_no_fields(self):
        self.assertEqual(profile_records([]), {"record_count": 0, "field_count": 0, "fields": {}})

    def test_rejects_non_array_input(self):
        with self.assertRaisesRegex(ValueError, "JSON array"):
            profile_records({"id": 1})

    def test_rejects_non_object_record(self):
        with self.assertRaisesRegex(ValueError, "record 2 must be an object"):
            profile_records([{"id": 1}, "bad"])

    def test_rejects_too_many_records(self):
        with self.assertRaisesRegex(ValueError, "more than 1 records"):
            profile_records([{}, {}], max_records=1)

    def test_rejects_excessive_depth(self):
        with self.assertRaisesRegex(ValueError, "maximum depth of 2"):
            profile_records([{"a": {"b": {"c": 1}}}], max_depth=2)

    def test_text_report_contains_counts_but_not_values(self):
        output = render_text(profile_records([{"token": "secret-value"}]))
        self.assertIn("token", output)
        self.assertIn("string:1", output)
        self.assertNotIn("secret-value", output)

    def test_cli_outputs_machine_readable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "records.json"
            source.write_text('[{"id":1},{"id":2,"name":"Ana"}]', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--json"],
                check=True, capture_output=True, text=True,
            )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["record_count"], 2)
        self.assertEqual(payload["fields"]["name"]["missing"], 1)


if __name__ == "__main__":
    unittest.main()
