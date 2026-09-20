#!/usr/bin/env python3
"""Run privacy-conscious, read-only checks on a Frappe bench directory."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Check:
    code: str
    level: str
    message: str
    subject: str


def add(checks: list[Check], code: str, level: str, message: str, subject: Path | str) -> None:
    checks.append(Check(code, level, message, str(subject)))


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, str(error)
    if not isinstance(value, dict):
        return None, "top-level JSON value must be an object"
    return value, None


def check_directory(checks: list[Check], path: Path, code: str) -> bool:
    if path.is_dir():
        add(checks, code, "pass", "Directory is present.", path)
        return True
    add(checks, code, "fail", "Required directory is missing.", path)
    return False


def inspect_bench(root: Path) -> list[Check]:
    """Inspect a bench without executing commands or revealing config values."""
    checks: list[Check] = []
    apps_ok = check_directory(checks, root / "apps", "apps-directory")
    sites_ok = check_directory(checks, root / "sites", "sites-directory")

    procfile = root / "Procfile"
    add(checks, "procfile", "pass" if procfile.is_file() else "warn", "Procfile is present." if procfile.is_file() else "Procfile was not found; confirm how processes are managed.", procfile)

    registry_candidates = [root / "sites" / "apps.txt", root / "apps.txt"]
    registry = next((path for path in registry_candidates if path.is_file()), None)
    if registry:
        names = [line.strip() for line in registry.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
        add(checks, "apps-registry", "pass" if names else "fail", f"Apps registry contains {len(names)} app name(s)." if names else "Apps registry is empty.", registry)
    elif sites_ok:
        add(checks, "apps-registry", "fail", "No apps registry was found.", root / "sites" / "apps.txt")

    common = root / "sites" / "common_site_config.json"
    if common.is_file():
        config, error = read_json(common)
        if error:
            add(checks, "common-config", "fail", f"Common config is not valid JSON: {error}", common)
        else:
            add(checks, "common-config", "pass", f"Common config is valid JSON with {len(config or {})} top-level key(s); values were not read into the report.", common)
            if config and config.get("pause_scheduler"):
                add(checks, "scheduler-paused", "warn", "The common configuration indicates that the scheduler is paused.", common)
    elif sites_ok:
        add(checks, "common-config", "warn", "Common site configuration was not found.", common)

    if sites_ok:
        site_configs = sorted(
            path for path in (root / "sites").glob("*/site_config.json")
            if path.parent.name not in {"assets", "common"}
        )
        if not site_configs:
            add(checks, "site-discovery", "warn", "No site_config.json files were discovered one directory below sites.", root / "sites")
        for site_config in site_configs:
            config, error = read_json(site_config)
            subject = site_config.parent.name
            if error:
                add(checks, "site-config", "fail", f"Site configuration is not valid JSON: {error}", subject)
                continue
            keys = set(config or {})
            add(checks, "site-config", "pass", f"Site config is valid JSON with {len(keys)} top-level key(s); values were omitted.", subject)
            if "db_name" not in keys:
                add(checks, "site-db-name", "warn", "Site config does not contain a db_name key.", subject)

    if apps_ok:
        app_directories = sorted(path.name for path in (root / "apps").iterdir() if path.is_dir() and not path.is_symlink())
        add(checks, "app-directories", "pass" if app_directories else "warn", f"Found {len(app_directories)} local app director{'y' if len(app_directories) == 1 else 'ies'}." if app_directories else "No local app directories were found.", root / "apps")
    return checks


def summary(checks: list[Check]) -> dict[str, int]:
    return {level: sum(check.level == level for check in checks) for level in ("pass", "warn", "fail")}


def render_text(root: Path, checks: list[Check]) -> str:
    totals = summary(checks)
    lines = [f"Bench Doctor Lite: {root}", f"PASS {totals['pass']} · WARN {totals['warn']} · FAIL {totals['fail']}"]
    lines.extend(f"[{check.level.upper():4}] {check.code}: {check.message} ({check.subject})" for check in checks)
    lines.append("Read-only inspection complete. Configuration values were not included.")
    return "\n".join(lines)


def render_json(root: Path, checks: list[Check]) -> str:
    return json.dumps({"root": str(root), "summary": summary(checks), "checks": [asdict(check) for check in checks], "values_included": False}, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe, read-only structural checks on a Frappe bench.")
    parser.add_argument("bench", type=Path, help="path to the bench directory")
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.bench.expanduser().resolve()
    if not root.is_dir():
        print(f"Bench Doctor Lite error: directory not found: {root}", file=sys.stderr)
        return 2
    checks = inspect_bench(root)
    print(render_json(root, checks) if args.json else render_text(root, checks))
    return 1 if any(check.level in {"warn", "fail"} for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
