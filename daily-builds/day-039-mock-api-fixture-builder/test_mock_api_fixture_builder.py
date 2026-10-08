import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mock_api_fixture_builder import build_fixtures, render_jsonl


SCRIPT = Path(__file__).with_name("mock_api_fixture_builder.py")


class MockApiFixtureBuilderTests(unittest.TestCase):
    def test_builds_integer_sequence(self):
        fixtures = build_fixtures({
            "count": 3,
            "fields": {"id": {"type": "integer", "start": 10, "step": 5}},
        })
        self.assertEqual(fixtures, [{"id": 10}, {"id": 15}, {"id": 20}])

    def test_builds_zero_padded_prefixed_strings(self):
        fixtures = build_fixtures({
            "count": 2,
            "fields": {"code": {"type": "string", "prefix": "item-", "pad": 3}},
        })
        self.assertEqual(fixtures, [{"code": "item-001"}, {"code": "item-002"}])

    def test_alternates_booleans_from_configured_start(self):
        fixtures = build_fixtures({
            "count": 3,
            "fields": {"active": {"type": "boolean", "start": False}},
        })
        self.assertEqual(fixtures, [{"active": False}, {"active": True}, {"active": False}])

    def test_cycles_enum_values(self):
        fixtures = build_fixtures({
            "count": 4,
            "fields": {"status": {"type": "enum", "values": ["new", "ready"]}},
        })
        self.assertEqual([item["status"] for item in fixtures], ["new", "ready", "new", "ready"])

    def test_builds_null_fields(self):
        fixtures = build_fixtures({"count": 2, "fields": {"note": {"type": "null"}}})
        self.assertEqual(fixtures, [{"note": None}, {"note": None}])

    def test_preserves_declared_field_order(self):
        fixtures = build_fixtures({
            "count": 1,
            "fields": {
                "id": {"type": "integer"},
                "label": {"type": "string", "prefix": "record-"},
            },
        })
        self.assertEqual(list(fixtures[0]), ["id", "label"])

    def test_rejects_unknown_top_level_keys(self):
        with self.assertRaisesRegex(ValueError, "unknown blueprint keys"):
            build_fixtures({"count": 1, "fields": {"id": {"type": "integer"}}, "secret": True})

    def test_rejects_unknown_rule_types(self):
        with self.assertRaisesRegex(ValueError, "unsupported type"):
            build_fixtures({"count": 1, "fields": {"email": {"type": "personal-data"}}})

    def test_rejects_excessive_record_count(self):
        with self.assertRaisesRegex(ValueError, "count must be between 1 and 1000"):
            build_fixtures({"count": 1001, "fields": {"id": {"type": "integer"}}})

    def test_rejects_too_many_fields(self):
        fields = {f"field_{index}": {"type": "null"} for index in range(51)}
        with self.assertRaisesRegex(ValueError, "between 1 and 50 fields"):
            build_fixtures({"count": 1, "fields": fields})

    def test_json_lines_contains_one_record_per_line(self):
        output = render_jsonl(build_fixtures({
            "count": 2,
            "fields": {"id": {"type": "integer", "start": 7}},
        }))
        self.assertEqual(output, '{"id": 7}\n{"id": 8}')

    def test_cli_outputs_deterministic_json(self):
        blueprint = {
            "count": 2,
            "fields": {
                "id": {"type": "integer", "start": 1},
                "name": {"type": "string", "prefix": "user-", "pad": 2},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "blueprint.json"
            source.write_text(json.dumps(blueprint), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(json.loads(result.stdout), [
            {"id": 1, "name": "user-01"},
            {"id": 2, "name": "user-02"},
        ])


if __name__ == "__main__":
    unittest.main()
