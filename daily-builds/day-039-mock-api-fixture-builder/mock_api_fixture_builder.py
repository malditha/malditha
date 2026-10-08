#!/usr/bin/env python3
"""Build deterministic synthetic API fixtures from a bounded JSON blueprint."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RULE_KEYS = {
    "integer": {"type", "start", "step"},
    "string": {"type", "prefix", "pad"},
    "boolean": {"type", "start"},
    "enum": {"type", "values"},
    "null": {"type"},
}


def require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def validate_rule(field: str, rule: Any) -> dict[str, Any]:
    if not isinstance(rule, dict):
        raise ValueError(f"rule for {field} must be an object")
    kind = rule.get("type")
    if kind not in RULE_KEYS:
        raise ValueError(f"field {field} has unsupported type")
    unknown = set(rule) - RULE_KEYS[kind]
    if unknown:
        raise ValueError(f"field {field} has unknown rule keys: {', '.join(sorted(unknown))}")

    if kind == "integer":
        start = require_int(rule.get("start", 1), f"{field}.start")
        step = require_int(rule.get("step", 1), f"{field}.step")
        if abs(start) > 1_000_000_000 or abs(step) > 1_000_000:
            raise ValueError(f"field {field} integer settings exceed limits")
    elif kind == "string":
        prefix = rule.get("prefix", "")
        pad = require_int(rule.get("pad", 0), f"{field}.pad")
        if not isinstance(prefix, str) or len(prefix) > 64:
            raise ValueError(f"{field}.prefix must be a string of at most 64 characters")
        if not 0 <= pad <= 12:
            raise ValueError(f"{field}.pad must be between 0 and 12")
    elif kind == "boolean":
        if not isinstance(rule.get("start", True), bool):
            raise ValueError(f"{field}.start must be a boolean")
    elif kind == "enum":
        values = rule.get("values")
        if (
            not isinstance(values, list)
            or not 1 <= len(values) <= 20
            or any(not isinstance(value, str) or len(value) > 64 for value in values)
        ):
            raise ValueError(f"{field}.values must contain 1 to 20 strings of at most 64 characters")
    return rule


def value_for(rule: dict[str, Any], index: int) -> Any:
    kind = rule["type"]
    if kind == "integer":
        return rule.get("start", 1) + index * rule.get("step", 1)
    if kind == "string":
        number = str(index + 1).zfill(rule.get("pad", 0))
        return f"{rule.get('prefix', '')}{number}"
    if kind == "boolean":
        start = rule.get("start", True)
        return start if index % 2 == 0 else not start
    if kind == "enum":
        values = rule["values"]
        return values[index % len(values)]
    return None


def build_fixtures(blueprint: Any) -> list[dict[str, Any]]:
    if not isinstance(blueprint, dict):
        raise ValueError("blueprint must be a JSON object")
    unknown = set(blueprint) - {"count", "fields"}
    if unknown:
        raise ValueError(f"unknown blueprint keys: {', '.join(sorted(unknown))}")

    count = require_int(blueprint.get("count"), "count")
    if not 1 <= count <= 1000:
        raise ValueError("count must be between 1 and 1000")
    fields = blueprint.get("fields")
    if not isinstance(fields, dict) or not 1 <= len(fields) <= 50:
        raise ValueError("blueprint must define between 1 and 50 fields")

    validated: list[tuple[str, dict[str, Any]]] = []
    for field, rule in fields.items():
        if not isinstance(field, str) or not FIELD_NAME.fullmatch(field):
            raise ValueError("field names must use letters, numbers and underscores")
        validated.append((field, validate_rule(field, rule)))

    return [
        {field: value_for(rule, index) for field, rule in validated}
        for index in range(count)
    ]


def render_jsonl(fixtures: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(record, ensure_ascii=False) for record in fixtures)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blueprint", help="Path to a UTF-8 JSON fixture blueprint")
    parser.add_argument("--jsonl", action="store_true", help="Write one JSON record per line")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        blueprint = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
        fixtures = build_fixtures(blueprint)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(render_jsonl(fixtures) if args.jsonl else json.dumps(fixtures, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
