#!/usr/bin/env python3
"""Build a reviewable role/action matrix from sanitized Frappe permission rows."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ACTIONS = (
    "read",
    "write",
    "create",
    "delete",
    "submit",
    "cancel",
    "amend",
    "report",
    "export",
    "import",
)
IDENTITY_KEYS = ("doctype", "role", "permlevel")


class InputError(ValueError):
    """Raised when the supplied export is not safe to interpret."""


def _flag(value: Any, path: str) -> bool:
    if value in (0, 1, False, True):
        return bool(value)
    raise InputError(f"{path} must be 0, 1, true or false")


def validate_rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise InputError("input must be a JSON array")

    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(payload):
        path = f"row {index + 1}"
        if not isinstance(raw, dict):
            raise InputError(f"{path} must be an object")

        doctype = raw.get("doctype")
        role = raw.get("role")
        permlevel = raw.get("permlevel", 0)
        if not isinstance(doctype, str) or not doctype.strip():
            raise InputError(f"{path}.doctype must be a non-empty string")
        if not isinstance(role, str) or not role.strip():
            raise InputError(f"{path}.role must be a non-empty string")
        if isinstance(permlevel, bool) or not isinstance(permlevel, int) or permlevel < 0:
            raise InputError(f"{path}.permlevel must be a non-negative integer")

        row: dict[str, Any] = {
            "doctype": doctype.strip(),
            "role": role.strip(),
            "permlevel": permlevel,
        }
        for action in ACTIONS:
            row[action] = _flag(raw.get(action, 0), f"{path}.{action}")
        rows.append(row)
    return rows


def build_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    keyed: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["doctype"], row["role"])].append(row)
        keyed[(row["doctype"], row["role"], row["permlevel"])].append(row)

    matrix = []
    for (doctype, role), role_rows in sorted(grouped.items()):
        matrix.append(
            {
                "doctype": doctype,
                "role": role,
                "permlevels": sorted({row["permlevel"] for row in role_rows}),
                "actions": {
                    action: any(row[action] for row in role_rows) for action in ACTIONS
                },
            }
        )

    duplicates = []
    conflicts = []
    for (doctype, role, permlevel), matching in sorted(keyed.items()):
        if len(matching) < 2:
            continue
        action_sets = {tuple(row[action] for action in ACTIONS) for row in matching}
        finding = {
            "doctype": doctype,
            "role": role,
            "permlevel": permlevel,
            "rows": len(matching),
        }
        (duplicates if len(action_sets) == 1 else conflicts).append(finding)

    return {
        "summary": {
            "permission_rows": len(rows),
            "doctypes": len({row["doctype"] for row in rows}),
            "roles": len({row["role"] for row in rows}),
            "matrix_rows": len(matrix),
            "duplicate_groups": len(duplicates),
            "conflicting_groups": len(conflicts),
        },
        "matrix": matrix,
        "duplicate_rows": duplicates,
        "conflicting_rows": conflicts,
    }


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "ROLE MATRIX",
        f"Permission rows: {summary['permission_rows']}",
        f"DocTypes: {summary['doctypes']} | Roles: {summary['roles']}",
        "",
    ]
    for row in report["matrix"]:
        granted = [name.upper() for name, enabled in row["actions"].items() if enabled]
        permissions = ", ".join(granted) if granted else "NO ACTIONS"
        levels = ",".join(str(level) for level in row["permlevels"])
        lines.append(f"{row['doctype']} | {row['role']} | levels {levels} | {permissions}")

    lines.extend(["", "REVIEW FINDINGS"])
    findings = [
        ("duplicate", item) for item in report["duplicate_rows"]
    ] + [("conflicting", item) for item in report["conflicting_rows"]]
    if not findings:
        lines.append("No duplicate or conflicting permission keys found.")
    for kind, item in findings:
        lines.append(
            f"{kind.upper()}: {item['doctype']} / {item['role']} / "
            f"level {item['permlevel']} ({item['rows']} rows)"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize sanitized Frappe permission rows by role and action."
    )
    parser.add_argument("input", type=Path, help="JSON array of sanitized permission rows")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report = build_report(validate_rows(payload))
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 1 if report["duplicate_rows"] or report["conflicting_rows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
