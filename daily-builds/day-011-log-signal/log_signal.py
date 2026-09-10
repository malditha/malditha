#!/usr/bin/env python3
"""Summarize common severity signals in plain-text logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

LEVELS = ("TRACE", "DEBUG", "INFO", "NOTICE", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL")
SEVERE_LEVELS = {"ERROR", "CRITICAL", "FATAL"}
LEVEL_PATTERN = re.compile(r"(?:^|[\s\[])" + "(" + "|".join(LEVELS) + r")" + r"(?:\]|:|\s)", re.IGNORECASE)
ISO_TIMESTAMP = re.compile(r"^\s*\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s*")
IP_ADDRESS = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE)
HEX_ID = re.compile(r"\b(?:0x)?[0-9a-f]{12,}\b", re.IGNORECASE)
NUMBER = re.compile(r"\b\d+\b")
WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Signal:
    level: str
    signature: str


@dataclass(frozen=True)
class Summary:
    total_lines: int
    matched_lines: int
    unmatched_lines: int
    levels: dict[str, int]
    top_signals: list[dict[str, object]]
    has_errors: bool


def normalize_level(level: str) -> str:
    normalized = level.upper()
    return "WARN" if normalized == "WARNING" else normalized


def normalize_message(message: str) -> str:
    """Replace volatile identifiers so equivalent log messages group together."""
    text = ISO_TIMESTAMP.sub("", message)
    text = IP_ADDRESS.sub("<ip>", text)
    text = UUID.sub("<uuid>", text)
    text = HEX_ID.sub("<id>", text)
    text = NUMBER.sub("<n>", text)
    return WHITESPACE.sub(" ", text).strip(" -:[]") or "(empty message)"


def parse_line(line: str) -> Signal | None:
    match = LEVEL_PATTERN.search(line)
    if not match:
        return None
    level = normalize_level(match.group(1))
    message = line[match.end() :]
    return Signal(level=level, signature=normalize_message(message))


def summarize(lines: Iterable[str], top: int = 5) -> Summary:
    level_counts: Counter[str] = Counter()
    signal_counts: Counter[Signal] = Counter()
    total = 0
    unmatched = 0

    for raw_line in lines:
        total += 1
        signal = parse_line(raw_line.rstrip("\n"))
        if signal is None:
            unmatched += 1
            continue
        level_counts[signal.level] += 1
        signal_counts[signal] += 1

    ranked = sorted(signal_counts.items(), key=lambda item: (-item[1], item[0].level, item[0].signature))[:top]
    return Summary(
        total_lines=total,
        matched_lines=total - unmatched,
        unmatched_lines=unmatched,
        levels=dict(sorted(level_counts.items())),
        top_signals=[{"level": signal.level, "count": count, "signature": signal.signature} for signal, count in ranked],
        has_errors=any(level_counts[level] for level in SEVERE_LEVELS),
    )


def format_text(summary: Summary) -> str:
    level_text = ", ".join(f"{level}={count}" for level, count in summary.levels.items()) or "none"
    rows = [
        "LOG SIGNAL",
        f"Lines: {summary.total_lines} total · {summary.matched_lines} matched · {summary.unmatched_lines} unmatched",
        f"Levels: {level_text}",
        "Status: ATTENTION" if summary.has_errors else "Status: CLEAR",
        "",
        "TOP SIGNALS",
    ]
    if not summary.top_signals:
        rows.append("No recognized signals.")
    for index, signal in enumerate(summary.top_signals, start=1):
        rows.append(f"{index}. [{signal['level']}] ×{signal['count']} {signal['signature']}")
    return "\n".join(rows)


def read_lines(source: str) -> list[str]:
    if source == "-":
        return sys.stdin.readlines()
    return Path(source).read_text(encoding="utf-8", errors="replace").splitlines()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize severity and recurring patterns in plain-text logs.")
    parser.add_argument("source", help="Log file path, or - to read standard input")
    parser.add_argument("--top", type=int, default=5, help="Number of recurring signals to show (default: 5)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--no-fail", action="store_true", help="Always exit successfully after producing the report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.top < 1:
        build_parser().error("--top must be at least 1")
    try:
        summary = summarize(read_lines(args.source), top=args.top)
    except OSError as error:
        print(f"log-signal: {error}", file=sys.stderr)
        return 2

    print(json.dumps(asdict(summary), indent=2) if args.json else format_text(summary))
    return 0 if args.no_fail or not summary.has_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
