import json
import tempfile
import unittest
from pathlib import Path

from openapi_endpoint_index import (
    DocumentError,
    build_index,
    format_text,
    load_document,
    main,
)


SAMPLE = {
    "openapi": "3.1.0",
    "info": {"title": "Pet Desk", "version": "1.0.0"},
    "paths": {
        "/pets/{petId}": {
            "parameters": [{"name": "petId", "in": "path", "required": True}],
            "get": {
                "operationId": "getPet",
                "summary": "Fetch one pet",
                "tags": ["Pets"],
                "deprecated": True,
                "parameters": [{"name": "include", "in": "query"}],
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/pets": {
            "post": {
                "operationId": "createPet",
                "tags": ["Pets", "Write"],
                "responses": {"201": {"description": "Created"}},
            },
            "get": {"summary": "List pets", "responses": {}},
        },
    },
}


class EndpointIndexTests(unittest.TestCase):
    def test_builds_deterministic_operation_index(self):
        report = build_index(SAMPLE)
        self.assertEqual(
            [(item["method"], item["path"]) for item in report["endpoints"]],
            [("GET", "/pets"), ("POST", "/pets"), ("GET", "/pets/{petId}")],
        )

    def test_keeps_only_allowlisted_operation_metadata(self):
        endpoint = build_index(SAMPLE)["endpoints"][2]
        self.assertEqual(endpoint["operation_id"], "getPet")
        self.assertEqual(endpoint["summary"], "Fetch one pet")
        self.assertEqual(endpoint["tags"], ["Pets"])
        self.assertTrue(endpoint["deprecated"])
        self.assertEqual(endpoint["parameter_count"], 2)
        self.assertEqual(endpoint["response_codes"], ["200"])

    def test_ignores_path_level_non_methods(self):
        report = build_index(SAMPLE)
        self.assertNotIn("PARAMETERS", [item["method"] for item in report["endpoints"]])

    def test_reports_document_summary(self):
        report = build_index(SAMPLE)
        self.assertEqual(report["api"], {"title": "Pet Desk", "version": "1.0.0", "openapi": "3.1.0"})
        self.assertEqual(report["endpoint_count"], 3)
        self.assertEqual(report["tag_counts"], {"Pets": 2, "Write": 1, "Untagged": 1})

    def test_rejects_unsupported_or_missing_openapi_version(self):
        for version in (None, "2.0"):
            document = {"paths": {}}
            if version:
                document["openapi"] = version
            with self.subTest(version=version), self.assertRaises(DocumentError):
                build_index(document)

    def test_rejects_malformed_paths_and_operations(self):
        with self.assertRaises(DocumentError):
            build_index({"openapi": "3.0.3", "info": {}, "paths": []})
        with self.assertRaises(DocumentError):
            build_index({"openapi": "3.0.3", "info": {}, "paths": {"/x": {"get": []}}})

    def test_rejects_excessive_operation_count(self):
        paths = {f"/items/{index}": {"get": {}} for index in range(501)}
        with self.assertRaisesRegex(DocumentError, "500"):
            build_index({"openapi": "3.1.0", "info": {}, "paths": paths})

    def test_load_document_rejects_invalid_json_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as folder:
            invalid = Path(folder) / "invalid.json"
            invalid.write_text("{broken", encoding="utf-8")
            with self.assertRaises(DocumentError):
                load_document(invalid)
            large = Path(folder) / "large.json"
            large.write_text(" " * (2_000_001), encoding="utf-8")
            with self.assertRaisesRegex(DocumentError, "2 MB"):
                load_document(large)

    def test_text_report_is_readable(self):
        output = format_text(build_index(SAMPLE))
        self.assertIn("Pet Desk 1.0.0 (OpenAPI 3.1.0)", output)
        self.assertIn("GET    /pets", output)
        self.assertIn("[DEPRECATED]", output)

    def test_cli_writes_json_and_uses_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "openapi.json"
            target = Path(folder) / "index.json"
            source.write_text(json.dumps(SAMPLE), encoding="utf-8")
            self.assertEqual(main([str(source), "--json", "--output", str(target)]), 0)
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(report["endpoint_count"], 3)
            self.assertEqual(main([str(Path(folder) / "missing.json")]), 2)


if __name__ == "__main__":
    unittest.main()
