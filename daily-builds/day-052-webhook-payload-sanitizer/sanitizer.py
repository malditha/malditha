#!/usr/bin/env python3
"""Sanitize one local JSON webhook payload using a conservative key policy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 1_000_000
MAX_DEPTH = 20
MAX_NODES = 10_000
MASK = "[REDACTED]"
DEFAULT_KEYS = {
    "access_token", "api_key", "apikey", "authorization", "cookie",
    "credit_card", "cvv", "password", "refresh_token", "secret",
    "session", "session_id", "token",
}
SENSITIVE_PARTS = {"auth", "credential", "password", "secret", "token"}
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class InputError(ValueError):
    """Raised when input cannot be processed within the safe limits."""


@dataclass
class Counter:
    nodes: int = 0

    def visit(self) -> None:
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise InputError("payload exceeds node limit")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise InputError("file exceeds size limit")
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except InputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("unable to read JSON input") from exc


def normalize_key(key: str) -> str:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    return re.sub(r"[^a-z0-9]+", "_", separated.casefold()).strip("_")


def is_sensitive_key(key: str, extra_keys: set[str]) -> bool:
    normalized = normalize_key(key)
    if normalized in DEFAULT_KEYS or normalized in extra_keys:
        return True
    parts = set(normalized.split("_"))
    return bool(parts & SENSITIVE_PARTS)


def sanitize_payload(
    payload: Any,
    *,
    strategy: str = "mask",
    extra_keys: set[str] | None = None,
) -> tuple[Any, dict[str, Any]]:
    if strategy not in {"mask", "remove"}:
        raise InputError("strategy must be mask or remove")
    normalized_extra = {normalize_key(key) for key in (extra_keys or set())}
    if any(not key for key in normalized_extra):
        raise InputError("invalid extra key")
    paths: list[str] = []
    counter = Counter()

    def walk(value: Any, path: str, depth: int) -> Any:
        if depth > MAX_DEPTH:
            raise InputError("payload exceeds depth limit")
        counter.visit()
        if isinstance(value, dict):
            output: dict[str, Any] = {}
            for key in sorted(value):
                if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
                    raise InputError("invalid object key")
                child_path = f"{path}.{key}" if path else key
                if is_sensitive_key(key, normalized_extra):
                    paths.append(child_path)
                    if strategy == "mask":
                        output[key] = MASK
                else:
                    output[key] = walk(value[key], child_path, depth + 1)
            return output
        if isinstance(value, list):
            return [walk(item, f"{path}[{index}]", depth + 1) for index, item in enumerate(value)]
        return value

    sanitized = walk(payload, "$", 0)
    return sanitized, {
        "strategy": strategy,
        "redacted_count": len(paths),
        "redacted_paths": paths,
        "nodes_checked": counter.nodes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--strategy", choices=("mask", "remove"), default="mask")
    parser.add_argument("--sensitive-key", action="append", default=[])
    parser.add_argument("--report", action="store_true", help="write a metadata report to stderr")
    args = parser.parse_args(argv)
    try:
        sanitized, report = sanitize_payload(
            load_json(args.payload), strategy=args.strategy, extra_keys=set(args.sensitive_key)
        )
    except InputError:
        print("Input error: unable to sanitize the supplied payload.", file=sys.stderr)
        return 2
    print(json.dumps(sanitized, indent=2, ensure_ascii=False))
    if args.report:
        print(json.dumps(report, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
