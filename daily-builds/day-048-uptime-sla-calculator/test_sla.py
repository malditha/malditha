import json
import subprocess
import sys
import unittest
from pathlib import Path
from sla import calculate


class SLATests(unittest.TestCase):
    def test_monthly_budget(self):
        self.assertEqual(calculate("30", "99.9")["allowed_downtime_minutes"], "43.2")

    def test_exact_boundary(self):
        self.assertEqual(calculate("30", "99.9", "43.2")["status"], "within_budget")

    def test_small_overrun(self):
        r = calculate("30", "99.9", "43.200000001")
        self.assertEqual(r["status"], "over_budget")
        self.assertEqual(r["remaining_budget_minutes"], "-0.000000001")

    def test_perfect_target(self):
        self.assertEqual(calculate(1, 100)["allowed_downtime_minutes"], "0")

    def test_full_outage(self):
        self.assertEqual(calculate(1, 99, 1440)["observed_availability_percent"], "0.000000000")

    def test_fractional_window(self):
        self.assertEqual(calculate("0.5", 99)["window_minutes"], "720")

    def test_invalid_values(self):
        for value in ["nan", "Infinity", "abc", True, "1e-20"]:
            with self.subTest(value=value), self.assertRaises(ValueError): calculate(value, 99)

    def test_target_bounds(self):
        for value in [0, -1, 101]:
            with self.assertRaises(ValueError): calculate(30, value)

    def test_window_and_downtime_bounds(self):
        for args in [(0,99,0),(3661,99,0),(1,99,-1),(1,99,1441)]:
            with self.assertRaises(ValueError): calculate(*args)

    def test_cli_json_exit(self):
        r = subprocess.run([sys.executable,"sla.py","--period-days","30","--target-percent","99.9","--downtime-minutes","44","--json"],cwd=Path(__file__).parent,capture_output=True,text=True)
        self.assertEqual(r.returncode,1)
        self.assertEqual(json.loads(r.stdout)["status"],"over_budget")


if __name__ == "__main__": unittest.main()
