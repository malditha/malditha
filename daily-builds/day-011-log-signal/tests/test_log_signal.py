import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from log_signal import format_text, main, normalize_message, parse_line, summarize


class LogSignalTests(unittest.TestCase):
    def test_parses_bracketed_level(self):
        signal = parse_line("2026-09-10 08:00:00 [ERROR] connection refused")
        self.assertEqual(signal.level, "ERROR")
        self.assertEqual(signal.signature, "connection refused")

    def test_normalizes_warning(self):
        self.assertEqual(parse_line("WARNING: disk nearly full").level, "WARN")

    def test_returns_none_for_unknown_line(self):
        self.assertIsNone(parse_line("plain diagnostic output"))

    def test_groups_volatile_values(self):
        first = normalize_message("job 123 failed from 10.0.0.1")
        second = normalize_message("job 987 failed from 10.0.0.42")
        self.assertEqual(first, second)
        self.assertEqual(first, "job <n> failed from <ip>")

    def test_summarizes_levels_and_unmatched_lines(self):
        result = summarize(["INFO ready", "ERROR failed", "no level"])
        self.assertEqual(result.total_lines, 3)
        self.assertEqual(result.matched_lines, 2)
        self.assertEqual(result.unmatched_lines, 1)
        self.assertEqual(result.levels, {"ERROR": 1, "INFO": 1})
        self.assertTrue(result.has_errors)

    def test_ranks_most_common_signal_first(self):
        result = summarize(["WARN retry 1", "INFO ready", "WARN retry 2"])
        self.assertEqual(result.top_signals[0], {"level": "WARN", "count": 2, "signature": "retry <n>"})

    def test_top_limit_is_respected(self):
        result = summarize(["INFO alpha", "WARN beta", "ERROR gamma"], top=2)
        self.assertEqual(len(result.top_signals), 2)

    def test_text_report_contains_status(self):
        self.assertIn("Status: CLEAR", format_text(summarize(["INFO ready"])))

    def test_main_emits_json_and_error_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "app.log"
            path.write_text("ERROR task 42 failed\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main([str(path), "--json"])
            self.assertEqual(code, 1)
            self.assertTrue(json.loads(output.getvalue())["has_errors"])

    def test_no_fail_overrides_error_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "app.log"
            path.write_text("FATAL unavailable\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                code = main([str(path), "--no-fail"])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
