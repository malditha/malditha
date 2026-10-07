#!/usr/bin/env python3
"""Profile field presence and types in a local JSON array without exposing values."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


MISSING = object()


def value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise ValueError("records contain an unsupported JSON value")


def collect_paths(value: dict[str, Any], *, max_depth: int) -> set[str]:
    paths: set[str] = set()

    def visit(current: dict[str, Any], prefix: tuple[str, ...]) -> None:
        for key, child in current.items():
            if not isinstance(key, str) or not key:
                raise ValueError("object keys must be non-empty strings")
            parts = (*prefix, key)
            if len(parts) > max_depth:
                raise ValueError(f"records exceed maximum depth of {max_depth}")
            path = ".".join(parts)
            paths.add(path)
            if isinstance(child, dict):
                visit(child, parts)

    visit(value, ())
    return paths


def read_path(record: dict[str, Any], path: str) -> Any:
    current: Any = record
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current


def profile_records(
    records: Any,
    *,
    max_records: int = 10_000,
    max_fields: int = 500,
    max_depth: int = 8,
) -> dict[str, Any]:
    if not isinstance(records, list):
        raise ValueError("input must be a JSON array of objects")
    if not 1 <= max_records <= 1_000_000:
        raise ValueError("max_records must be between 1 and 1000000")
    if not 1 <= max_fields <= 10_000:
        raise ValueError("max_fields must be between 1 and 10000")
    if not 1 <= max_depth <= 32:
        raise ValueError("max_depth must be between 1 and 32")
    if len(records) > max_records:
        raise ValueError(f"input has more than {max_records} records")
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} must be an object")

    paths: set[str] = set()
    for record in records:
        paths.update(collect_paths(record, max_depth=max_depth))
        if len(paths) > max_fields:
            raise ValueError(f"input has more than {max_fields} field paths")

    fields: dict[str, Any] = {}
    for path in sorted(paths):
        types: Counter[str] = Counter()
        present = 0
        nulls = 0
        for record in records:
            value = read_path(record, path)
            if value is MISSING:
                continue
            present += 1
            kind = value_type(value)
            types[kind] += 1
            if value is None:
                nulls += 1
        fields[path] = {
            "present": present,
            "missing": len(records) - present,
            "null": nulls,
            "types": dict(sorted(types.items())),
        }
    return {"record_count": len(records), "field_count": len(fields), "fields": fields}


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "DATA SHAPE PROFILER",
        f"Records: {report['record_count']}",
        f"Field paths: {report['field_count']}",
        "Values: omitted",
    ]
    for path, stats in report["fields"].items():
        types = ", ".join(f"{name}:{count}" for name, count in stats["types"].items())
        lines.append(
            f"{path} | present {stats['present']} | missing {stats['missing']} | "
            f"null {stats['null']} | {types}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to a UTF-8 JSON array of objects")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--max-records", type=int, default=10_000)
    parser.add_argument("--max-fields", type=int, default=500)
    parser.add_argument("--max-depth", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = profile_records(
            payload,
            max_records=args.max_records,
            max_fields=args.max_fields,
            max_depth=args.max_depth,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.as_json else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
