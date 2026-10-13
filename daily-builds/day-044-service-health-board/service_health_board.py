#!/usr/bin/env python3
"""Build a privacy-conscious service health board from a local JSON snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_SERVICES = 100
ALLOWED_STATES = {"up", "degraded", "down", "unknown"}


class BoardError(ValueError):
    pass


def parse_time(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise BoardError(f"{field} must be an ISO 8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BoardError(f"{field} must be a valid ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise BoardError(f"{field} must include a timezone")
    return parsed


def load_snapshot(path: Path) -> dict:
    try:
        if path.stat().st_size > MAX_BYTES:
            raise BoardError("snapshot exceeds the 2 MiB limit")
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BoardError(f"cannot read snapshot: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BoardError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise BoardError("snapshot must be a JSON object")
    return data


def build_board(snapshot: dict, stale_minutes: int = 15) -> dict:
    if not 1 <= stale_minutes <= 1440:
        raise BoardError("stale threshold must be between 1 and 1440 minutes")
    observed_at = parse_time(snapshot.get("observed_at"), "observed_at")
    services = snapshot.get("services")
    if not isinstance(services, list) or not services:
        raise BoardError("services must be a non-empty array")
    if len(services) > MAX_SERVICES:
        raise BoardError("snapshot may contain at most 100 services")

    names: set[str] = set()
    rows = []
    for index, item in enumerate(services):
        if not isinstance(item, dict):
            raise BoardError(f"services[{index}] must be an object")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise BoardError(f"services[{index}].name must contain 1 to 80 characters")
        name = name.strip()
        key = name.casefold()
        if key in names:
            raise BoardError(f"duplicate service name: {name}")
        names.add(key)
        state = item.get("state")
        if state not in ALLOWED_STATES:
            raise BoardError(f"services[{index}].state must be up, degraded, down, or unknown")
        checked_at = parse_time(item.get("last_checked_at"), f"services[{index}].last_checked_at")
        age_seconds = (observed_at - checked_at).total_seconds()
        if age_seconds < 0:
            raise BoardError(f"services[{index}].last_checked_at cannot be in the future")
        latency = item.get("latency_ms")
        if latency is not None and (isinstance(latency, bool) or not isinstance(latency, (int, float)) or latency < 0):
            raise BoardError(f"services[{index}].latency_ms must be a non-negative number")
        status = "stale" if age_seconds > stale_minutes * 60 else {"up": "healthy", "degraded": "degraded", "down": "down", "unknown": "unknown"}[state]
        row = {"name": name, "state": state, "status": status, "age_seconds": int(age_seconds)}
        if latency is not None:
            row["latency_ms"] = latency
        rows.append(row)

    rows.sort(key=lambda row: row["name"].casefold())
    counts = {status: sum(row["status"] == status for row in rows) for status in ("healthy", "degraded", "down", "stale", "unknown")}
    if counts["down"]:
        overall = "down"
    elif counts["degraded"] or counts["stale"]:
        overall = "degraded"
    elif counts["unknown"]:
        overall = "unknown"
    else:
        overall = "healthy"
    return {"observed_at": observed_at.isoformat(), "stale_after_minutes": stale_minutes, "overall": overall, "summary": counts, "services": rows}


def format_text(board: dict) -> str:
    lines = [f"Service Health Board", f"Overall: {board['overall'].upper()}", f"Observed: {board['observed_at']}", ""]
    for row in board["services"]:
        latency = f" · {row['latency_ms']:g} ms" if "latency_ms" in row else ""
        lines.append(f"[{row['status'].upper():8}] {row['name']} · age {row['age_seconds']}s{latency}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="local JSON snapshot")
    parser.add_argument("--stale-minutes", type=int, default=15)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        board = build_board(load_snapshot(args.snapshot), args.stale_minutes)
    except BoardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(board, indent=2) if args.as_json else format_text(board))
    return 0 if board["overall"] == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
