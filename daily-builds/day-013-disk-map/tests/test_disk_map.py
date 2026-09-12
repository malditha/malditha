import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from disk_map import file_group, format_report, human_size, main, scan_directory


class DiskMapTests(unittest.TestCase):
    def make_tree(self, root: Path) -> None:
        (root / "assets").mkdir()
        (root / "notes.txt").write_bytes(b"a" * 10)
        (root / "README").write_bytes(b"b" * 5)
        (root / "assets" / "hero.PNG").write_bytes(b"c" * 25)
        (root / "assets" / "icon.png").write_bytes(b"d" * 15)

    def test_human_size_formats_binary_units(self):
        self.assertEqual(human_size(999), "999 B")
        self.assertEqual(human_size(1536), "1.5 KB")
        self.assertEqual(human_size(2 * 1024 * 1024), "2.0 MB")

    def test_file_group_normalizes_case(self):
        self.assertEqual(file_group(Path("PHOTO.PNG")), ".png")
        self.assertEqual(file_group(Path("LICENSE")), "[no extension]")

    def test_scan_counts_files_and_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_tree(root)
            report = scan_directory(root)
            self.assertEqual(report["files"], 4)
            self.assertEqual(report["bytes"], 55)

    def test_extensions_are_grouped_and_sorted_by_size(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_tree(root)
            groups = scan_directory(root)["extensions"]
            self.assertEqual(groups[0], {"extension": ".png", "files": 2, "bytes": 40})
            self.assertEqual(groups[1]["extension"], ".txt")

    def test_largest_files_respect_top_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_tree(root)
            largest = scan_directory(root, top=2)["largest"]
            self.assertEqual([item["path"] for item in largest], ["assets/hero.PNG", "assets/icon.png"])

    def test_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            self.make_tree(root)
            (Path(outside) / "private.txt").write_bytes(b"secret")
            try:
                (root / "outside").symlink_to(outside, target_is_directory=True)
                (root / "linked.txt").symlink_to(Path(outside) / "private.txt")
            except OSError:
                self.skipTest("symlinks are unavailable")
            report = scan_directory(root)
            self.assertEqual(report["files"], 4)
            self.assertNotIn("outside/private.txt", [item["path"] for item in report["largest"]])

    def test_empty_directory_has_clear_report(self):
        with tempfile.TemporaryDirectory() as temp:
            text = format_report(scan_directory(Path(temp)))
            self.assertIn("0 files", text)
            self.assertIn("No files found", text)

    def test_invalid_top_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                scan_directory(Path(temp), top=0)

    def test_missing_directory_returns_error(self):
        self.assertEqual(main(["does-not-exist"]), 2)

    def test_json_cli_output_is_parseable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_tree(root)
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main([str(root), "--top", "1", "--json"]), 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["files"], 4)
            self.assertEqual(len(data["largest"]), 1)


if __name__ == "__main__":
    unittest.main()
