#!/usr/bin/env python3
"""Summarize a sanitized Frappe worker-queue snapshot without touching Redis."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


class QueueError(ValueError):
    """Raised when the input snapshot cannot be inspected safely."""


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise QueueError(f"Invalid ISO timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise QueueError("Timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise QueueError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise QueueError(f"Invalid JSON in {path}: line {exc.lineno}") from exc
    if not isinstance(value, dict):
        raise QueueError("Snapshot must be a JSON object")
    if not isinstance(value.get("captured_at"), str):
        raise QueueError("Snapshot requires captured_at")
    if not isinstance(value.get("queues"), list) or not isinstance(value.get("workers"), list):
        raise QueueError("Snapshot requires queues and workers arrays")
    return value


def analyze(snapshot: dict[str, Any], stale_after: int = 300) -> dict[str, Any]:
    if stale_after < 1:
        raise QueueError("stale-after must be at least one second")
    captured = parse_time(snapshot["captured_at"])
    coverage: dict[str, int] = {}
    active_workers = 0
    for worker in snapshot["workers"]:
        if not isinstance(worker, dict) or not isinstance(worker.get("queues"), list):
            raise QueueError("Each worker requires a queues array")
        if worker.get("status", "active") == "active":
            active_workers += 1
            for queue in worker["queues"]:
                if not isinstance(queue, str):
                    raise QueueError("Worker queue names must be strings")
                coverage[queue] = coverage.get(queue, 0) + 1

    rows = []
    for queue in snapshot["queues"]:
        if not isinstance(queue, dict) or not isinstance(queue.get("name"), str):
            raise QueueError("Each queue requires a name")
        pending = queue.get("pending", 0)
        if not isinstance(pending, int) or pending < 0:
            raise QueueError("Queue pending counts must be non-negative integers")
        oldest = queue.get("oldest_enqueued_at")
        age = max(0, int((captured - parse_time(oldest)).total_seconds())) if oldest else None
        workers = coverage.get(queue["name"], 0)
        if pending and workers == 0:
            status = "uncovered"
        elif pending and age is not None and age >= stale_after:
            status = "stale"
        elif pending:
            status = "backlog"
        else:
            status = "clear"
        rows.append({"queue": queue["name"], "pending": pending, "active_workers": workers, "oldest_age_seconds": age, "status": status})

    rows.sort(key=lambda row: row["queue"].casefold())
    return {
        "captured_at": snapshot["captured_at"],
        "stale_after_seconds": stale_after,
        "active_worker_count": active_workers,
        "total_pending": sum(row["pending"] for row in rows),
        "attention_required": any(row["status"] in {"stale", "uncovered"} for row in rows),
        "queues": rows,
    }


def render(report: dict[str, Any]) -> str:
    lines = [f"Worker queue snapshot: {report['captured_at']}", f"Active workers: {report['active_worker_count']} · Pending jobs: {report['total_pending']}"]
    lines.extend(
        f"- {row['queue']}: {row['pending']} pending, {row['active_workers']} worker(s), {row['status']}"
        + (f", oldest {row['oldest_age_seconds']}s" if row["oldest_age_seconds"] is not None else "")
        for row in report["queues"]
    )
    lines.append("Read-only analysis of supplied metadata; no Redis connection or job mutation is performed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--stale-after", type=int, default=300, metavar="SECONDS")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = analyze(load_snapshot(args.snapshot), args.stale_after)
        print(json.dumps(report, indent=2) if args.json else render(report))
        return 1 if report["attention_required"] else 0
    except QueueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
