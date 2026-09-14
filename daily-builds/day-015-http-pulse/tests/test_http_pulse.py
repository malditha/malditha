import io
import urllib.error
import unittest
from http.client import HTTPMessage

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from http_pulse import CheckResult, check_all, check_url, parse_urls, render_text


class FakeResponse:
    def __init__(self, status):
        self.status = status
        self.closed = False

    def getcode(self):
        return self.status

    def close(self):
        self.closed = True


class Clock:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


class HttpPulseTests(unittest.TestCase):
    def test_parse_urls_ignores_comments_and_blanks(self):
        self.assertEqual(parse_urls("# services\n\nhttps://example.com/health\nhttp://localhost:3000\n"), ("https://example.com/health", "http://localhost:3000"))

    def test_parse_urls_rejects_non_http_scheme(self):
        with self.assertRaisesRegex(ValueError, "line 1"):
            parse_urls("file:///tmp/status")

    def test_parse_urls_rejects_empty_input(self):
        with self.assertRaisesRegex(ValueError, "no URLs"):
            parse_urls("# only a comment")

    def test_success_records_status_and_elapsed_time(self):
        response = FakeResponse(204)
        result = check_url("https://example.test", 2, opener=lambda *_args, **_kwargs: response, clock=Clock(1.0, 1.125))
        self.assertEqual(result, CheckResult("https://example.test", True, 204, 125))
        self.assertTrue(response.closed)

    def test_redirect_status_is_healthy(self):
        result = check_url("https://example.test", 2, opener=lambda *_args, **_kwargs: FakeResponse(302), clock=Clock(2.0, 2.01))
        self.assertTrue(result.ok)

    def test_http_error_retains_status_without_body(self):
        error = urllib.error.HTTPError("https://example.test", 503, "Unavailable", HTTPMessage(), io.BytesIO(b"private body"))
        def fail(*_args, **_kwargs):
            raise error
        result = check_url("https://example.test", 2, opener=fail, clock=Clock(1.0, 1.05))
        self.assertEqual(result.status, 503)
        self.assertEqual(result.error, "HTTP 503")
        self.assertNotIn("private", repr(result))

    def test_network_error_has_no_status(self):
        def fail(*_args, **_kwargs):
            raise urllib.error.URLError("connection refused")
        result = check_url("https://example.test", 2, opener=fail, clock=Clock(1.0, 1.02))
        self.assertFalse(result.ok)
        self.assertIsNone(result.status)
        self.assertEqual(result.error, "connection refused")

    def test_check_all_preserves_input_order_and_timeout(self):
        calls = []
        def checker(url, timeout):
            calls.append((url, timeout))
            return CheckResult(url, True, 200, 1)
        results = check_all(("https://a.test", "https://b.test"), 3.5, checker)
        self.assertEqual([r.url for r in results], ["https://a.test", "https://b.test"])
        self.assertEqual(calls, [("https://a.test", 3.5), ("https://b.test", 3.5)])

    def test_text_summary_counts_health(self):
        output = render_text((CheckResult("https://a.test", True, 200, 8), CheckResult("https://b.test", False, 500, 14, "HTTP 500")))
        self.assertIn("1/2 healthy", output)
        self.assertIn("[OK] 200", output)
        self.assertIn("[FAIL] 500", output)


if __name__ == "__main__":
    unittest.main()
