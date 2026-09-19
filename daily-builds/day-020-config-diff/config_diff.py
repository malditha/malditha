#!/usr/bin/env python3
"""Compare JSON configuration files without printing their values."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Difference:
    path: str
    status: str
    before_type: str | None = None
    after_type: str | None = None


def value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def child_path(parent: str, key: str) -> str:
    return f"{parent}.{key}" if parent else key


def index_path(parent: str, index: int) -> str:
    return f"{parent}[{index}]" if parent else f"[{index}]"


def is_ignored(path: str, ignored: Iterable[str]) -> bool:
    return any(
        path == prefix or path.startswith(f"{prefix}.") or path.startswith(f"{prefix}[")
        for prefix in ignored
    )


def compare(before: Any, after: Any, ignored: Iterable[str] = (), path: str = "") -> list[Difference]:
    """Return a deterministic, value-free list of structural differences."""
    if path and is_ignored(path, ignored):
        return []

    before_type = value_type(before)
    after_type = value_type(after)
    if before_type != after_type:
        return [Difference(path or "$", "type_changed", before_type, after_type)]

    differences: list[Difference] = []
    if isinstance(before, dict):
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(before_keys | after_keys):
            current = child_path(path, key)
            if is_ignored(current, ignored):
                continue
            if key not in before:
                differences.append(Difference(current, "added", None, value_type(after[key])))
            elif key not in after:
                differences.append(Difference(current, "removed", value_type(before[key]), None))
            else:
                differences.extend(compare(before[key], after[key], ignored, current))
        return differences

    if isinstance(before, list):
        for index in range(max(len(before), len(after))):
            current = index_path(path, index)
            if is_ignored(current, ignored):
                continue
            if index >= len(before):
                differences.append(Difference(current, "added", None, value_type(after[index])))
            elif index >= len(after):
                differences.append(Difference(current, "removed", value_type(before[index]), None))
            else:
                differences.extend(compare(before[index], after[index], ignored, current))
        return differences

    if before != after:
        differences.append(Difference(path or "$", "changed", before_type, after_type))
    return differences


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def render_text(differences: list[Difference]) -> str:
    if not differences:
        return "No configuration differences found."
    lines = [f"Configuration differences: {len(differences)}"]
    for item in differences:
        details = ""
        if item.status == "type_changed":
            details = f" ({item.before_type} -> {item.after_type})"
        lines.append(f"- {item.status.upper():12} {item.path}{details}")
    return "\n".join(lines)


def render_json(differences: list[Difference]) -> str:
    return json.dumps(
        {"different": bool(differences), "difference_count": len(differences), "differences": [asdict(item) for item in differences]},
        indent=2,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare JSON configs without exposing their values.")
    parser.add_argument("before", type=Path, help="baseline JSON file")
    parser.add_argument("after", type=Path, help="candidate JSON file")
    parser.add_argument("--ignore", action="append", default=[], metavar="PATH", help="ignore an exact path and its descendants")
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        before = load_json(args.before)
        after = load_json(args.after)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Config Diff error: {error}", file=sys.stderr)
        return 2

    differences = compare(before, after, args.ignore)
    print(render_json(differences) if args.json else render_text(differences))
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
