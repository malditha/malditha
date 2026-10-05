import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from rate_limit_visualizer import analyze_rate_limit, load_timestamps, render_text


SCRIPT = Path(__file__).with_name("rate_limit_visualizer.py")


class RateLimitVisualizerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 5, 0, 0, 30, tzinfo=timezone.utc)

    def test_counts_requests_inside_fixed_window(self):
        report = analyze_rate_limit(
            ["2026-10-05T00:00:01Z", "2026-10-05T00:00:20Z", "2026-10-04T23:59:59Z"],
            limit=5, window_seconds=60, now=self.now,
        )
        self.assertEqual(report.used, 2)
        self.assertEqual(report.remaining, 3)

    def test_request_on_window_start_is_included(self):
        report = analyze_rate_limit(["2026-10-05T00:00:00Z"], 2, 60, self.now)
        self.assertEqual(report.used, 1)

    def test_future_request_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "future"):
            analyze_rate_limit(["2026-10-05T00:00:31Z"], 5, 60, self.now)

    def test_blocked_status_at_limit(self):
        report = analyze_rate_limit(
            ["2026-10-05T00:00:01Z", "2026-10-05T00:00:02Z"], 2, 60, self.now
        )
        self.assertEqual(report.status, "blocked")
        self.assertEqual(report.remaining, 0)

    def test_warning_status_at_eighty_percent(self):
        timestamps = [f"2026-10-05T00:00:0{i}Z" for i in range(1, 5)]
        report = analyze_rate_limit(timestamps, 5, 60, self.now)
        self.assertEqual(report.status, "warning")

    def test_healthy_status_below_eighty_percent(self):
        report = analyze_rate_limit(["2026-10-05T00:00:01Z"], 5, 60, self.now)
        self.assertEqual(report.status, "healthy")

    def test_reset_uses_fixed_window_boundary(self):
        report = analyze_rate_limit([], 5, 60, self.now)
        self.assertEqual(report.reset_at, "2026-10-05T00:01:00Z")
        self.assertEqual(report.seconds_until_reset, 30)

    def test_bar_has_fixed_width(self):
        report = analyze_rate_limit(["2026-10-05T00:00:01Z"], 4, 60, self.now, bar_width=10)
        self.assertEqual(report.bar, "██░░░░░░░░")
        self.assertEqual(len(report.bar), 10)

    def test_load_timestamps_accepts_only_array_of_strings(self):
        with self.assertRaisesRegex(ValueError, "array of timestamp strings"):
            load_timestamps('{"timestamp":"2026-10-05T00:00:00Z"}')

    def test_rejects_naive_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            analyze_rate_limit(["2026-10-05T00:00:01"], 5, 60, self.now)

    def test_text_states_fixed_window_scope(self):
        output = render_text(analyze_rate_limit([], 5, 60, self.now))
        self.assertIn("Fixed-window model", output)
        self.assertIn("does not contact an API", output)

    def test_cli_json_output(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--limit", "5", "--window-seconds", "60",
             "--now", "2026-10-05T00:00:30Z", "--timestamps-json",
             '["2026-10-05T00:00:01Z","2026-10-05T00:00:20Z"]', "--json"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["used"], 2)
        self.assertEqual(payload["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
