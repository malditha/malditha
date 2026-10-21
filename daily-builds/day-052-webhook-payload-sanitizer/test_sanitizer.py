import json
import tempfile
import unittest
from pathlib import Path

from sanitizer import InputError, MASK, load_json, sanitize_payload


class SanitizerTests(unittest.TestCase):
    def test_masks_nested_sensitive_keys(self):
        cleaned, report = sanitize_payload({"user": {"password": "nope"}, "token": "nope"})
        self.assertEqual(cleaned, {"token": MASK, "user": {"password": MASK}})
        self.assertEqual(report["redacted_count"], 2)

    def test_preserves_non_sensitive_values(self):
        payload = {"event": "order.created", "amount": 42, "ok": True, "empty": None}
        cleaned, _ = sanitize_payload(payload)
        self.assertEqual(cleaned, payload)

    def test_remove_strategy_omits_keys(self):
        cleaned, report = sanitize_payload({"name": "A", "api_key": "nope"}, strategy="remove")
        self.assertEqual(cleaned, {"name": "A"})
        self.assertEqual(report["redacted_paths"], ["$.api_key"])

    def test_walks_objects_inside_arrays(self):
        cleaned, _ = sanitize_payload({"items": [{"authorization": "nope", "id": 1}]})
        self.assertEqual(cleaned["items"][0], {"authorization": MASK, "id": 1})

    def test_matches_camel_and_punctuated_keys(self):
        cleaned, _ = sanitize_payload({"refreshToken": "nope", "client-secret": "nope"})
        self.assertEqual(cleaned, {"client-secret": MASK, "refreshToken": MASK})

    def test_supports_custom_sensitive_keys(self):
        cleaned, _ = sanitize_payload({"internal_code": "nope"}, extra_keys={"internal-code"})
        self.assertEqual(cleaned["internal_code"], MASK)

    def test_report_never_contains_values(self):
        _, report = sanitize_payload({"password": "unique-secret-value"})
        self.assertNotIn("unique-secret-value", json.dumps(report))

    def test_rejects_unknown_strategy(self):
        with self.assertRaises(InputError):
            sanitize_payload({}, strategy="blur")

    def test_rejects_excessive_depth(self):
        value = "leaf"
        for _ in range(22):
            value = {"child": value}
        with self.assertRaises(InputError):
            sanitize_payload(value)

    def test_loader_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "payload.json"
            path.write_text('{"token":"one","token":"two"}', encoding="utf-8")
            with self.assertRaises(InputError):
                load_json(path)


if __name__ == "__main__":
    unittest.main()
