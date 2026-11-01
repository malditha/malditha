#!/usr/bin/env python3
"""Build a prioritized accessibility review report from a local JSON audit."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_BYTES = 256_000
VALID_RESULTS = {"pass", "fail", "not_tested", "not_applicable"}
VALID_SEVERITIES = {"blocker", "high", "medium", "low"}
SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}


class AuditError(ValueError):
    """Raised when the audit input is unsafe or invalid."""


@dataclass(frozen=True)
class Finding:
    check_id: str
    label: str
    severity: str
    result: str
    evidence: str
    next_action: str


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_audit(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AuditError(f"file not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise AuditError("input exceeds 256 KB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read JSON: {exc}") from exc
    validate_audit(data)
    return data


def _clean_text(value: Any, field: str, *, required: bool = True, limit: int = 500) -> str:
    if not isinstance(value, str):
        raise AuditError(f"{field} must be text")
    text = " ".join(value.split())
    if required and not text:
        raise AuditError(f"{field} cannot be empty")
    if len(text) > limit:
        raise AuditError(f"{field} exceeds {limit} characters")
    return text


def validate_audit(data: Any) -> None:
    if not isinstance(data, dict):
        raise AuditError("root must be an object")
    allowed = {"page", "auditor", "checked_at", "checks"}
    unknown = set(data) - allowed
    if unknown:
        raise AuditError(f"unknown root field: {sorted(unknown)[0]}")
    _clean_text(data.get("page"), "page", limit=200)
    _clean_text(data.get("auditor"), "auditor", limit=100)
    _clean_text(data.get("checked_at"), "checked_at", limit=40)
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise AuditError("checks must be a non-empty array")
    if len(checks) > 100:
        raise AuditError("checks cannot exceed 100 items")
    seen: set[str] = set()
    for index, check in enumerate(checks):
        prefix = f"checks[{index}]"
        if not isinstance(check, dict):
            raise AuditError(f"{prefix} must be an object")
        fields = {"id", "label", "severity", "result", "evidence", "next_action"}
        unknown = set(check) - fields
        if unknown:
            raise AuditError(f"{prefix} has unknown field: {sorted(unknown)[0]}")
        check_id = _clean_text(check.get("id"), f"{prefix}.id", limit=60)
        if check_id in seen:
            raise AuditError(f"duplicate check id: {check_id}")
        seen.add(check_id)
        _clean_text(check.get("label"), f"{prefix}.label", limit=160)
        severity = check.get("severity")
        result = check.get("result")
        if severity not in VALID_SEVERITIES:
            raise AuditError(f"{prefix}.severity must be blocker, high, medium, or low")
        if result not in VALID_RESULTS:
            raise AuditError(f"{prefix}.result must be pass, fail, not_tested, or not_applicable")
        evidence = _clean_text(check.get("evidence", ""), f"{prefix}.evidence", required=False)
        action = _clean_text(check.get("next_action", ""), f"{prefix}.next_action", required=False)
        if result in {"pass", "fail"} and not evidence:
            raise AuditError(f"{prefix}.evidence is required for pass or fail")
        if result == "fail" and not action:
            raise AuditError(f"{prefix}.next_action is required for fail")


def build_report(data: dict[str, Any]) -> dict[str, Any]:
    findings = [Finding(
        check_id=check["id"], label=check["label"], severity=check["severity"],
        result=check["result"], evidence=check.get("evidence", ""),
        next_action=check.get("next_action", ""),
    ) for check in data["checks"]]
    findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.check_id))
    counts = {result: sum(item.result == result for item in findings) for result in VALID_RESULTS}
    blockers = [item.check_id for item in findings if item.result == "fail" and item.severity == "blocker"]
    unverified = [item.check_id for item in findings if item.result == "not_tested"]
    status = "blocked" if blockers else "needs_review" if counts["fail"] or unverified else "ready"
    return {
        "page": data["page"], "auditor": data["auditor"], "checked_at": data["checked_at"],
        "status": status, "counts": counts, "blockers": blockers, "unverified": unverified,
        "findings": [{
            "id": item.check_id, "label": item.label, "severity": item.severity,
            "result": item.result, "evidence": item.evidence,
            "next_action": item.next_action,
        } for item in findings],
        "note": "This report supports a manual review; it does not certify accessibility conformance.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Accessibility audit: {report['page']}", "",
        f"- **Status:** {report['status']}", f"- **Auditor:** {report['auditor']}",
        f"- **Checked:** {report['checked_at']}",
        f"- **Results:** {report['counts']['pass']} pass, {report['counts']['fail']} fail, "
        f"{report['counts']['not_tested']} not tested, {report['counts']['not_applicable']} not applicable", "",
        "## Findings", "",
    ]
    for item in report["findings"]:
        lines.extend([f"### {item['id']} — {item['label']}",
                      f"- Severity: {item['severity']}", f"- Result: {item['result']}"])
        if item["evidence"]:
            lines.append(f"- Evidence: {item['evidence']}")
        if item["next_action"]:
            lines.append(f"- Next action: {item['next_action']}")
        lines.append("")
    lines.extend([f"> {report['note']}", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path, help="local JSON audit")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    try:
        report = build_report(load_audit(args.audit))
    except AuditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.format == "json" else render_markdown(report), end="\n")
    return 1 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
