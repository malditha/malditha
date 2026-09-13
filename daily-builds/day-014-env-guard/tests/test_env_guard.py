import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_guard import compare, parse_env_text, render_text


class EnvGuardTests(unittest.TestCase):
    def test_parses_comments_blanks_and_export(self):
        result = parse_env_text("# note\n\nexport API_URL=https://example.test\nTOKEN=x=y\n")
        self.assertEqual(result.keys, ("API_URL", "TOKEN"))

    def test_values_are_not_retained(self):
        secret = "never-print-this"
        result = parse_env_text(f"TOKEN={secret}\n")
        self.assertNotIn(secret, repr(result))

    def test_reports_duplicate_key_once(self):
        result = parse_env_text("PORT=1\nPORT=2\nPORT=3\n")
        self.assertEqual(result.duplicates, ("PORT",))

    def test_reports_malformed_line_numbers(self):
        result = parse_env_text("GOOD=yes\nNO_EQUALS\nBAD-KEY=x\n")
        self.assertEqual(result.malformed_lines, (2, 3))

    def test_compare_finds_missing_and_unexpected(self):
        report = compare(parse_env_text("A=\nB=\n"), parse_env_text("B=1\nC=2\n"))
        self.assertEqual(report.missing, ("A",))
        self.assertEqual(report.unexpected, ("C",))
        self.assertFalse(report.valid)

    def test_matching_keys_are_valid_regardless_of_order(self):
        report = compare(parse_env_text("A=\nB=\n"), parse_env_text("B=secret\nA=value\n"))
        self.assertTrue(report.valid)

    def test_text_report_never_contains_values(self):
        report = compare(parse_env_text("TOKEN=placeholder\n"), parse_env_text("TOKEN=real-secret\nEXTRA=sensitive\n"))
        output = render_text(report)
        self.assertNotIn("real-secret", output)
        self.assertNotIn("sensitive", output)
        self.assertIn("EXTRA", output)

    def test_cli_json_and_failure_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / ".env.example"
            environment = root / ".env"
            template.write_text("REQUIRED=\n", encoding="utf-8")
            environment.write_text("OTHER=secret\n", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(ROOT / "env_guard.py"), str(template), str(environment), "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 1)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["missing"], ["REQUIRED"])
            self.assertEqual(payload["unexpected"], ["OTHER"])
            self.assertNotIn("secret", run.stdout)

    def test_cli_success_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.env"
            environment = root / "current.env"
            template.write_text("A=\n", encoding="utf-8")
            environment.write_text("A=value\n", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(ROOT / "env_guard.py"), str(template), str(environment)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0)
            self.assertIn("OK", run.stdout)


if __name__ == "__main__":
    unittest.main()
