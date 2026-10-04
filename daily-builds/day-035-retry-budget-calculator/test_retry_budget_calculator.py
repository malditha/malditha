import json
import subprocess
import sys
import unittest
from pathlib import Path

from retry_budget_calculator import calculate_retry_plan, render_text


SCRIPT = Path(__file__).with_name("retry_budget_calculator.py")


class RetryBudgetCalculatorTests(unittest.TestCase):
    def test_exponential_delays_fit_budget(self):
        plan = calculate_retry_plan(7000, 1000, "2", 10000, max_retries=5)
        self.assertEqual(plan.delays_ms, [1000, 2000, 4000])
        self.assertEqual(plan.remaining_ms, 0)

    def test_delay_cap_is_applied(self):
        plan = calculate_retry_plan(11000, 1000, "3", 4000, max_retries=4)
        self.assertEqual(plan.delays_ms, [1000, 3000, 4000])
        self.assertEqual(plan.next_delay_ms, 4000)

    def test_jitter_allowance_rounds_up(self):
        plan = calculate_retry_plan(5000, 333, "1", 333, "10", 2)
        self.assertEqual(plan.delays_ms, [367, 367])

    def test_total_attempts_includes_initial_attempt(self):
        plan = calculate_retry_plan(1000, 1000, "2", 5000, max_retries=3)
        self.assertEqual(plan.retries_allowed, 1)
        self.assertEqual(plan.total_attempts, 2)

    def test_next_delay_is_none_when_all_requested_fit(self):
        plan = calculate_retry_plan(3000, 1000, "2", 5000, max_retries=2)
        self.assertTrue(plan.fits_all_requested)
        self.assertIsNone(plan.next_delay_ms)

    def test_rejects_initial_delay_above_cap(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            calculate_retry_plan(1000, 1001, "2", 1000)

    def test_rejects_multiplier_below_one(self):
        with self.assertRaisesRegex(ValueError, "multiplier"):
            calculate_retry_plan(1000, 100, "0.5", 1000)

    def test_rejects_non_finite_multiplier(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            calculate_retry_plan(1000, 100, "NaN", 1000)

    def test_rejects_jitter_over_100(self):
        with self.assertRaisesRegex(ValueError, "jitter_percent"):
            calculate_retry_plan(1000, 100, "2", 1000, "101")

    def test_text_explains_scope(self):
        output = render_text(calculate_retry_plan(1000, 100, "2", 1000, max_retries=2))
        self.assertIn("initial attempt + retries", output)
        self.assertIn("network latency are not included", output)

    def test_cli_json_output(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--budget-ms", "700", "--initial-delay-ms", "100", "--multiplier", "2", "--max-delay-ms", "500", "--max-retries", "4", "--json"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["delays_ms"], [100, 200, 400])
        self.assertEqual(payload["retries_allowed"], 3)

    def test_cli_rejects_invalid_budget(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--budget-ms", "0", "--initial-delay-ms", "100", "--max-delay-ms", "1000"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("budget_ms", result.stderr)


if __name__ == "__main__":
    unittest.main()
