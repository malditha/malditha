import json
import subprocess
import sys
import unittest
from pathlib import Path
from log_rotation_planner import plan


class PlannerTests(unittest.TestCase):
    def test_daily_uncompressed(self):
        r = plan(100, 1, 14, 1, 2000)
        self.assertEqual((r["steady_mb"], r["peak_mb"]), (1500, 1600))

    def test_compression_applies_only_to_archives(self):
        r = plan(100, 1, 14, .25, 1000)
        self.assertEqual((r["active_mb"], r["archives_mb"], r["peak_mb"]), (100, 350, 550))

    def test_partial_interval_rounds_up(self):
        r = plan(10, 3, 7, 1, 1000)
        self.assertEqual((r["archive_count"], r["effective_archive_days"]), (3, 9))

    def test_exact_budget_passes(self):
        self.assertEqual(plan(100, 1, 14, 1, 1600)["status"], "within_budget")

    def test_over_budget_has_negative_headroom(self):
        r = plan(100, 1, 14, 1, 1000)
        self.assertEqual(r["headroom_mb"], -600)

    def test_invalid_numeric_values(self):
        for value in [0, -1, float("nan"), float("inf"), True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                plan(value, 1, 14, 1, 1000)

    def test_invalid_ratios(self):
        for ratio in [0, 1.1, -1]:
            with self.assertRaises(ValueError): plan(100, 1, 14, ratio, 1000)

    def test_invalid_intervals(self):
        for interval, retention in [(0, 14), (15, 14), (1, 3651), (1.5, 14)]:
            with self.assertRaises(ValueError): plan(100, interval, retention, 1, 1000)

    def test_fractional_growth(self):
        self.assertEqual(plan(.5, 2, 4, .5, 10)["peak_mb"], 3)

    def test_cli_json_and_review_exit(self):
        r = subprocess.run([sys.executable, "log_rotation_planner.py", "--daily-mb", "100", "--budget-mb", "1000", "--json"], cwd=Path(__file__).parent, text=True, capture_output=True)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout)["status"], "over_budget")


if __name__ == "__main__": unittest.main()
