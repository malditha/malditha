import json
import tempfile
import unittest
from pathlib import Path

from accessibility_audit import AuditError, build_report, load_audit, render_markdown, validate_audit


def audit(checks=None):
    return {"page": "Checkout", "auditor": "Reviewer", "checked_at": "2026-11-01", "checks": checks or [
        {"id": "keyboard", "label": "Keyboard flow", "severity": "blocker", "result": "pass", "evidence": "Completed", "next_action": ""}
    ]}


class AuditTests(unittest.TestCase):
    def test_ready_when_all_applicable_checks_pass(self):
        self.assertEqual(build_report(audit())["status"], "ready")

    def test_blocker_failure_blocks_release(self):
        data = audit([{"id": "keyboard", "label": "Keyboard", "severity": "blocker", "result": "fail", "evidence": "Button unreachable", "next_action": "Fix tab order"}])
        report = build_report(data)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["blockers"], ["keyboard"])

    def test_non_blocker_failure_needs_review(self):
        data = audit([{"id": "focus", "label": "Focus", "severity": "high", "result": "fail", "evidence": "No outline", "next_action": "Add outline"}])
        self.assertEqual(build_report(data)["status"], "needs_review")

    def test_not_tested_needs_review(self):
        data = audit([{"id": "errors", "label": "Errors", "severity": "high", "result": "not_tested", "evidence": "", "next_action": "Test it"}])
        self.assertEqual(build_report(data)["unverified"], ["errors"])

    def test_findings_sort_by_severity_then_id(self):
        checks = [
            {"id": "b", "label": "B", "severity": "low", "result": "pass", "evidence": "Done", "next_action": ""},
            {"id": "a", "label": "A", "severity": "high", "result": "pass", "evidence": "Done", "next_action": ""},
        ]
        self.assertEqual([x["id"] for x in build_report(audit(checks))["findings"]], ["a", "b"])

    def test_fail_requires_next_action(self):
        with self.assertRaises(AuditError):
            validate_audit(audit([{"id": "x", "label": "X", "severity": "low", "result": "fail", "evidence": "Issue", "next_action": ""}]))

    def test_pass_requires_evidence(self):
        with self.assertRaises(AuditError):
            validate_audit(audit([{"id": "x", "label": "X", "severity": "low", "result": "pass", "evidence": "", "next_action": ""}]))

    def test_duplicate_ids_rejected(self):
        item = {"id": "x", "label": "X", "severity": "low", "result": "not_tested", "evidence": "", "next_action": ""}
        with self.assertRaises(AuditError):
            validate_audit(audit([item, item.copy()]))

    def test_unknown_fields_rejected(self):
        data = audit(); data["secret"] = "no"
        with self.assertRaises(AuditError): validate_audit(data)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.json"
            path.write_text('{"page":"a","page":"b"}', encoding="utf-8")
            with self.assertRaises(AuditError): load_audit(path)

    def test_markdown_contains_disclaimer_and_action(self):
        data = audit([{"id": "x", "label": "X", "severity": "high", "result": "fail", "evidence": "Issue", "next_action": "Fix it"}])
        output = render_markdown(build_report(data))
        self.assertIn("does not certify accessibility conformance", output)
        self.assertIn("Next action: Fix it", output)

    def test_counts_include_not_applicable(self):
        data = audit([{"id": "x", "label": "X", "severity": "low", "result": "not_applicable", "evidence": "", "next_action": ""}])
        self.assertEqual(build_report(data)["counts"]["not_applicable"], 1)


if __name__ == "__main__": unittest.main()
