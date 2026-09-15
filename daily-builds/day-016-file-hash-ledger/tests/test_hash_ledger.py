import json
import tempfile
import unittest
from pathlib import Path

from hash_ledger import GENESIS, current_status, hash_file, read_ledger, record, verify_entries


class HashLedgerTests(unittest.TestCase):
    def test_hash_file_matches_known_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "a.txt"
            path.write_text("hello", encoding="utf-8")
            self.assertEqual(hash_file(path), "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_record_creates_genesis_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "a.txt"
            source.write_text("one", encoding="utf-8")
            entries = record(root / "ledger.jsonl", [source], "2026-09-15T00:00:00+00:00")
            self.assertEqual(entries[0]["previous"], GENESIS)
            self.assertEqual(entries[0]["index"], 1)

    def test_second_record_links_to_previous_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "a.txt"
            ledger = root / "ledger.jsonl"
            source.write_text("one", encoding="utf-8")
            first = record(ledger, [source], "2026-09-15T00:00:00+00:00")[0]
            source.write_text("two", encoding="utf-8")
            second = record(ledger, [source], "2026-09-15T01:00:00+00:00")[0]
            self.assertEqual(second["previous"], first["entry_hash"])
            self.assertEqual(second["index"], 2)

    def test_verify_accepts_intact_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "a.txt"
            source.write_text("safe", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            record(ledger, [source], "2026-09-15T00:00:00+00:00")
            self.assertTrue(verify_entries(read_ledger(ledger))[0])

    def test_verify_detects_modified_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "a.txt"
            source.write_text("safe", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            record(ledger, [source], "2026-09-15T00:00:00+00:00")
            entry = json.loads(ledger.read_text(encoding="utf-8"))
            entry["size"] = 999
            self.assertFalse(verify_entries([entry])[0])

    def test_record_refuses_tampered_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "a.txt"
            source.write_text("safe", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            record(ledger, [source], "2026-09-15T00:00:00+00:00")
            ledger.write_text(ledger.read_text(encoding="utf-8").replace('"size": 4', '"size": 5'), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing to append"):
                record(ledger, [source])

    def test_current_status_reports_changed_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = root / "a.txt", root / "b.txt"
            a.write_text("a", encoding="utf-8")
            b.write_text("b", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            old = Path.cwd()
            try:
                import os
                os.chdir(root)
                record(ledger, [Path("a.txt"), Path("b.txt")], "2026-09-15T00:00:00+00:00")
            finally:
                os.chdir(old)
            a.write_text("changed", encoding="utf-8")
            b.unlink()
            statuses = current_status(read_ledger(ledger), root)
            self.assertEqual(statuses, [{"path": "a.txt", "status": "changed"}, {"path": "b.txt", "status": "missing"}])

    def test_read_ledger_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            ledger.write_text("{broken}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 1"):
                read_ledger(ledger)

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "a.txt"
            link = root / "link.txt"
            source.write_text("safe", encoding="utf-8")
            try:
                link.symlink_to(source)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "regular file"):
                record(root / "ledger.jsonl", [link])


if __name__ == "__main__":
    unittest.main()
