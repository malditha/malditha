import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import scheduler_snapshot as tool


class SchedulerSnapshotTests(unittest.TestCase):
    def make_bench(self, root: Path, common=None, sites=None) -> Path:
        bench = root / "frappe-bench"
        sites_dir = bench / "sites"
        sites_dir.mkdir(parents=True)
        if common is not None:
            (sites_dir / "common_site_config.json").write_text(json.dumps(common), encoding="utf-8")
        for name, config in (sites or {}).items():
            site_dir = sites_dir / name
            site_dir.mkdir()
            (site_dir / "site_config.json").write_text(json.dumps(config), encoding="utf-8")
        return bench

    def test_truthy_values_are_normalized(self):
        for value in (True, 1, "1", "TRUE", "yes", "on"):
            self.assertTrue(tool.is_truthy(value))
        for value in (False, 0, "0", "false", None):
            self.assertFalse(tool.is_truthy(value))

    def test_site_setting_overrides_common_setting(self):
        value, source = tool.resolve_flag({"pause_scheduler": 0}, {"pause_scheduler": 1}, "pause_scheduler")
        self.assertEqual((value, source), (False, "site"))

    def test_snapshot_reports_scheduler_states(self):
        with tempfile.TemporaryDirectory() as directory:
            bench = self.make_bench(Path(directory), {"pause_scheduler": 1}, {"alpha.local": {}, "beta.local": {"pause_scheduler": 0, "maintenance_mode": 1}})
            snapshot = tool.build_snapshot(bench, "2026-09-21T00:00:00+00:00")
        self.assertEqual([site["status"] for site in snapshot["sites"]], ["paused", "maintenance"])
        self.assertEqual(snapshot["site_count"], 2)

    def test_snapshot_omits_unapproved_configuration_values(self):
        with tempfile.TemporaryDirectory() as directory:
            bench = self.make_bench(Path(directory), {"db_password": "common-secret"}, {"alpha.local": {"db_password": "site-secret", "api_key": "token"}})
            snapshot = tool.build_snapshot(bench, "2026-09-21T00:00:00+00:00")
        serialized = json.dumps(snapshot)
        self.assertNotIn("common-secret", serialized)
        self.assertNotIn("site-secret", serialized)
        self.assertNotIn("token", serialized)
        self.assertNotIn("db_password", serialized)

    def test_invalid_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(tool.SnapshotError):
                tool.load_object(path)

    def test_compare_reports_added_removed_and_changed_sites(self):
        before = {"sites": [{"site": "old", "status": "enabled"}, {"site": "same", "status": "enabled"}]}
        after = {"sites": [{"site": "new", "status": "enabled"}, {"site": "same", "status": "paused"}]}
        result = tool.compare_snapshots(before, after)
        self.assertEqual(result["added"], ["new"])
        self.assertEqual(result["removed"], ["old"])
        self.assertEqual(result["changed"], [{"site": "same", "fields": ["status"]}])

    def test_compare_is_stable_when_nothing_changed(self):
        snapshot = {"sites": [{"site": "alpha", "status": "enabled", "pause_scheduler": False}]}
        self.assertFalse(tool.compare_snapshots(snapshot, snapshot)["has_changes"])

    def test_cli_writes_snapshot_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bench = self.make_bench(root, {}, {"alpha.local": {}})
            output = root / "snapshot.json"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = tool.main(["snapshot", str(bench), "--output", str(output)])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output.read_text())["sites"][0]["site"], "alpha.local")

    def test_cli_returns_two_for_invalid_bench(self):
        with contextlib.redirect_stderr(io.StringIO()):
            exit_code = tool.main(["snapshot", "/does/not/exist"])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
