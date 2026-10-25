import unittest
from datetime import datetime, timezone
from cron_schedule_previewer import CronError, parse_expression, parse_start, preview, format_text

START=datetime(2026,10,25,0,0,tzinfo=timezone.utc)
class Tests(unittest.TestCase):
    def test_daily(self):
        r=preview("0 9 * * *","Asia/Manila",START,2)
        self.assertEqual([x["local"][11:16] for x in r["runs"]],["09:00","09:00"])
    def test_list_and_range(self):
        r=preview("0 9-10 * * 1,2","UTC",START,3)
        self.assertEqual([x["local"][11:16] for x in r["runs"]],["09:00","10:00","09:00"])
    def test_step(self):
        r=preview("*/15 * * * *","UTC",START,2)
        self.assertEqual([x["local"][14:16] for x in r["runs"]],["15","30"])
    def test_day_of_month(self):
        self.assertIn("-11-01T",preview("0 0 1 * *","UTC",START,1)["runs"][0]["local"])
    def test_dom_or_dow(self):
        r=preview("0 0 1 * 1","UTC",START,2)
        self.assertEqual([x["local"][:10] for x in r["runs"]],["2026-10-26","2026-11-01"])
    def test_timezone_offset(self):
        run=preview("0 9 * * *","Asia/Manila",START,1)["runs"][0]
        self.assertTrue(run["utc"].endswith("+00:00"))
    def test_bad_field_count(self):
        with self.assertRaises(CronError): parse_expression("* * * *")
    def test_out_of_range(self):
        with self.assertRaises(CronError): parse_expression("60 * * * *")
    def test_start_requires_offset(self):
        with self.assertRaises(CronError): parse_start("2026-10-25T00:00:00")
    def test_text(self):
        self.assertIn("Cron Schedule Preview",format_text(preview("0 9 * * *","UTC",START,1)))
if __name__=="__main__": unittest.main()
