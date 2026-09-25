#!/usr/bin/env python3
"""Validate and preview a small, documented subset of Frappe naming series."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

TOKEN_RE = re.compile(r"(#+|\.[A-Za-z_][A-Za-z0-9_]*\.|YYYY|YY|MM|DD)")
FIELD_RE = re.compile(r"^\.([A-Za-z_][A-Za-z0-9_]*)\.$")
SAFE_FIELD_VALUE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class SeriesError(ValueError):
    """Raised when a pattern or preview input is unsafe or unsupported."""


@dataclass(frozen=True)
class Preview:
    pattern: str
    rendered: list[str]
    counter_width: int
    fields_used: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "pattern": self.pattern,
            "rendered": self.rendered,
            "counter_width": self.counter_width,
            "fields_used": self.fields_used,
        }


def parse_fields(pairs: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SeriesError(f"Field must use key=value syntax: {pair!r}")
        key, value = pair.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise SeriesError(f"Invalid field name: {key!r}")
        if not value or not SAFE_FIELD_VALUE_RE.fullmatch(value):
            raise SeriesError(f"Unsafe field value for {key!r}")
        fields[key] = value
    return fields


def tokenize(pattern: str) -> list[str]:
    if not pattern or len(pattern) > 160:
        raise SeriesError("Pattern must contain 1 to 160 characters")
    if any(ord(char) < 32 for char in pattern):
        raise SeriesError("Pattern cannot contain control characters")

    tokens: list[str] = []
    position = 0
    for match in TOKEN_RE.finditer(pattern):
        if match.start() > position:
            literal = pattern[position:match.start()]
            if "#" in literal or literal.count(".") % 2:
                raise SeriesError(f"Unsupported token near {literal!r}")
            tokens.append(literal)
        tokens.append(match.group(0))
        position = match.end()
    if position < len(pattern):
        literal = pattern[position:]
        if "#" in literal or literal.count(".") % 2:
            raise SeriesError(f"Unsupported token near {literal!r}")
        tokens.append(literal)

    counters = [token for token in tokens if token.startswith("#")]
    if len(counters) != 1:
        raise SeriesError("Pattern must contain exactly one # counter token")
    if not 1 <= len(counters[0]) <= 9:
        raise SeriesError("Counter width must be between 1 and 9")
    return tokens


def preview_series(
    pattern: str,
    *,
    start: int = 1,
    count: int = 5,
    on_date: date | None = None,
    fields: dict[str, str] | None = None,
) -> Preview:
    if start < 0:
        raise SeriesError("Start must be zero or greater")
    if not 1 <= count <= 50:
        raise SeriesError("Count must be between 1 and 50")

    tokens = tokenize(pattern)
    sample_date = on_date or date.today()
    supplied_fields = fields or {}
    fields_used: list[str] = []
    counter_width = next(len(token) for token in tokens if token.startswith("#"))

    pieces: list[str | tuple[str, int]] = []
    for token in tokens:
        field_match = FIELD_RE.match(token)
        if token.startswith("#"):
            pieces.append(("counter", len(token)))
        elif field_match:
            field_name = field_match.group(1)
            if field_name not in supplied_fields:
                raise SeriesError(f"Missing sample value for field {field_name!r}")
            if field_name not in fields_used:
                fields_used.append(field_name)
            pieces.append(supplied_fields[field_name])
        elif token == "YYYY":
            pieces.append(f"{sample_date.year:04d}")
        elif token == "YY":
            pieces.append(f"{sample_date.year % 100:02d}")
        elif token == "MM":
            pieces.append(f"{sample_date.month:02d}")
        elif token == "DD":
            pieces.append(f"{sample_date.day:02d}")
        else:
            pieces.append(token)

    rendered: list[str] = []
    limit = 10**counter_width
    if start + count > limit:
        raise SeriesError(f"Counter exceeds {counter_width}-digit capacity")
    for number in range(start, start + count):
        rendered.append(
            "".join(
                f"{number:0{piece[1]}d}" if isinstance(piece, tuple) else piece
                for piece in pieces
            )
        )

    return Preview(pattern, rendered, counter_width, sorted(fields_used))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a naming-series pattern and preview sample names."
    )
    parser.add_argument("pattern", help="Example: INV-.branch.-YYYY-MM-#####")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--date", dest="sample_date", help="Preview date in YYYY-MM-DD")
    parser.add_argument("--field", action="append", default=[], help="Sample key=value")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        sample_date = date.fromisoformat(args.sample_date) if args.sample_date else None
        result = preview_series(
            args.pattern,
            start=args.start,
            count=args.count,
            on_date=sample_date,
            fields=parse_fields(args.field),
        )
    except (SeriesError, ValueError) as error:
        if args.json:
            print(json.dumps({"ok": False, "error": str(error)}, indent=2))
        else:
            print(f"ERROR: {error}")
        return 2

    if args.json:
        print(json.dumps({"ok": True, **result.as_dict()}, indent=2))
    else:
        print(f"Pattern: {result.pattern}")
        print(f"Counter width: {result.counter_width}")
        print("Preview:")
        for name in result.rendered:
            print(f"  {name}")
        print("\nThis is a local preview; no Frappe counter was read or changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
