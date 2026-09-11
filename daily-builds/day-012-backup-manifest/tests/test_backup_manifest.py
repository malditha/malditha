import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backup_manifest import build_manifest, format_verification, load_manifest, main, sha256_file, verify_manifest


class BackupManifestTests(unittest.TestCase):
    def make_backup(self, root: Path) -> None:
        (root / "nested").mkdir()
        (root / "alpha.txt").write_text("alpha\n", encoding="utf-8")
        (root / "nested" / "beta.bin").write_bytes(b"beta\x00")

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "value.txt"
            path.write_text("abc", encoding="utf-8")
            self.assertEqual(sha256_file(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_manifest_uses_stable_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            manifest = build_manifest(root)
            self.assertEqual([entry["path"] for entry in manifest["files"]], ["alpha.txt", "nested/beta.bin"])

    def test_manifest_totals(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            manifest = build_manifest(root)
            self.assertEqual(manifest["file_count"], 2)
            self.assertEqual(manifest["total_bytes"], 11)

    def test_unchanged_backup_verifies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            report = verify_manifest(root, build_manifest(root))
            self.assertTrue(report["ok"])

    def test_changed_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            manifest = build_manifest(root)
            (root / "alpha.txt").write_text("changed", encoding="utf-8")
            self.assertEqual(verify_manifest(root, manifest)["changed"], ["alpha.txt"])

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            manifest = build_manifest(root)
            (root / "alpha.txt").unlink()
            self.assertEqual(verify_manifest(root, manifest)["missing"], ["alpha.txt"])

    def test_unexpected_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            manifest = build_manifest(root)
            (root / "extra.txt").write_text("extra", encoding="utf-8")
            self.assertEqual(verify_manifest(root, manifest)["unexpected"], ["extra.txt"])

    def test_manifest_file_can_be_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_backup(root)
            manifest_path = root / "manifest.json"
            manifest_path.write_text("{}", encoding="utf-8")
            manifest = build_manifest(root, excluded=[manifest_path])
            self.assertNotIn("manifest.json", [entry["path"] for entry in manifest["files"]])

    def test_rejects_unsupported_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text('{"version": 99}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_main_create_then_verify(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "backup"
            root.mkdir()
            self.make_backup(root)
            manifest_path = Path(temp) / "manifest.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["create", str(root), "--output", str(manifest_path)]), 0)
                self.assertEqual(main(["verify", str(root), str(manifest_path), "--json"]), 0)
            self.assertEqual(json.loads(manifest_path.read_text())["file_count"], 2)

    def test_text_report_lists_differences(self):
        text = format_verification({"ok": False, "checked": 1, "missing": ["a"], "changed": [], "unexpected": []})
        self.assertIn("DIFFERENCES FOUND", text)
        self.assertIn("  - a", text)


if __name__ == "__main__":
    unittest.main()
