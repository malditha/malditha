import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from json_schema_starter import SchemaStarterError, build_schema, infer_schema, load_sample


class JSONSchemaStarterTests(unittest.TestCase):
    def test_infers_scalar_types_without_confusing_boolean_and_integer(self):
        schema = infer_schema({"active": True, "count": 2, "ratio": 1.5, "name": "demo", "note": None})
        props = schema["properties"]
        self.assertEqual(props["active"], {"type": "boolean"})
        self.assertEqual(props["count"], {"type": "integer"})
        self.assertEqual(props["ratio"], {"type": "number"})
        self.assertEqual(props["name"], {"type": "string"})
        self.assertEqual(props["note"], {"type": "null"})

    def test_object_keys_are_sorted_and_required(self):
        schema = infer_schema({"z": 1, "a": 2})
        self.assertEqual(list(schema["properties"]), ["a", "z"])
        self.assertEqual(schema["required"], ["a", "z"])

    def test_nested_objects_are_closed_by_default(self):
        schema = infer_schema({"profile": {"name": "Ada"}})
        nested = schema["properties"]["profile"]
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(nested["additionalProperties"])

    def test_allow_additional_applies_recursively(self):
        schema = infer_schema({"profile": {"name": "Ada"}}, allow_additional=True)
        self.assertTrue(schema["additionalProperties"])
        self.assertTrue(schema["properties"]["profile"]["additionalProperties"])

    def test_homogeneous_array_uses_one_item_schema(self):
        schema = infer_schema({"ports": [80, 443]})
        self.assertEqual(schema["properties"]["ports"]["items"], {"type": "integer"})

    def test_mixed_array_uses_deterministic_any_of(self):
        schema = infer_schema({"values": [1, "one", 2]})
        items = schema["properties"]["values"]["items"]
        self.assertEqual(items, {"anyOf": [{"type": "integer"}, {"type": "string"}]})

    def test_empty_array_keeps_open_items_schema(self):
        self.assertEqual(infer_schema([]), {"type": "array", "items": {}})

    def test_build_schema_adds_draft_and_title(self):
        schema = build_schema({"id": 1}, "Event payload")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "Event payload")

    def test_rejects_excessive_depth(self):
        value = 1
        for _ in range(34):
            value = {"next": value}
        with self.assertRaisesRegex(SchemaStarterError, "maximum depth"):
            infer_schema(value)

    def test_load_rejects_non_object_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.json"
            path.write_text("[1, 2]", encoding="utf-8")
            with self.assertRaisesRegex(SchemaStarterError, "root sample"):
                load_sample(path)

    def test_load_reports_invalid_json_without_echoing_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.json"
            path.write_text('{"token":"secret",}', encoding="utf-8")
            with self.assertRaisesRegex(SchemaStarterError, "invalid JSON at line") as caught:
                load_sample(path)
            self.assertNotIn("secret", str(caught.exception))

    def test_cli_writes_schema_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "sample.json"
            output = root / "schema.json"
            sample.write_text(json.dumps({"event": "created", "attempt": 1}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "json_schema_starter.py", str(sample), "--title", "Webhook", "--output", str(output)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(generated["title"], "Webhook")
            self.assertEqual(generated["properties"]["attempt"]["type"], "integer")


if __name__ == "__main__":
    unittest.main()
