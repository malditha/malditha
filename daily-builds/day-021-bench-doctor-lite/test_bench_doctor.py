import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from bench_doctor import inspect_bench, main, render_json, summary


def make_bench(root: Path, *, paused: bool = False) -> None:
    (root / "apps" / "frappe").mkdir(parents=True)
    (root / "sites" / "example.test").mkdir(parents=True)
    (root / "Procfile").write_text("web: bench serve\n", encoding="utf-8")
    (root / "sites" / "apps.txt").write_text("frappe\nerpnext\n", encoding="utf-8")
    (root / "sites" / "common_site_config.json").write_text(json.dumps({"pause_scheduler": paused, "redis_queue": "redis://queue"}), encoding="utf-8")
    (root / "sites" / "example.test" / "site_config.json").write_text(json.dumps({"db_name": "demo", "db_password": "never-report-this"}), encoding="utf-8")


class BenchDoctorTests(unittest.TestCase):
    def test_healthy_fixture_has_only_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root)
            self.assertEqual(summary(inspect_bench(root))["warn"], 0)

    def test_missing_directories_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            checks = inspect_bench(Path(directory))
            self.assertEqual(summary(checks)["fail"], 2)

    def test_missing_procfile_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root); (root / "Procfile").unlink()
            self.assertIn("procfile", [c.code for c in inspect_bench(root) if c.level == "warn"])

    def test_empty_apps_registry_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root); (root / "sites" / "apps.txt").write_text("", encoding="utf-8")
            self.assertIn("apps-registry", [c.code for c in inspect_bench(root) if c.level == "fail"])

    def test_invalid_common_config_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root); (root / "sites" / "common_site_config.json").write_text("bad", encoding="utf-8")
            self.assertIn("common-config", [c.code for c in inspect_bench(root) if c.level == "fail"])

    def test_paused_scheduler_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root, paused=True)
            self.assertIn("scheduler-paused", [c.code for c in inspect_bench(root) if c.level == "warn"])

    def test_missing_db_name_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root); (root / "sites" / "example.test" / "site_config.json").write_text("{}", encoding="utf-8")
            self.assertIn("site-db-name", [c.code for c in inspect_bench(root) if c.level == "warn"])

    def test_json_report_never_contains_config_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root)
            report = render_json(root, inspect_bench(root))
            self.assertNotIn("never-report-this", report)
            self.assertFalse(json.loads(report)["values_included"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); make_bench(root)
            with redirect_stdout(StringIO()): self.assertEqual(main([str(root)]), 0)
            (root / "Procfile").unlink()
            with redirect_stdout(StringIO()): self.assertEqual(main([str(root)]), 1)
            with redirect_stderr(StringIO()): self.assertEqual(main([str(root / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()
