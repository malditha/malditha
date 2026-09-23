#!/usr/bin/env python3
"""Compare the field structure of two exported Frappe DocType definitions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SAFE_PROPERTIES = (
    "fieldtype",
    "reqd",
    "unique",
    "read_only",
    "hidden",
    "in_list_view",
    "in_standard_filter",
    "allow_on_submit",
    "no_copy",
)


class InputError(ValueError):
    """Raised when an input is not a usable DocType definition."""


def load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"{path} is not valid JSON: line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(document, dict):
        raise InputError(f"{path} must contain a JSON object")
    return document


def normalize_fields(document: dict[str, Any], source: str) -> list[dict[str, Any]]:
    raw_fields = document.get("fields")
    if not isinstance(raw_fields, list):
        raise InputError(f"{source}: 'fields' must be a JSON array")

    fields: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, raw in enumerate(raw_fields, start=1):
        if not isinstance(raw, dict):
            raise InputError(f"{source}: field {position} must be a JSON object")
        fieldname = raw.get("fieldname")
        fieldtype = raw.get("fieldtype")
        if not isinstance(fieldname, str) or not fieldname.strip():
            raise InputError(f"{source}: field {position} needs a non-empty fieldname")
        if fieldname in seen:
            raise InputError(f"{source}: duplicate fieldname '{fieldname}'")
        if not isinstance(fieldtype, str) or not fieldtype.strip():
            raise InputError(f"{source}: field '{fieldname}' needs a non-empty fieldtype")
        seen.add(fieldname)
        fields.append(raw)
    return fields


def safe_value(value: Any) -> Any:
    """Return only structural scalar values used by the report."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return type(value).__name__


def compare_documents(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    before = normalize_fields(baseline, "baseline")
    after = normalize_fields(candidate, "candidate")
    before_map = {field["fieldname"]: field for field in before}
    after_map = {field["fieldname"]: field for field in after}
    before_order = {field["fieldname"]: index for index, field in enumerate(before, start=1)}
    after_order = {field["fieldname"]: index for index, field in enumerate(after, start=1)}

    added = sorted(set(after_map) - set(before_map))
    removed = sorted(set(before_map) - set(after_map))
    changed: list[dict[str, Any]] = []
    reordered: list[dict[str, Any]] = []

    for fieldname in sorted(set(before_map) & set(after_map)):
        property_changes = []
        for property_name in SAFE_PROPERTIES:
            old_value = safe_value(before_map[fieldname].get(property_name))
            new_value = safe_value(after_map[fieldname].get(property_name))
            if old_value != new_value:
                property_changes.append(
                    {
                        "property": property_name,
                        "before": old_value,
                        "after": new_value,
                    }
                )
        if property_changes:
            changed.append({"fieldname": fieldname, "changes": property_changes})
        if before_order[fieldname] != after_order[fieldname]:
            reordered.append(
                {
                    "fieldname": fieldname,
                    "before": before_order[fieldname],
                    "after": after_order[fieldname],
                }
            )

    return {
        "doctype": {
            "baseline": baseline.get("name"),
            "candidate": candidate.get("name"),
        },
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "reordered": len(reordered),
        },
        "added": added,
        "removed": removed,
        "changed": changed,
        "reordered": reordered,
    }


def has_differences(report: dict[str, Any]) -> bool:
    return any(report["summary"].values())


def format_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "DocType Field Diff",
        "==================",
        (
            f"Added: {summary['added']}  Removed: {summary['removed']}  "
            f"Changed: {summary['changed']}  Reordered: {summary['reordered']}"
        ),
    ]
    if report["added"]:
        lines.append("\nAdded fields:")
        lines.extend(f"  + {name}" for name in report["added"])
    if report["removed"]:
        lines.append("\nRemoved fields:")
        lines.extend(f"  - {name}" for name in report["removed"])
    if report["changed"]:
        lines.append("\nChanged fields:")
        for field in report["changed"]:
            properties = ", ".join(change["property"] for change in field["changes"])
            lines.append(f"  ~ {field['fieldname']}: {properties}")
    if report["reordered"]:
        lines.append("\nReordered fields:")
        lines.extend(
            f"  ↕ {item['fieldname']}: {item['before']} -> {item['after']}"
            for item in report["reordered"]
        )
    if not has_differences(report):
        lines.append("\nNo structural field differences found.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two exported Frappe DocType field definitions."
    )
    parser.add_argument("baseline", type=Path, help="baseline DocType JSON file")
    parser.add_argument("candidate", type=Path, help="candidate DocType JSON file")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = compare_documents(
            load_document(args.baseline), load_document(args.candidate)
        )
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
    return 1 if has_differences(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
