#!/usr/bin/env python3
"""Validate environment variable names without exposing their values."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ParseResult:
    keys: tuple[str, ...]
    duplicates: tuple[str, ...]
    malformed_lines: tuple[int, ...]


@dataclass(frozen=True)
class Report:
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    template_duplicates: tuple[str, ...]
    env_duplicates: tuple[str, ...]
    template_malformed_lines: tuple[int, ...]
    env_malformed_lines: tuple[int, ...]

    @property
    def valid(self) -> bool:
        return not any(asdict(self).values())


def parse_env_text(text: str) -> ParseResult:
    """Parse keys only; values are deliberately discarded immediately."""
    keys: list[str] = []
    duplicates: set[str] = set()
    malformed: list[int] = []
    seen: set[str] = set()

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            malformed.append(number)
            continue
        key, _value = line.split("=", 1)
        key = key.strip()
        if not KEY_PATTERN.fullmatch(key):
            malformed.append(number)
            continue
        if key in seen:
            duplicates.add(key)
        else:
            keys.append(key)
            seen.add(key)

    return ParseResult(tuple(keys), tuple(sorted(duplicates)), tuple(malformed))


def compare(template: ParseResult, environment: ParseResult) -> Report:
    template_keys = set(template.keys)
    env_keys = set(environment.keys)
    return Report(
        missing=tuple(sorted(template_keys - env_keys)),
        unexpected=tuple(sorted(env_keys - template_keys)),
        template_duplicates=template.duplicates,
        env_duplicates=environment.duplicates,
        template_malformed_lines=template.malformed_lines,
        env_malformed_lines=environment.malformed_lines,
    )


def validate_files(template_path: Path, env_path: Path) -> Report:
    template = parse_env_text(template_path.read_text(encoding="utf-8"))
    environment = parse_env_text(env_path.read_text(encoding="utf-8"))
    return compare(template, environment)


def render_text(report: Report) -> str:
    if report.valid:
        return "Env Guard: OK — variable names match the template."
    lines = ["Env Guard: CHECK FAILED"]
    fields = (
        ("Missing", report.missing),
        ("Unexpected", report.unexpected),
        ("Duplicate in template", report.template_duplicates),
        ("Duplicate in environment", report.env_duplicates),
        ("Malformed template lines", report.template_malformed_lines),
        ("Malformed environment lines", report.env_malformed_lines),
    )
    for label, values in fields:
        if values:
            lines.append(f"- {label}: {', '.join(map(str, values))}")
    lines.append("Values were not displayed or included in this report.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path, help="Template file, usually .env.example")
    parser.add_argument("environment", type=Path, help="Environment file to validate")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    args = parser.parse_args(argv)

    try:
        report = validate_files(args.template, args.environment)
    except (OSError, UnicodeError) as error:
        print(f"Env Guard: could not read input files: {error}", file=sys.stderr)
        return 2

    if args.json:
        payload = {"valid": report.valid, **asdict(report)}
        print(json.dumps(payload, indent=2))
    else:
        print(render_text(report))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
