import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import drift

CHECKS = ("runtime_version", "os_release", "dependency_lock", "schema_revision", "timezone", "feature_set")


def snapshot():
    return {"checks": {key: "synthetic-v1" for key in CHECKS}}


class DriftTests(unittest.TestCase):
    def test_all_six_matches_are_aligned(self):
        result = drift.compare(snapshot(), snapshot())
        self.assertEqual(result["status"], "aligned")
        self.assertEqual(result["counts"], {"match": 6, "drift": 0, "unverified": 0})
        self.assertEqual([r["check"] for r in result["checks"]], list(CHECKS))

    def test_changed_observation_is_drift(self):
        candidate = snapshot()
        candidate["checks"]["runtime_version"] = "synthetic-v2"
        result = drift.compare(snapshot(), candidate)
        self.assertEqual(result["status"], "drift")
        self.assertEqual(result["checks"][0]["status"], "drift")
        self.assertEqual(result["counts"]["match"], 5)

    def test_missing_candidate_is_unverified(self):
        candidate = snapshot()
        del candidate["checks"]["timezone"]
        result = drift.compare(snapshot(), candidate)
        self.assertEqual(result["status"], "unverified")
        self.assertEqual(result["checks"][4]["reason"], "missing_candidate")

    def test_missing_baseline_and_both_are_distinct(self):
        result = drift.compare({"checks": {}}, snapshot())
        self.assertTrue(all(r["reason"] == "missing_baseline" for r in result["checks"]))
        result = drift.compare({"checks": {}}, {"checks": {}})
        self.assertTrue(all(r["reason"] == "missing_both" for r in result["checks"]))
        self.assertEqual(result["counts"]["unverified"], 6)

    def test_drift_takes_precedence_over_missing_evidence(self):
        c = snapshot()
        c["checks"]["runtime_version"] = "v2"
        del c["checks"]["timezone"]
        r = drift.compare(snapshot(), c)
        self.assertEqual(r["status"], "drift")
        self.assertEqual(r["counts"], {"match": 4, "drift": 1, "unverified": 1})

    def test_comparison_is_exact_not_version_or_whitespace_normalization(self):
        for value in ["SYNTHETIC-v1", "synthetic-v1 "]:
            c = snapshot()
            c["checks"]["runtime_version"] = value
            self.assertEqual(drift.compare(snapshot(), c)["status"], "drift")

    def test_no_values_or_unknown_fields_are_reported_or_mutated(self):
        b = snapshot()
        b["checks"]["runtime_version"] = "PRIVATE_CANARY"
        b["checks"]["token"] = "PRIVATE_CANARY"
        b["metadata"] = "PRIVATE_CANARY"
        before = copy.deepcopy(b)
        result = drift.compare(b, snapshot())
        self.assertNotIn("PRIVATE_CANARY", json.dumps(result))
        self.assertNotIn("token", json.dumps(result))
        self.assertEqual(b, before)

    def test_rejects_wrong_snapshot_shapes(self):
        for bad in [None, [], {}, {"checks": []}, {"checks": None}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                drift.compare(snapshot(), bad)

    def test_rejects_invalid_known_observations(self):
        for bad in [None, False, 12, [], {}, "", "  ", "x"*257, "a\nb", "a\u202eb"]:
            c = snapshot()
            c["checks"]["runtime_version"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                drift.compare(snapshot(), c)

    def cli(self, baseline, candidate, *args):
        with tempfile.TemporaryDirectory() as tmp:
            b, c = Path(tmp)/"b.json", Path(tmp)/"c.json"
            b.write_text(baseline)
            c.write_text(candidate)
            return subprocess.run([sys.executable, str(Path(__file__).with_name("drift.py")), str(b), str(c), *args], capture_output=True, text=True)

    def test_cli_aligned_json_and_text(self):
        raw = json.dumps(snapshot())
        r = self.cli(raw, raw, "--json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["status"], "aligned")
        self.assertIn("runtime_version: match", self.cli(raw, raw).stdout)

    def test_cli_drift_and_unverified_exit_one(self):
        c = snapshot()
        c["checks"]["runtime_version"] = "v2"
        for candidate in [c, {"checks": {}}]:
            r = self.cli(json.dumps(snapshot()), json.dumps(candidate), "--json")
            self.assertEqual(r.returncode, 1)
            self.assertIn(json.loads(r.stdout)["status"], ["drift", "unverified"])

    def test_cli_errors_are_bounded_and_value_free(self):
        for raw in ['{"SECRET_CANARY":', '{"checks": {}, "checks": {}}', 'x'*1_000_001]:
            r = self.cli(raw, json.dumps(snapshot()), "--json")
            self.assertEqual(r.returncode, 2)
            self.assertEqual(r.stdout, "")
            self.assertEqual(r.stderr.strip(), "Error: invalid or unreadable snapshot input")


if __name__ == "__main__":
    unittest.main()
