#!/usr/bin/env python3
"""Format a small, sanitized Frappe patch execution log."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_RECORDS = 200
ALLOWED_FIELDS = {"patch", "status", "started_at", "finished_at"}
ALLOWED_STATUSES = {"success", "failed", "skipped"}
PATCH_PATTERN = re.compile(r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*$")


class InputError(ValueError):
    """Raised when the sanitized input contract is not met."""


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise InputError(f"{field} must be an ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InputError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InputError(f"{field} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def normalize_records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise InputError("input must be a JSON array")
    if len(payload) > MAX_RECORDS:
        raise InputError(f"input may contain at most {MAX_RECORDS} records")

    records: list[dict[str, Any]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise InputError(f"record {index} must be an object")
        unknown = set(item) - ALLOWED_FIELDS
        missing = ALLOWED_FIELDS - set(item)
        if unknown:
            raise InputError(f"record {index} has unsupported fields: {', '.join(sorted(unknown))}")
        if missing:
            raise InputError(f"record {index} is missing fields: {', '.join(sorted(missing))}")

        patch = item["patch"]
        status = item["status"]
        if not isinstance(patch, str) or len(patch) > 160 or not PATCH_PATTERN.fullmatch(patch):
            raise InputError(f"record {index} has an invalid patch identifier")
        if status not in ALLOWED_STATUSES:
            raise InputError(f"record {index} has an invalid status")

        started = parse_timestamp(item["started_at"], f"record {index} started_at")
        finished = parse_timestamp(item["finished_at"], f"record {index} finished_at")
        if finished < started:
            raise InputError(f"record {index} finishes before it starts")

        records.append({
            "patch": patch,
            "status": status,
            "started_at": started.isoformat().replace("+00:00", "Z"),
            "finished_at": finished.isoformat().replace("+00:00", "Z"),
            "duration_ms": round((finished - started).total_seconds() * 1000),
            "_started": started,
        })

    return sorted(records, key=lambda record: (record["_started"], record["patch"]))


def build_report(payload: Any) -> dict[str, Any]:
    records = normalize_records(payload)
    summary = {status: 0 for status in ("success", "failed", "skipped")}
    total_duration = 0
    safe_records = []
    for record in records:
        summary[record["status"]] += 1
        total_duration += record["duration_ms"]
        safe_records.append({key: value for key, value in record.items() if key != "_started"})
    return {
        "summary": {"total": len(records), **summary, "total_duration_ms": total_duration},
        "records": safe_records,
    }


def format_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "PATCH LOG REPORT",
        f"Total: {summary['total']} | Success: {summary['success']} | Failed: {summary['failed']} | Skipped: {summary['skipped']}",
        f"Combined duration: {summary['total_duration_ms']} ms",
        "",
    ]
    if not report["records"]:
        lines.append("No patch records supplied.")
    for record in report["records"]:
        lines.append(
            f"[{record['status'].upper():7}] {record['started_at']}  {record['patch']}  ({record['duration_ms']} ms)"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format a sanitized Frappe patch log.")
    parser.add_argument("input", type=Path, help="JSON array containing allowlisted patch records")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report = build_report(payload)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
