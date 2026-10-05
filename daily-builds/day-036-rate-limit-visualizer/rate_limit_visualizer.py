#!/usr/bin/env python3
"""Visualize a sanitized request history against a fixed-window rate limit."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class RateLimitReport:
    limit: int
    window_seconds: int
    used: int
    remaining: int
    utilization_percent: float
    status: str
    window_started_at: str
    reset_at: str
    seconds_until_reset: int
    bar: str


def parse_timestamp(value: str, label: str = "timestamp") -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be a valid ISO 8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_timestamps(raw_json: str) -> list[str]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as error:
        raise ValueError("timestamps_json must be valid JSON") from error
    if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
        raise ValueError("timestamps_json must be an array of timestamp strings")
    if len(payload) > 10_000:
        raise ValueError("timestamps_json cannot contain more than 10000 entries")
    return payload


def analyze_rate_limit(
    timestamps: list[str],
    limit: int,
    window_seconds: int,
    now: datetime,
    bar_width: int = 20,
) -> RateLimitReport:
    if not 1 <= limit <= 1_000_000:
        raise ValueError("limit must be between 1 and 1000000")
    if not 1 <= window_seconds <= 86_400:
        raise ValueError("window_seconds must be between 1 and 86400")
    if not 5 <= bar_width <= 60:
        raise ValueError("bar_width must be between 5 and 60")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must include a timezone")
    now_utc = now.astimezone(timezone.utc)
    epoch_seconds = int(now_utc.timestamp())
    window_start = datetime.fromtimestamp(
        epoch_seconds - (epoch_seconds % window_seconds), tz=timezone.utc
    )
    reset_at = window_start + timedelta(seconds=window_seconds)

    parsed_timestamps = [parse_timestamp(value) for value in timestamps]
    if any(value > now_utc for value in parsed_timestamps):
        raise ValueError("timestamps cannot be in the future")
    used = sum(window_start <= value <= now_utc for value in parsed_timestamps)
    remaining = max(limit - used, 0)
    utilization = min((used / limit) * 100, 100.0)
    status = "blocked" if used >= limit else "warning" if utilization >= 80 else "healthy"
    filled = min(int((used / limit) * bar_width), bar_width)

    return RateLimitReport(
        limit=limit,
        window_seconds=window_seconds,
        used=used,
        remaining=remaining,
        utilization_percent=round(utilization, 2),
        status=status,
        window_started_at=iso_utc(window_start),
        reset_at=iso_utc(reset_at),
        seconds_until_reset=max(int((reset_at - now_utc).total_seconds()), 0),
        bar="█" * filled + "░" * (bar_width - filled),
    )


def render_text(report: RateLimitReport) -> str:
    return "\n".join([
        "RATE LIMIT VISUALIZER",
        f"[{report.bar}] {report.utilization_percent:.2f}%",
        f"Status: {report.status.upper()}",
        f"Requests used: {report.used}/{report.limit}",
        f"Remaining: {report.remaining}",
        f"Window: {report.window_started_at} → {report.reset_at}",
        f"Reset in: {report.seconds_until_reset} seconds",
        "Scope: Fixed-window model; this tool does not contact an API.",
    ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--window-seconds", type=int, required=True)
    parser.add_argument("--now", required=True, help="ISO 8601 timestamp with timezone")
    parser.add_argument("--timestamps-json", required=True, help="JSON array of ISO 8601 timestamps")
    parser.add_argument("--bar-width", type=int, default=20)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = analyze_rate_limit(
            load_timestamps(args.timestamps_json), args.limit, args.window_seconds,
            parse_timestamp(args.now, "now"), args.bar_width,
        )
    except ValueError as error:
        raise SystemExit(f"error: {error}") from error
    print(json.dumps(asdict(report), indent=2) if args.as_json else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
