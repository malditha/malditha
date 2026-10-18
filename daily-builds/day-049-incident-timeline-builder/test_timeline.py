import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import timeline


def event(ident, at, kind="note", label="Reviewed sample"):
    return {"id": ident, "at": at, "kind": kind, "label": label}


class TimelineTests(unittest.TestCase):
    def test_orders_instants_and_calculates_gaps(self):
        # Removing UTC normalization or elapsed subtraction must break this.
        data = {"events": [event("b", "2026-10-18T08:02:00+08:00"),
                           event("a", "2026-10-18T00:00:00Z", "detected")]}
        result = timeline.build_timeline(data)
        self.assertEqual([e["id"] for e in result["events"]], ["a", "b"])
        self.assertEqual(result["duration_seconds"], "120")
        self.assertEqual(result["events"][1]["gap_seconds"], "120")

    def test_equal_instants_preserve_input_order(self):
        r = timeline.build_timeline({"events": [event("z", "2026-10-18T08:00:00+08:00"), event("a", "2026-10-18T00:00:00Z")]})
        self.assertEqual([e["id"] for e in r["events"]], ["z", "a"])
        self.assertEqual(r["duration_seconds"], "0")

    def test_fractional_seconds_remain_exact(self):
        r = timeline.build_timeline({"events": [event("a", "2026-10-18T00:00:00.000001Z"), event("b", "2026-10-18T00:00:00.000003Z")]})
        self.assertEqual(r["duration_seconds"], "0.000002")

    def test_single_event_zero_span(self):
        r = timeline.build_timeline({"events": [event("a", "2026-10-18T00:00:00Z")]})
        self.assertEqual(r["count"], 1)
        self.assertEqual(r["events"][0]["elapsed_seconds"], "0")
        self.assertEqual(r["events"][0]["gap_seconds"], "0")

    def test_does_not_mutate_or_copy_unrecognized_fields(self):
        d = {"secret": "DO_NOT_PRINT", "events": [dict(event("a", "2026-10-18T00:00:00Z"), token="DO_NOT_PRINT")]}
        original = copy.deepcopy(d)
        r = timeline.build_timeline(d)
        self.assertEqual(d, original)
        self.assertNotIn("DO_NOT_PRINT", json.dumps(r))

    def test_rejects_naive_invalid_and_excess_precision_timestamps(self):
        for at in ["2026-10-18T00:00:00", "2026-02-30T00:00:00Z", "2026-10-18T00:00:60Z", "2026-10-18T00:00:00.1234567Z", "2026-10-18T00:00:00+15:00"]:
            with self.subTest(at=at), self.assertRaises(ValueError):
                timeline.build_timeline({"events": [event("a", at)]})

    def test_rejects_duplicate_ids(self):
        with self.assertRaises(ValueError):
            timeline.build_timeline({"events": [event("a", "2026-10-18T00:00:00Z")]*2})

    def test_rejects_wrong_shapes_and_event_limits(self):
        for d in [None, [], {}, {"events": []}, {"events": [None]}, {"events": [event(str(i), "2026-10-18T00:00:00Z") for i in range(1001)]}]:
            with self.subTest(shape=type(d).__name__), self.assertRaises(ValueError):
                timeline.build_timeline(d)

    def test_validates_ids_kinds_labels_and_controls(self):
        for change in [{"id": "bad id"}, {"kind": "invented"}, {"label": "x"*161}, {"label": "bad\nline"}, {"id": True}, {"label": "   "}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                timeline.build_timeline({"events": [dict(event("a", "2026-10-18T00:00:00Z"), **change)]})

    def run_cli(self, raw, *args):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"input.json"
            p.write_text(raw)
            return subprocess.run([sys.executable, str(Path(__file__).with_name("timeline.py")), str(p), *args], capture_output=True, text=True)

    def test_cli_json_and_text(self):
        raw = json.dumps({"events": [event("a", "2026-10-18T00:00:00Z")]})
        r = self.run_cli(raw, "--json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["count"], 1)
        self.assertIn("span: 0 seconds", self.run_cli(raw).stdout)

    def test_cli_duplicate_json_keys_and_invalid_input_are_sanitized(self):
        for raw in ['{"events": [], "events": []}', '{"SECRET_VALUE":', 'x'*(1_000_001)]:
            r = self.run_cli(raw, "--json")
            self.assertEqual(r.returncode, 2)
            self.assertEqual(r.stdout, "")
            self.assertEqual(r.stderr.strip(), "Error: invalid or unreadable timeline input")


if __name__ == "__main__":
    unittest.main()
