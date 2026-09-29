import copy
import json
import tempfile
import unittest
from pathlib import Path

import patch_log_formatter as formatter


def record(**overrides):
    item = {
        "patch": "frappe.patches.v15_0.sample_patch",
        "status": "success",
        "started_at": "2026-09-29T08:00:00+08:00",
        "finished_at": "2026-09-29T08:00:01.250+08:00",
    }
    item.update(overrides)
    return item


class PatchLogFormatterTests(unittest.TestCase):
    def test_builds_counts_and_duration(self):
        report = formatter.build_report([record(), record(patch="custom.cleanup", status="skipped")])
        self.assertEqual(report["summary"], {"total": 2, "success": 1, "failed": 0, "skipped": 1, "total_duration_ms": 2500})

    def test_normalizes_timestamps_to_utc(self):
        report = formatter.build_report([record()])
        self.assertEqual(report["records"][0]["started_at"], "2026-09-29T00:00:00Z")

    def test_sorts_chronologically_then_by_patch(self):
        payload = [record(patch="z.patch"), record(patch="a.patch"), record(patch="earlier.patch", started_at="2026-09-28T23:59:00Z", finished_at="2026-09-28T23:59:01Z")]
        names = [item["patch"] for item in formatter.build_report(payload)["records"]]
        self.assertEqual(names, ["earlier.patch", "a.patch", "z.patch"])

    def test_does_not_mutate_input(self):
        payload = [record()]
        original = copy.deepcopy(payload)
        formatter.build_report(payload)
        self.assertEqual(payload, original)

    def test_formats_failure_in_text(self):
        report = formatter.build_report([record(status="failed")])
        self.assertIn("[FAILED ", formatter.format_text(report))

    def test_rejects_non_array(self):
        with self.assertRaises(formatter.InputError):
            formatter.build_report({})

    def test_rejects_more_than_limit(self):
        with self.assertRaises(formatter.InputError):
            formatter.build_report([record()] * 201)

    def test_rejects_unknown_fields(self):
        with self.assertRaises(formatter.InputError):
            formatter.build_report([record(traceback="secret")])

    def test_rejects_bad_identifier(self):
        with self.assertRaises(formatter.InputError):
            formatter.build_report([record(patch="patch name; rm")])

    def test_rejects_naive_timestamp(self):
        with self.assertRaises(formatter.InputError):
            formatter.build_report([record(started_at="2026-09-29T08:00:00")])

    def test_rejects_reverse_duration(self):
        with self.assertRaises(formatter.InputError):
            formatter.build_report([record(finished_at="2026-09-28T23:59:59Z")])

    def test_cli_returns_one_for_failed_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.json"
            path.write_text(json.dumps([record(status="failed")]), encoding="utf-8")
            self.assertEqual(formatter.main([str(path), "--format", "json"]), 1)


if __name__ == "__main__":
    unittest.main()
