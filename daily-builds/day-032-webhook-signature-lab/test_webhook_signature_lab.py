import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from webhook_signature_lab import (
    SignatureError,
    compute_signature,
    parse_signature_header,
    read_secret,
    sign_payload,
    verify_payload,
)


SECRET = b"local-development-secret"


class WebhookSignatureTests(unittest.TestCase):
    def test_matches_known_hmac_sha256_value(self):
        payload = b'{"event":"demo"}'
        expected = hmac.new(SECRET, b"1700000000." + payload, hashlib.sha256).hexdigest()
        self.assertEqual(compute_signature(payload, SECRET, 1700000000), expected)

    def test_sign_header_round_trips_through_verification(self):
        payload = b'{"event":"created"}'
        signed = sign_payload(payload, SECRET, 1700000000)
        report = verify_payload(payload, SECRET, signed["header"], now=1700000020)
        self.assertTrue(report["valid"])

    def test_modified_payload_fails(self):
        signed = sign_payload(b"original", SECRET, 1700000000)
        report = verify_payload(b"changed", SECRET, signed["header"], now=1700000000)
        self.assertFalse(report["signature_matches"])
        self.assertFalse(report["valid"])

    def test_wrong_secret_fails(self):
        signed = sign_payload(b"payload", SECRET, 1700000000)
        report = verify_payload(b"payload", b"different-local-secret", signed["header"], now=1700000000)
        self.assertFalse(report["valid"])

    def test_expired_timestamp_fails_even_with_matching_signature(self):
        signed = sign_payload(b"payload", SECRET, 1700000000)
        report = verify_payload(b"payload", SECRET, signed["header"], now=1700001000, tolerance=300)
        self.assertTrue(report["signature_matches"])
        self.assertFalse(report["timestamp_valid"])
        self.assertFalse(report["valid"])

    def test_future_timestamp_outside_tolerance_fails(self):
        signed = sign_payload(b"payload", SECRET, 1700001000)
        report = verify_payload(b"payload", SECRET, signed["header"], now=1700000000, tolerance=300)
        self.assertFalse(report["valid"])

    def test_accepts_one_of_multiple_v1_values(self):
        valid = compute_signature(b"payload", SECRET, 1700000000)
        header = "t=1700000000,v1=" + ("0" * 64) + ",v1=" + valid
        self.assertTrue(verify_payload(b"payload", SECRET, header, now=1700000000)["valid"])

    def test_rejects_malformed_and_duplicate_timestamp_headers(self):
        headers = ["v1=" + ("0" * 64), "t=1,t=2,v1=" + ("0" * 64), "t=1,v1=nope", "t=1"]
        for header in headers:
            with self.subTest(header=header), self.assertRaises(SignatureError):
                parse_signature_header(header)

    def test_rejects_invalid_tolerance(self):
        with self.assertRaises(SignatureError):
            verify_payload(b"x", SECRET, "t=1,v1=" + ("0" * 64), now=1, tolerance=86401)

    def test_secret_is_read_from_named_environment_variable(self):
        self.assertEqual(read_secret("WEBHOOK_SECRET", {"WEBHOOK_SECRET": "local-development-secret"}), SECRET)
        with self.assertRaises(SignatureError):
            read_secret("bad-name", {})

    def test_reports_never_include_secret(self):
        signed = sign_payload(b"payload", SECRET, 1700000000)
        verified = verify_payload(b"payload", SECRET, signed["header"], now=1700000000)
        self.assertNotIn(SECRET.decode(), json.dumps(signed))
        self.assertNotIn(SECRET.decode(), json.dumps(verified))
        self.assertFalse(verified["network_request_sent"])

    def test_cli_sign_and_verify_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = Path(directory) / "payload.json"
            payload.write_text('{"event":"demo"}', encoding="utf-8")
            env = {**os.environ, "WEBHOOK_SECRET": "local-development-secret"}
            signed = subprocess.run(
                [sys.executable, "webhook_signature_lab.py", "--format", "json", "sign", str(payload), "--timestamp", "1700000000"],
                cwd=Path(__file__).parent, env=env, capture_output=True, text=True
            )
            self.assertEqual(signed.returncode, 0, signed.stderr)
            header = json.loads(signed.stdout)["header"]
            verified = subprocess.run(
                [sys.executable, "webhook_signature_lab.py", "--format", "json", "verify", str(payload), "--header", header, "--now", "1700000000"],
                cwd=Path(__file__).parent, env=env, capture_output=True, text=True
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertTrue(json.loads(verified.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
