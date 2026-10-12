import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

import ssl_expiry_reporter as reporter


NOW = datetime(2026, 10, 12, 0, 0, tzinfo=timezone.utc)


class EndpointTests(unittest.TestCase):
    def test_default_port_is_443(self):
        self.assertEqual(reporter.parse_endpoint("example.com"), ("example.com", 443))

    def test_explicit_port_is_preserved(self):
        self.assertEqual(reporter.parse_endpoint("api.example.com:8443"), ("api.example.com", 8443))

    def test_invalid_port_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "port"):
            reporter.parse_endpoint("example.com:70000")

    def test_endpoint_count_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "20"):
            reporter.normalize_endpoints([f"host-{index}.example" for index in range(21)])

    def test_duplicate_endpoints_are_removed_in_input_order(self):
        self.assertEqual(
            reporter.normalize_endpoints(["example.com", "example.com:443", "api.example.com"]),
            [("example.com", 443), ("api.example.com", 443)],
        )


class ExpiryTests(unittest.TestCase):
    def test_expired_certificate_is_classified(self):
        result = reporter.classify_expiry(NOW.replace(day=11), NOW, 30, 7)
        self.assertEqual(result["status"], "expired")
        self.assertEqual(result["days_remaining"], -1)

    def test_critical_certificate_is_classified(self):
        result = reporter.classify_expiry(NOW.replace(day=15), NOW, 30, 7)
        self.assertEqual(result["status"], "critical")
        self.assertEqual(result["days_remaining"], 3)

    def test_warning_and_healthy_boundaries_are_distinct(self):
        warning = reporter.classify_expiry(NOW.replace(day=22), NOW, 30, 7)
        healthy = reporter.classify_expiry(datetime(2026, 12, 1, tzinfo=timezone.utc), NOW, 30, 7)
        self.assertEqual(warning["status"], "warning")
        self.assertEqual(healthy["status"], "healthy")

    def test_thresholds_must_be_ordered(self):
        with self.assertRaisesRegex(ValueError, "critical"):
            reporter.validate_thresholds(7, 7)


class InspectionTests(unittest.TestCase):
    def test_inspection_uses_injected_verified_certificate(self):
        def connector(host, port, timeout):
            self.assertEqual((host, port, timeout), ("example.com", 443, 4.0))
            return {
                "notAfter": "Nov 30 00:00:00 2026 GMT",
                "issuer": ((('commonName', 'Example Test CA'),),),
            }

        result = reporter.inspect_endpoint(("example.com", 443), 4.0, NOW, 30, 7, connector)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["endpoint"], "example.com:443")
        self.assertNotIn("issuer", result)

    def test_connection_error_is_sanitized(self):
        def connector(host, port, timeout):
            raise TimeoutError("internal route 10.0.0.8 timed out")

        result = reporter.inspect_endpoint(("example.com", 443), 4.0, NOW, 30, 7, connector)
        self.assertEqual(result, {"endpoint": "example.com:443", "status": "error", "error": "timeout"})

    def test_json_cli_returns_review_exit_code_without_network(self):
        original = reporter.inspect_endpoint
        reporter.inspect_endpoint = lambda *args, **kwargs: {
            "endpoint": "example.com:443",
            "status": "warning",
            "days_remaining": 12,
            "not_after": "2026-10-24T00:00:00Z",
        }
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                code = reporter.main(["example.com", "--json"])
        finally:
            reporter.inspect_endpoint = original
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["summary"]["warning"], 1)


if __name__ == "__main__":
    unittest.main()
