import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_to_json_converter import convert_csv, render_json


SCRIPT = Path(__file__).with_name("csv_to_json_converter.py")


class CsvToJsonConverterTests(unittest.TestCase):
    def test_converts_quoted_commas_and_preserves_strings(self):
        rows = convert_csv('name,postal_code,note\nAna,00123,"Quezon City, PH"\n')
        self.assertEqual(rows, [{"name": "Ana", "postal_code": "00123", "note": "Quezon City, PH"}])

    def test_preserves_empty_fields(self):
        self.assertEqual(convert_csv("name,email\nMia,\n"), [{"name": "Mia", "email": ""}])

    def test_accepts_utf8_bom(self):
        self.assertEqual(convert_csv("\ufeffname,city\nLia,Manila\n"), [{"name": "Lia", "city": "Manila"}])

    def test_rejects_blank_header(self):
        with self.assertRaisesRegex(ValueError, "header 2 is blank"):
            convert_csv("name,\nAna,value\n")

    def test_rejects_duplicate_header(self):
        with self.assertRaisesRegex(ValueError, "duplicate header: name"):
            convert_csv("name,name\nAna,Santos\n")

    def test_rejects_short_row(self):
        with self.assertRaisesRegex(ValueError, "row 2 has 1 fields; expected 2"):
            convert_csv("name,city\nAna\n")

    def test_rejects_long_row(self):
        with self.assertRaisesRegex(ValueError, "row 2 has 3 fields; expected 2"):
            convert_csv("name,city\nAna,Manila,extra\n")

    def test_rejects_too_many_columns(self):
        with self.assertRaisesRegex(ValueError, "more than 2 columns"):
            convert_csv("a,b,c\n1,2,3\n", max_columns=2)

    def test_rejects_too_many_rows(self):
        with self.assertRaisesRegex(ValueError, "more than 1 data rows"):
            convert_csv("name\nAna\nMia\n", max_rows=1)

    def test_renders_json_lines(self):
        output = render_json([{"name": "Ana"}, {"name": "Mia"}], json_lines=True)
        self.assertEqual(output, '{"name": "Ana"}\n{"name": "Mia"}')

    def test_cli_converts_file_to_json_array(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "people.csv"
            source.write_text("name,active\nAna,true\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                check=True, capture_output=True, text=True,
            )
        self.assertEqual(json.loads(result.stdout), [{"name": "Ana", "active": "true"}])

    def test_cli_returns_error_for_invalid_csv(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], input="name,name\nAna,Santos\n",
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate header", result.stderr)


if __name__ == "__main__":
    unittest.main()
