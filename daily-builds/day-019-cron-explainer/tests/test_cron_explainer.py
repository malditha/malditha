import unittest
from datetime import datetime

from cron_explainer import CronError, build_report, next_matches, parse


class CronExplainerTests(unittest.TestCase):
    def test_requires_five_fields(self):
        with self.assertRaisesRegex(CronError, "exactly five fields"):
            parse("0 9 * *")

    def test_rejects_out_of_range_values(self):
        with self.assertRaisesRegex(CronError, "outside 0-59"):
            parse("60 9 * * *")

    def test_rejects_zero_step(self):
        with self.assertRaisesRegex(CronError, "greater than zero"):
            parse("*/0 9 * * *")

    def test_expands_ranges_lists_steps_and_names(self):
        schedule = parse("*/15 9-10 * jan,mar mon-fri")
        self.assertEqual(schedule.values[0], frozenset({0, 15, 30, 45}))
        self.assertEqual(schedule.values[1], frozenset({9, 10}))
        self.assertEqual(schedule.values[3], frozenset({1, 3}))
        self.assertEqual(schedule.values[4], frozenset({1, 2, 3, 4, 5}))

    def test_sunday_seven_is_normalized_to_zero(self):
        self.assertEqual(parse("0 9 * * 7").values[4], frozenset({0}))

    def test_next_matches_weekday_schedule(self):
        schedule = parse("0 9 * * 1-5")
        matches = next_matches(schedule, datetime(2026, 9, 18, 9, 0), count=3)
        self.assertEqual(
            matches,
            [
                datetime(2026, 9, 21, 9, 0),
                datetime(2026, 9, 22, 9, 0),
                datetime(2026, 9, 23, 9, 0),
            ],
        )

    def test_day_of_month_or_day_of_week_semantics(self):
        schedule = parse("0 9 20 * 1")
        self.assertTrue(schedule.matches(datetime(2026, 9, 20, 9, 0)))
        self.assertTrue(schedule.matches(datetime(2026, 9, 21, 9, 0)))
        self.assertFalse(schedule.matches(datetime(2026, 9, 22, 9, 0)))

    def test_report_is_serializable_and_deterministic(self):
        report = build_report("30 8 * * mon-fri", datetime(2026, 9, 18, 9, 0), 2)
        self.assertEqual(report["next_matches"], ["2026-09-21T08:30", "2026-09-22T08:30"])
        self.assertEqual(report["fields"][0]["field"], "minute")

    def test_count_is_bounded(self):
        with self.assertRaisesRegex(CronError, "between 1 and 20"):
            next_matches(parse("* * * * *"), datetime(2026, 9, 18), count=21)


if __name__ == "__main__":
    unittest.main()
