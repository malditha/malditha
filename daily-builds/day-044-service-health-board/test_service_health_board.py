import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from service_health_board import BoardError, build_board, format_text, load_snapshot


NOW = "2026-10-13T00:00:00Z"


class ServiceHealthBoardTests(unittest.TestCase):
    def test_healthy_service(self):
        board = build_board({"observed_at": NOW, "services": [{"name": "web", "state": "up", "last_checked_at": NOW}]}, 15)
        self.assertEqual(board["overall"], "healthy")

    def test_stale_overrides_up(self):
        board = build_board({"observed_at": NOW, "services": [{"name": "worker", "state": "up", "last_checked_at": "2026-10-12T23:30:00Z"}]}, 15)
        self.assertEqual(board["services"][0]["status"], "stale")

    def test_down_has_highest_priority(self):
        services = [{"name": "a", "state": "degraded", "last_checked_at": NOW}, {"name": "b", "state": "down", "last_checked_at": NOW}]
        self.assertEqual(build_board({"observed_at": NOW, "services": services}, 15)["overall"], "down")

    def test_unknown_rolls_up(self):
        board = build_board({"observed_at": NOW, "services": [{"name": "cache", "state": "unknown", "last_checked_at": NOW}]}, 15)
        self.assertEqual(board["overall"], "unknown")

    def test_sorts_by_name(self):
        services = [{"name": "Worker", "state": "up", "last_checked_at": NOW}, {"name": "api", "state": "up", "last_checked_at": NOW}]
        names = [item["name"] for item in build_board({"observed_at": NOW, "services": services}, 15)["services"]]
        self.assertEqual(names, ["api", "Worker"])

    def test_private_extra_fields_are_omitted(self):
        service = {"name": "db", "state": "up", "last_checked_at": NOW, "token": "never-report", "note": "private"}
        rendered = json.dumps(build_board({"observed_at": NOW, "services": [service]}, 15))
        self.assertNotIn("never-report", rendered)
        self.assertNotIn("private", rendered)

    def test_rejects_future_check(self):
        with self.assertRaises(BoardError):
            build_board({"observed_at": NOW, "services": [{"name": "web", "state": "up", "last_checked_at": "2026-10-13T00:01:00Z"}]}, 15)

    def test_rejects_duplicate_names(self):
        services = [{"name": "web", "state": "up", "last_checked_at": NOW}] * 2
        with self.assertRaises(BoardError):
            build_board({"observed_at": NOW, "services": services}, 15)

    def test_rejects_more_than_100_services(self):
        services = [{"name": f"svc-{i}", "state": "up", "last_checked_at": NOW} for i in range(101)]
        with self.assertRaises(BoardError):
            build_board({"observed_at": NOW, "services": services}, 15)

    def test_text_contains_summary_without_values(self):
        board = build_board({"observed_at": NOW, "services": [{"name": "web", "state": "up", "last_checked_at": NOW, "latency_ms": 42}]}, 15)
        self.assertIn("Overall: HEALTHY", format_text(board))
        self.assertIn("42 ms", format_text(board))

    def test_loader_rejects_oversized_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large.json"
            path.write_bytes(b" " * (2 * 1024 * 1024 + 1))
            with self.assertRaises(BoardError):
                load_snapshot(path)

    def test_cli_returns_one_when_review_needed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            path.write_text(json.dumps({"observed_at": NOW, "services": [{"name": "web", "state": "down", "last_checked_at": NOW}]}))
            result = subprocess.run([sys.executable, "service_health_board.py", str(path), "--json"], cwd=Path(__file__).parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["overall"], "down")


if __name__ == "__main__":
    unittest.main()
