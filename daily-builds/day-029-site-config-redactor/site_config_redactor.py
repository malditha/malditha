#!/usr/bin/env python3
"""Create a conservative, shareable copy of a Frappe site config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REDACTED = "[REDACTED]"
MAX_KEYS = 200
MAX_KEY_LENGTH = 128

# These fields describe runtime behaviour without normally containing credentials.
# Unknown fields are redacted by default instead of guessed from their names.
SAFE_FIELDS: dict[str, tuple[type, ...]] = {
    "allow_tests": (bool,),
    "background_workers": (int,),
    "db_type": (str,),
    "developer_mode": (bool, int),
    "disable_website_cache": (bool, int),
    "gunicorn_workers": (int,),
    "maintenance_mode": (bool, int),
    "pause_scheduler": (bool, int),
    "scheduler_interval": (int,),
    "server_script_enabled": (bool, int),
    "socketio_port": (int,),
}


class ConfigError(ValueError):
    """Raised when the input is not a bounded site-config object."""


def validate_config(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ConfigError("site config must be a top-level JSON object")
    if len(config) > MAX_KEYS:
        raise ConfigError(f"site config cannot contain more than {MAX_KEYS} keys")

    for key in config:
        if not isinstance(key, str) or not key:
            raise ConfigError("every site-config key must be a non-empty string")
        if len(key) > MAX_KEY_LENGTH:
            raise ConfigError(
                f"site-config keys cannot exceed {MAX_KEY_LENGTH} characters"
            )
    return config


def _is_safe_scalar(key: str, value: Any) -> bool:
    allowed_types = SAFE_FIELDS.get(key)
    if allowed_types is None:
        return False
    # bool is an int subclass, so keep numeric-only fields strict.
    if bool not in allowed_types and isinstance(value, bool):
        return False
    return isinstance(value, allowed_types)


def redact_config(config: Any) -> dict[str, Any]:
    """Return a deterministic report and a sanitized copy without mutating input."""
    source = validate_config(config)
    sanitized: dict[str, Any] = {}
    kept: list[str] = []
    redacted: list[str] = []

    for key in sorted(source):
        value = source[key]
        if _is_safe_scalar(key, value):
            sanitized[key] = value
            kept.append(key)
        else:
            sanitized[key] = REDACTED
            redacted.append(key)

    return {
        "ok": True,
        "redacted_config": sanitized,
        "summary": {
            "kept_count": len(kept),
            "kept_keys": kept,
            "redacted_count": len(redacted),
            "redacted_keys": redacted,
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"could not read {path}: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create an allowlist-based redacted copy of a Frappe site config."
    )
    parser.add_argument("input", type=Path, help="path to the source JSON file")
    parser.add_argument("--output", type=Path, help="write the safe report to this file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = redact_config(load_json(args.input))
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
            print(f"Wrote redacted report to {args.output}")
        else:
            sys.stdout.write(payload)
        return 0
    except (ConfigError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
