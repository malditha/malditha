import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_request_builder import REDACTED, RequestValidationError, build_request


class RequestBuilderTests(unittest.TestCase):
    def test_normalizes_method_and_sorts_new_query_fields(self):
        report = build_request({"method": "post", "url": "https://api.example.test/items?z=9", "query": {"b": 2, "a": True}})
        self.assertEqual(report["method"], "POST")
        self.assertEqual(report["url"], "https://api.example.test/items?z=9&a=true&b=2")

    def test_list_query_values_are_repeated(self):
        report = build_request({"url": "https://example.test", "query": {"tag": ["one", "two"]}})
        self.assertEqual(report["url"], "https://example.test/?tag=one&tag=two")

    def test_rejects_non_http_url(self):
        with self.assertRaises(RequestValidationError):
            build_request({"url": "file:///tmp/example"})

    def test_rejects_credentials_and_fragments(self):
        for url in ("https://user:pass@example.test", "https://example.test/#private"):
            with self.subTest(url=url), self.assertRaises(RequestValidationError):
                build_request({"url": url})

    def test_redacts_sensitive_headers(self):
        report = build_request({"url": "https://example.test", "headers": {"Authorization": "Bearer secret", "X-API-Key": "abc", "Accept": "application/json"}})
        self.assertEqual(report["headers"]["Authorization"], REDACTED)
        self.assertEqual(report["headers"]["X-API-Key"], REDACTED)
        self.assertEqual(report["headers"]["Accept"], "application/json")
        self.assertNotIn("Bearer secret", report["curl"])

    def test_rejects_header_injection(self):
        with self.assertRaises(RequestValidationError):
            build_request({"url": "https://example.test", "headers": {"X-Test": "ok\r\nInjected: yes"}})

    def test_rejects_get_or_head_body(self):
        for method in ("GET", "HEAD"):
            with self.subTest(method=method), self.assertRaises(RequestValidationError):
                build_request({"method": method, "url": "https://example.test", "json": {"x": 1}})

    def test_rejects_unknown_fields(self):
        with self.assertRaisesRegex(RequestValidationError, "unknown field"):
            build_request({"url": "https://example.test", "timeout": 10})

    def test_rejects_too_many_headers(self):
        with self.assertRaises(RequestValidationError):
            build_request({"url": "https://example.test", "headers": {f"X-{n}": "ok" for n in range(41)}})

    def test_input_is_not_mutated(self):
        spec = {"method": "post", "url": "https://example.test", "query": {"page": 1}}
        before = json.dumps(spec, sort_keys=True)
        build_request(spec)
        self.assertEqual(json.dumps(spec, sort_keys=True), before)

    def test_curl_is_shell_quoted(self):
        report = build_request({"method": "POST", "url": "https://example.test", "json": {"message": "it's safe; echo no"}})
        self.assertIn("--data", report["curl"])
        self.assertNotIn("; echo no", report["curl"].split("--data", 1)[0])

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            path.write_text(json.dumps({"url": "https://example.test/health"}), encoding="utf-8")
            result = subprocess.run([sys.executable, "api_request_builder.py", str(path), "--format", "json"], cwd=Path(__file__).parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["network_request_sent"])


if __name__ == "__main__":
    unittest.main()
