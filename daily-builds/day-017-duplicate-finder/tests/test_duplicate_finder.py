import json
import tempfile
import unittest
from pathlib import Path

from duplicate_finder import human_size, main, report_as_json, report_as_text, scan_directory


class DuplicateFinderTests(unittest.TestCase):
    def test_groups_only_byte_identical_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            (root / "same-size.txt").write_text("diff", encoding="utf-8")
            report = scan_directory(root)
        self.assertEqual(1, len(report.duplicate_groups))
        self.assertEqual(("a.txt", "b.txt"), report.duplicate_groups[0].files)

    def test_scans_nested_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            (root / "one.bin").write_bytes(b"copy")
            (root / "nested" / "two.bin").write_bytes(b"copy")
            report = scan_directory(root)
        self.assertEqual(("nested/two.bin", "one.bin"), report.duplicate_groups[0].files)

    def test_reclaimable_bytes_counts_extra_copies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("a", "b", "c"):
                (root / name).write_bytes(b"12345")
            report = scan_directory(root)
        self.assertEqual(10, report.reclaimable_bytes)

    def test_unique_files_produce_no_groups(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a").write_bytes(b"a")
            (root / "b").write_bytes(b"bb")
            report = scan_directory(root)
        self.assertEqual((), report.duplicate_groups)

    def test_symlink_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.write_text("safe", encoding="utf-8")
            try:
                (root / "link").symlink_to(target)
            except OSError:
                self.skipTest("symlinks unavailable")
            report = scan_directory(root)
        self.assertEqual(1, report.skipped_symlinks)
        self.assertEqual(1, report.files_scanned)

    def test_json_contains_files_and_totals(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a").write_bytes(b"same")
            (root / "b").write_bytes(b"same")
            payload = json.loads(report_as_json(scan_directory(root)))
        self.assertEqual(2, payload["files_scanned"])
        self.assertEqual(["a", "b"], payload["duplicate_groups"][0]["files"])

    def test_text_report_has_safety_notice(self):
        with tempfile.TemporaryDirectory() as temp:
            report = scan_directory(Path(temp))
        self.assertIn("Read-only report", report_as_text(report))

    def test_human_size(self):
        self.assertEqual("999 B", human_size(999))
        self.assertEqual("1.0 KiB", human_size(1024))

    def test_main_rejects_non_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(2, main([str(Path(temp) / "missing")]))


if __name__ == "__main__":
    unittest.main()
