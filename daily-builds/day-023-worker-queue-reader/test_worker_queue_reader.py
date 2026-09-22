import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import worker_queue_reader as tool


def sample():
    return {
        "captured_at": "2026-09-22T08:00:00+08:00",
        "queues": [
            {"name": "default", "pending": 2, "oldest_enqueued_at": "2026-09-21T23:58:00Z"},
            {"name": "long", "pending": 1, "oldest_enqueued_at": "2026-09-21T23:40:00Z"},
            {"name": "short", "pending": 0},
        ],
        "workers": [
            {"name": "worker-1", "status": "active", "queues": ["default", "short"]},
            {"name": "worker-2", "status": "offline", "queues": ["long"]},
        ],
        "redis_password": "must-not-appear",
    }


class WorkerQueueReaderTests(unittest.TestCase):
    def test_time_requires_timezone(self):
        with self.assertRaises(tool.QueueError):
            tool.parse_time("2026-09-22T08:00:00")

    def test_reports_backlog_stale_and_uncovered(self):
        report = tool.analyze(sample(), stale_after=300)
        states = {row["queue"]: row["status"] for row in report["queues"]}
        self.assertEqual(states, {"default": "backlog", "long": "uncovered", "short": "clear"})
        self.assertTrue(report["attention_required"])

    def test_stale_queue_with_worker_is_flagged(self):
        data = sample()
        data["workers"][0]["queues"].append("long")
        self.assertEqual(tool.analyze(data)["queues"][1]["status"], "stale")

    def test_only_active_workers_count_toward_coverage(self):
        report = tool.analyze(sample())
        self.assertEqual(report["active_worker_count"], 1)
        self.assertEqual(report["queues"][1]["active_workers"], 0)

    def test_total_pending_is_summed(self):
        self.assertEqual(tool.analyze(sample())["total_pending"], 3)

    def test_report_omits_unapproved_values(self):
        self.assertNotIn("must-not-appear", json.dumps(tool.analyze(sample())))

    def test_negative_pending_is_rejected(self):
        data = sample()
        data["queues"][0]["pending"] = -1
        with self.assertRaises(tool.QueueError):
            tool.analyze(data)

    def test_invalid_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(tool.QueueError):
                tool.load_snapshot(path)

    def test_cli_returns_one_when_attention_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            path.write_text(json.dumps(sample()), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = tool.main([str(path)])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
