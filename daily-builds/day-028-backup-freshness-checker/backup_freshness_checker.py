#!/usr/bin/env python3
"""Evaluate sanitized backup metadata against explicit freshness policies."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class InputError(ValueError):
    pass


@dataclass(frozen=True)
class BackupStatus:
    site: str
    latest_backup_at: str | None
    age_hours: float | None
    maximum_age_hours: float
    status: str


ALLOWED_KEYS = {"site", "latest_backup_at", "maximum_age_hours"}


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{field} must be a non-empty ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InputError(f"{field} must be a valid ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise InputError(f"{field} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{field} must be a number")
    number = float(value)
    if not 0 < number <= 8760:
        raise InputError(f"{field} must be greater than zero and at most 8760")
    return number


def evaluate(row: dict[str, Any], now: datetime) -> BackupStatus:
    if not isinstance(row, dict):
        raise InputError("Each backup record must be a JSON object")
    unknown = set(row) - ALLOWED_KEYS
    if unknown:
        raise InputError(f"Unsupported properties: {', '.join(sorted(unknown))}")

    site = row.get("site")
    if not isinstance(site, str) or not site.strip() or len(site) > 120:
        raise InputError("site must be a non-empty string up to 120 characters")
    threshold = positive_number(row.get("maximum_age_hours"), "maximum_age_hours")
    value = row.get("latest_backup_at")
    if value is None:
        return BackupStatus(site.strip(), None, None, threshold, "missing")

    backup_at = parse_time(value, "latest_backup_at")
    age_seconds = (now.astimezone(timezone.utc) - backup_at).total_seconds()
    if age_seconds < -300:
        status = "future"
    else:
        age_seconds = max(0, age_seconds)
        status = "fresh" if age_seconds <= threshold * 3600 else "stale"
    return BackupStatus(
        site=site.strip(),
        latest_backup_at=backup_at.isoformat().replace("+00:00", "Z"),
        age_hours=round(age_seconds / 3600, 2),
        maximum_age_hours=threshold,
        status=status,
    )


def evaluate_all(data: Any, now: datetime) -> list[BackupStatus]:
    if now.tzinfo is None:
        raise InputError("Reference time must include a timezone offset")
    if not isinstance(data, list) or not 1 <= len(data) <= 500:
        raise InputError("Input must be a JSON array containing 1 to 500 records")
    results: list[BackupStatus] = []
    seen: set[str] = set()
    for index, row in enumerate(data):
        try:
            result = evaluate(row, now)
        except InputError as error:
            raise InputError(f"Record {index + 1}: {error}") from error
        normalized = result.site.casefold()
        if normalized in seen:
            raise InputError(f"Record {index + 1}: duplicate site {result.site!r}")
        seen.add(normalized)
        results.append(result)
    return sorted(results, key=lambda item: item.site.casefold())


def render_text(results: list[BackupStatus], checked_at: datetime) -> str:
    lines = ["BACKUP FRESHNESS REPORT", f"Checked at: {checked_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')}", ""]
    for item in results:
        age = "not available" if item.age_hours is None else f"{item.age_hours:g} hours"
        lines.append(f"{item.site}: {item.status.upper()} — age {age}; limit {item.maximum_age_hours:g} hours")
    lines.extend(["", "Metadata review only; no backup archive was opened, restored, deleted or changed."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check backup metadata freshness without opening archives.")
    parser.add_argument("input", type=Path, help="Sanitized JSON backup metadata")
    parser.add_argument("--now", required=True, help="Timezone-aware ISO 8601 reference time")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args(argv)
    try:
        now = parse_time(args.now, "now")
        data = json.loads(args.input.read_text(encoding="utf-8"))
        results = evaluate_all(data, now)
    except (OSError, json.JSONDecodeError, InputError) as error:
        print(json.dumps({"ok": False, "error": str(error)}) if args.json else f"ERROR: {error}")
        return 2
    if args.json:
        print(json.dumps({"ok": True, "checked_at": now.isoformat().replace("+00:00", "Z"), "backups": [asdict(item) for item in results]}, indent=2))
    else:
        print(render_text(results, now))
    return 1 if any(item.status != "fresh" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
