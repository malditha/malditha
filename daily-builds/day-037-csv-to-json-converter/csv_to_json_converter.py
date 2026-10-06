#!/usr/bin/env python3
"""Convert a bounded UTF-8 CSV document to JSON without guessing data types."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path


DEFAULT_MAX_ROWS = 10_000
DEFAULT_MAX_COLUMNS = 100


def convert_csv(
    text: str,
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    max_columns: int = DEFAULT_MAX_COLUMNS,
) -> list[dict[str, str]]:
    if not isinstance(text, str):
        raise ValueError("input must be text")
    if not 1 <= max_rows <= 1_000_000:
        raise ValueError("max_rows must be between 1 and 1000000")
    if not 1 <= max_columns <= 1_000:
        raise ValueError("max_columns must be between 1 and 1000")

    reader = csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""), strict=True)
    try:
        headers = next(reader)
    except StopIteration as error:
        raise ValueError("CSV must include a header row") from error
    except csv.Error as error:
        raise ValueError(f"invalid CSV: {error}") from error

    if len(headers) > max_columns:
        raise ValueError(f"CSV has more than {max_columns} columns")
    normalized_headers = [header.strip() for header in headers]
    for index, header in enumerate(normalized_headers, start=1):
        if not header:
            raise ValueError(f"header {index} is blank")
    seen: set[str] = set()
    for header in normalized_headers:
        if header in seen:
            raise ValueError(f"duplicate header: {header}")
        seen.add(header)

    rows: list[dict[str, str]] = []
    try:
        for line_number, values in enumerate(reader, start=2):
            if len(rows) >= max_rows:
                raise ValueError(f"CSV has more than {max_rows} data rows")
            if len(values) != len(normalized_headers):
                raise ValueError(
                    f"row {line_number} has {len(values)} fields; expected {len(normalized_headers)}"
                )
            rows.append(dict(zip(normalized_headers, values, strict=True)))
    except csv.Error as error:
        raise ValueError(f"invalid CSV: {error}") from error
    return rows


def render_json(rows: list[dict[str, str]], *, json_lines: bool = False) -> str:
    if json_lines:
        return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    return json.dumps(rows, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="CSV path; omit to read standard input")
    parser.add_argument("--json-lines", action="store_true", help="emit one JSON object per line")
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--max-columns", type=int, default=DEFAULT_MAX_COLUMNS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        rows = convert_csv(text, max_rows=args.max_rows, max_columns=args.max_columns)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(render_json(rows, json_lines=args.json_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
