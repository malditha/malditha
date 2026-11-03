import json
import tempfile
import unittest
from pathlib import Path

from test_data_factory import FactoryError, generate_records, load_schema, validate_schema


def schema(fields=None):
    return {"fields": fields or [{"name": "score", "type": "integer", "minimum": 1, "maximum": 3}]}


class FactoryTests(unittest.TestCase):
    def test_same_seed_produces_same_records(self):
        self.assertEqual(generate_records(schema(), 5, 8), generate_records(schema(), 5, 8))

    def test_different_seed_changes_records(self):
        self.assertNotEqual(generate_records(schema(), 10, 1), generate_records(schema(), 10, 2))

    def test_field_order_is_preserved(self):
        data = schema([{"name": "flag", "type": "boolean"}, {"name": "count", "type": "integer", "minimum": 0, "maximum": 0}])
        self.assertEqual(list(generate_records(data, 1, 1)[0]), ["flag", "count"])

    def test_integer_stays_within_bounds(self):
        values = [row["score"] for row in generate_records(schema(), 100, 4)]
        self.assertTrue(all(1 <= value <= 3 for value in values))

    def test_choice_uses_declared_values(self):
        data = schema([{"name": "state", "type": "choice", "values": ["new", "done"]}])
        self.assertLessEqual({r["state"] for r in generate_records(data, 20, 7)}, {"new", "done"})

    def test_string_has_prefix_and_length(self):
        data = schema([{"name": "id", "type": "string", "prefix": "T-", "length": 5}])
        value = generate_records(data, 1, 1)[0]["id"]
        self.assertTrue(value.startswith("T-")); self.assertEqual(len(value), 7)

    def test_test_email_uses_reserved_domain_and_unique_row(self):
        data = schema([{"name": "email", "type": "test_email"}])
        values = [r["email"] for r in generate_records(data, 3, 1)]
        self.assertEqual(len(set(values)), 3); self.assertTrue(all(v.endswith("@example.test") for v in values))

    def test_duplicate_field_name_rejected(self):
        fields = [{"name": "x", "type": "boolean"}, {"name": "x", "type": "boolean"}]
        with self.assertRaises(FactoryError): validate_schema(schema(fields))

    def test_unknown_option_rejected(self):
        data = schema([{"name": "x", "type": "boolean", "extra": True}])
        with self.assertRaises(FactoryError): validate_schema(data)

    def test_inverted_integer_bounds_rejected(self):
        data = schema([{"name": "x", "type": "integer", "minimum": 2, "maximum": 1}])
        with self.assertRaises(FactoryError): validate_schema(data)

    def test_count_is_bounded(self):
        with self.assertRaises(FactoryError): generate_records(schema(), 1001, 1)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"schema.json"; path.write_text('{"fields":[],"fields":[]}', encoding="utf-8")
            with self.assertRaises(FactoryError): load_schema(path)


if __name__ == "__main__": unittest.main()
