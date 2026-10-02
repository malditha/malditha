#!/usr/bin/env python3
"""Generate a conservative starter JSON Schema from one local JSON object."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 1_048_576
MAX_DEPTH = 32
MAX_NODES = 10_000
MAX_PROPERTIES = 500


class SchemaStarterError(ValueError):
    """Raised when an input cannot safely produce a starter schema."""


def load_sample(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SchemaStarterError(f"could not inspect input: {exc}") from exc
    if size > MAX_INPUT_BYTES:
        raise SchemaStarterError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise SchemaStarterError(f"could not read input: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaStarterError(f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(data, dict):
        raise SchemaStarterError("the root sample must be a JSON object")
    return data


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SchemaStarterError("non-finite numbers are not supported")
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise SchemaStarterError(f"unsupported value type: {type(value).__name__}")


def schema_key(schema: dict[str, Any]) -> str:
    return json.dumps(schema, sort_keys=True, separators=(",", ":"))


def merge_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    unique = {schema_key(schema): schema for schema in schemas}
    ordered = [unique[key] for key in sorted(unique)]
    if not ordered:
        return {}
    if len(ordered) == 1:
        return ordered[0]
    return {"anyOf": ordered}


def infer_schema(
    value: Any,
    *,
    allow_additional: bool = False,
    depth: int = 0,
    state: dict[str, int] | None = None,
) -> dict[str, Any]:
    if state is None:
        state = {"nodes": 0}
    if depth > MAX_DEPTH:
        raise SchemaStarterError(f"sample exceeds maximum depth of {MAX_DEPTH}")
    state["nodes"] += 1
    if state["nodes"] > MAX_NODES:
        raise SchemaStarterError(f"sample exceeds maximum node count of {MAX_NODES}")

    value_type = json_type(value)
    if value_type == "object":
        if len(value) > MAX_PROPERTIES:
            raise SchemaStarterError(f"object exceeds {MAX_PROPERTIES} properties")
        names = sorted(value)
        properties = {
            name: infer_schema(
                value[name],
                allow_additional=allow_additional,
                depth=depth + 1,
                state=state,
            )
            for name in names
        }
        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": allow_additional,
        }
        if names:
            schema["required"] = names
        return schema
    if value_type == "array":
        item_schemas = [
            infer_schema(
                item,
                allow_additional=allow_additional,
                depth=depth + 1,
                state=state,
            )
            for item in value
        ]
        return {"type": "array", "items": merge_schemas(item_schemas)}
    return {"type": value_type}


def build_schema(sample: dict[str, Any], title: str, allow_additional: bool = False) -> dict[str, Any]:
    schema = infer_schema(sample, allow_additional=allow_additional)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        **schema,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a conservative Draft 2020-12 starter schema from one JSON object."
    )
    parser.add_argument("sample", type=Path, help="path to a local JSON object")
    parser.add_argument("--title", default="Generated starter schema", help="schema title")
    parser.add_argument("--allow-additional", action="store_true", help="allow unlisted object properties")
    parser.add_argument("--output", type=Path, help="write the schema to this file instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        sample = load_sample(args.sample)
        schema = build_schema(sample, args.title, args.allow_additional)
        rendered = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote starter schema to {args.output}")
        else:
            sys.stdout.write(rendered)
        return 0
    except (SchemaStarterError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
