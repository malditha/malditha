import unittest
from datetime import datetime, timezone

from backup_freshness_checker import InputError, evaluate, evaluate_all, render_text


NOW = datetime(2026, 9, 27, 0, 0, tzinfo=timezone.utc)
BASE = {"site": "demo.local", "latest_backup_at": "2026-09-26T18:00:00Z", "maximum_age_hours": 24}


class BackupFreshnessCheckerTests(unittest.TestCase):
    def test_fresh_backup(self):
        result = evaluate(BASE, NOW)
        self.assertEqual(result.status, "fresh")
        self.assertEqual(result.age_hours, 6)

    def test_threshold_boundary_is_fresh(self):
        result = evaluate({**BASE, "latest_backup_at": "2026-09-26T00:00:00Z"}, NOW)
        self.assertEqual(result.status, "fresh")

    def test_stale_backup(self):
        result = evaluate({**BASE, "latest_backup_at": "2026-09-25T00:00:00Z"}, NOW)
        self.assertEqual(result.status, "stale")

    def test_missing_backup(self):
        result = evaluate({**BASE, "latest_backup_at": None}, NOW)
        self.assertEqual(result.status, "missing")
        self.assertIsNone(result.age_hours)

    def test_future_backup(self):
        result = evaluate({**BASE, "latest_backup_at": "2026-09-28T00:00:00Z"}, NOW)
        self.assertEqual(result.status, "future")

    def test_small_clock_skew_is_zero_age(self):
        result = evaluate({**BASE, "latest_backup_at": "2026-09-27T00:04:00Z"}, NOW)
        self.assertEqual(result.status, "fresh")
        self.assertEqual(result.age_hours, 0)

    def test_requires_timezone(self):
        with self.assertRaisesRegex(InputError, "timezone"):
            evaluate({**BASE, "latest_backup_at": "2026-09-26T18:00:00"}, NOW)

    def test_rejects_unknown_sensitive_fields(self):
        with self.assertRaisesRegex(InputError, "Unsupported"):
            evaluate({**BASE, "database_password": "secret"}, NOW)

    def test_rejects_duplicate_sites_case_insensitively(self):
        with self.assertRaisesRegex(InputError, "duplicate"):
            evaluate_all([BASE, {**BASE, "site": "DEMO.LOCAL"}], NOW)

    def test_results_are_sorted(self):
        results = evaluate_all([{**BASE, "site": "z.local"}, {**BASE, "site": "a.local"}], NOW)
        self.assertEqual([item.site for item in results], ["a.local", "z.local"])

    def test_text_has_non_mutating_notice(self):
        self.assertIn("no backup archive was opened", render_text([evaluate(BASE, NOW)], NOW))


if __name__ == "__main__":
    unittest.main()
