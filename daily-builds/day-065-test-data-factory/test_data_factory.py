#!/usr/bin/env python3
"""Generate deterministic synthetic JSON records from a bounded local schema."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

MAX_BYTES = 256_000
MAX_FIELDS = 50
MAX_RECORDS = 1_000
FIELD_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,49}$")
TYPES = {"integer", "boolean", "choice", "string", "test_email"}


class FactoryError(ValueError):
    """Raised when a schema cannot safely generate records."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise FactoryError(f"duplicate key: {key}")
        value[key] = item
    return value


def load_schema(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FactoryError(f"schema not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise FactoryError("schema exceeds 256 KB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FactoryError(f"cannot read schema JSON: {exc}") from exc
    validate_schema(data)
    return data


def _text(value: Any, field: str, limit: int = 80) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > limit:
        raise FactoryError(f"{field} must be trimmed text of 1–{limit} characters")
    return value


def validate_schema(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"fields"}:
        raise FactoryError("schema must contain only fields")
    fields = data["fields"]
    if not isinstance(fields, list) or not fields or len(fields) > MAX_FIELDS:
        raise FactoryError("fields must contain 1–50 items")
    seen: set[str] = set()
    for index, field in enumerate(fields):
        prefix = f"fields[{index}]"
        if not isinstance(field, dict):
            raise FactoryError(f"{prefix} must be an object")
        name = field.get("name")
        if not isinstance(name, str) or not FIELD_NAME.fullmatch(name):
            raise FactoryError(f"{prefix}.name is invalid")
        if name in seen:
            raise FactoryError(f"duplicate field name: {name}")
        seen.add(name)
        kind = field.get("type")
        if kind not in TYPES:
            raise FactoryError(f"{prefix}.type is unsupported")
        required = {"name", "type"}
        if kind == "integer":
            required |= {"minimum", "maximum"}
            if type(field.get("minimum")) is not int or type(field.get("maximum")) is not int:
                raise FactoryError(f"{prefix} integer bounds must be integers")
            if field["minimum"] > field["maximum"]:
                raise FactoryError(f"{prefix} minimum cannot exceed maximum")
        elif kind == "choice":
            required.add("values")
            values = field.get("values")
            if not isinstance(values, list) or not values or len(values) > 30:
                raise FactoryError(f"{prefix}.values must contain 1–30 choices")
            cleaned = [_text(value, f"{prefix}.values") for value in values]
            if len(set(cleaned)) != len(cleaned):
                raise FactoryError(f"{prefix}.values contains duplicates")
        elif kind == "string":
            required |= {"prefix", "length"}
            _text(field.get("prefix"), f"{prefix}.prefix", 30)
            if type(field.get("length")) is not int or not 1 <= field["length"] <= 64:
                raise FactoryError(f"{prefix}.length must be 1–64")
        if set(field) != required:
            raise FactoryError(f"{prefix} has missing or unknown options")


def _token(rng: random.Random, length: int) -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(rng.choice(alphabet) for _ in range(length))


def generate_records(schema: dict[str, Any], count: int, seed: int) -> list[dict[str, Any]]:
    validate_schema(schema)
    if type(count) is not int or not 1 <= count <= MAX_RECORDS:
        raise FactoryError("count must be 1–1000")
    if type(seed) is not int:
        raise FactoryError("seed must be an integer")
    rng = random.Random(seed)
    records = []
    for row in range(count):
        record: dict[str, Any] = {}
        for field in schema["fields"]:
            kind = field["type"]
            if kind == "integer":
                value = rng.randint(field["minimum"], field["maximum"])
            elif kind == "boolean":
                value = bool(rng.getrandbits(1))
            elif kind == "choice":
                value = rng.choice(field["values"])
            elif kind == "string":
                value = field["prefix"] + _token(rng, field["length"])
            else:
                value = f"case-{row + 1}-{_token(rng, 6)}@example.test"
            record[field["name"]] = value
        records.append(record)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--format", choices=("json", "ndjson"), default="json")
    args = parser.parse_args(argv)
    try:
        records = generate_records(load_schema(args.schema), args.count, args.seed)
    except FactoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "ndjson":
        for record in records:
            print(json.dumps(record, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(records, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
