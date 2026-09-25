import unittest
from datetime import date

from naming_series_tester import SeriesError, parse_fields, preview_series, tokenize


class NamingSeriesTesterTests(unittest.TestCase):
    def test_renders_dates_field_and_counter(self):
        result = preview_series(
            "INV-.branch.-YYYY-MM-#####",
            start=7,
            count=2,
            on_date=date(2026, 9, 25),
            fields={"branch": "MNL"},
        )
        self.assertEqual(result.rendered, ["INV-MNL-2026-09-00007", "INV-MNL-2026-09-00008"])
        self.assertEqual(result.fields_used, ["branch"])

    def test_supports_day_and_short_year(self):
        result = preview_series("DR-YYMMDD-###", on_date=date(2026, 1, 2), count=1)
        self.assertEqual(result.rendered, ["DR-260102-001"])

    def test_requires_exactly_one_counter(self):
        for pattern in ("INV-YYYY", "INV-##-###"):
            with self.subTest(pattern=pattern), self.assertRaises(SeriesError):
                tokenize(pattern)

    def test_rejects_wide_counter(self):
        with self.assertRaises(SeriesError):
            tokenize("INV-##########")

    def test_requires_sample_field(self):
        with self.assertRaisesRegex(SeriesError, "Missing sample"):
            preview_series("INV-.branch.-###")

    def test_rejects_unsafe_field_value(self):
        with self.assertRaises(SeriesError):
            parse_fields(["branch=Manila Office"])

    def test_rejects_invalid_field_syntax(self):
        with self.assertRaises(SeriesError):
            parse_fields(["branch"])

    def test_rejects_unclosed_field_token(self):
        with self.assertRaises(SeriesError):
            tokenize("INV-.branch-###")

    def test_bounds_preview_count(self):
        with self.assertRaises(SeriesError):
            preview_series("INV-###", count=51)

    def test_detects_counter_capacity(self):
        with self.assertRaises(SeriesError):
            preview_series("INV-##", start=99, count=2)

    def test_json_shape_omits_sample_values(self):
        result = preview_series("INV-.branch.-###", fields={"branch": "MNL"}, count=1)
        data = result.as_dict()
        self.assertEqual(data["fields_used"], ["branch"])
        self.assertNotIn("fields", data)


if __name__ == "__main__":
    unittest.main()
