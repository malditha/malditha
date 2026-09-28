import copy
import json
import tempfile
import unittest
from pathlib import Path

from site_config_redactor import (
    MAX_KEYS,
    REDACTED,
    ConfigError,
    main,
    redact_config,
)


class RedactorTests(unittest.TestCase):
    def test_keeps_allowlisted_operational_values(self):
        result = redact_config({"db_type": "mariadb", "pause_scheduler": 1})
        self.assertEqual(result["redacted_config"]["db_type"], "mariadb")
        self.assertEqual(result["redacted_config"]["pause_scheduler"], 1)

    def test_redacts_known_secret_names(self):
        result = redact_config({"db_password": "not-a-real-secret", "encryption_key": "x"})
        self.assertEqual(result["redacted_config"]["db_password"], REDACTED)
        self.assertEqual(result["redacted_config"]["encryption_key"], REDACTED)

    def test_redacts_unknown_fields_by_default(self):
        result = redact_config({"custom_feature": "enabled"})
        self.assertEqual(result["redacted_config"]["custom_feature"], REDACTED)

    def test_redacts_nested_values_as_one_marker(self):
        result = redact_config({"workers": {"short": {"timeout": 300}}})
        self.assertEqual(result["redacted_config"]["workers"], REDACTED)

    def test_rejects_wrong_type_for_numeric_field(self):
        result = redact_config({"socketio_port": True})
        self.assertEqual(result["redacted_config"]["socketio_port"], REDACTED)

    def test_sorts_keys_and_summary(self):
        result = redact_config({"z_private": 1, "db_type": "postgres", "a_private": 2})
        self.assertEqual(list(result["redacted_config"]), ["a_private", "db_type", "z_private"])
        self.assertEqual(result["summary"]["redacted_keys"], ["a_private", "z_private"])

    def test_does_not_mutate_source(self):
        source = {"db_password": {"value": "secret"}, "developer_mode": 1}
        before = copy.deepcopy(source)
        redact_config(source)
        self.assertEqual(source, before)

    def test_sensitive_value_never_appears_in_serialized_report(self):
        secret = "fictional-password-123"
        payload = json.dumps(redact_config({"db_password": secret, "api_key": secret}))
        self.assertNotIn(secret, payload)

    def test_rejects_non_object_input(self):
        with self.assertRaises(ConfigError):
            redact_config(["not", "an", "object"])

    def test_rejects_too_many_keys(self):
        with self.assertRaises(ConfigError):
            redact_config({f"key_{index}": index for index in range(MAX_KEYS + 1)})

    def test_cli_writes_safe_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "site_config.json"
            output = root / "safe.json"
            source.write_text(json.dumps({"db_type": "mariadb", "db_password": "hidden"}))
            self.assertEqual(main([str(source), "--output", str(output)]), 0)
            saved = output.read_text()
            self.assertIn(REDACTED, saved)
            self.assertNotIn("hidden", saved)


if __name__ == "__main__":
    unittest.main()
