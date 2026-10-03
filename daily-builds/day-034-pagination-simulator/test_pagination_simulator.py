import json
import subprocess
import sys
import unittest
from pathlib import Path

from pagination_simulator import PaginationError, navigation_window, render_text, simulate


class PaginationSimulatorTests(unittest.TestCase):
    def test_exact_multiple_has_expected_page_count(self):
        result = simulate(100, 20, 3)
        self.assertEqual(result.total_pages, 5)
        self.assertEqual((result.first_item, result.last_item), (41, 60))
        self.assertEqual((result.offset, result.limit), (40, 20))

    def test_partial_last_page_is_clamped_to_total(self):
        result = simulate(101, 20, 6)
        self.assertEqual((result.first_item, result.last_item), (101, 101))
        self.assertEqual(result.next_page, None)

    def test_first_page_has_no_previous_page(self):
        result = simulate(40, 10, 1)
        self.assertIsNone(result.previous_page)
        self.assertEqual(result.next_page, 2)

    def test_middle_page_has_previous_and_next(self):
        result = simulate(40, 10, 2)
        self.assertEqual((result.previous_page, result.next_page), (1, 3))

    def test_empty_collection_has_no_item_range_or_navigation(self):
        result = simulate(0, 25, 1)
        self.assertEqual(result.total_pages, 0)
        self.assertIsNone(result.first_item)
        self.assertIsNone(result.last_item)
        self.assertEqual(result.navigation, [])

    def test_small_page_set_shows_every_page(self):
        self.assertEqual(navigation_window(2, 4, 7), [1, 2, 3, 4])

    def test_middle_window_uses_two_ellipses(self):
        self.assertEqual(navigation_window(10, 20, 7), [1, "…", 8, 9, 10, 11, 12, "…", 20])

    def test_ending_window_keeps_last_pages_visible(self):
        self.assertEqual(navigation_window(20, 20, 7), [1, "…", 15, 16, 17, 18, 19, 20])

    def test_rejects_page_beyond_last_page(self):
        with self.assertRaisesRegex(PaginationError, "current page"):
            simulate(10, 5, 3)

    def test_rejects_booleans_as_integer_inputs(self):
        with self.assertRaisesRegex(PaginationError, "total items"):
            simulate(True, 10, 1)

    def test_text_report_contains_request_bounds(self):
        report = render_text(simulate(63, 10, 4))
        self.assertIn("Range: 31-40", report)
        self.assertIn("Request: offset=30 limit=10", report)

    def test_cli_json_output_is_machine_readable(self):
        result = subprocess.run(
            [sys.executable, "pagination_simulator.py", "--total-items", "63", "--page-size", "10", "--page", "7", "--json"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["first_item"], 61)
        self.assertEqual(payload["last_item"], 63)
        self.assertIsNone(payload["next_page"])


if __name__ == "__main__":
    unittest.main()
