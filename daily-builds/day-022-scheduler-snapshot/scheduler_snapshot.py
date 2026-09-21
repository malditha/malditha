#!/usr/bin/env python3
"""Create and compare privacy-conscious Frappe scheduler configuration snapshots."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


SCHEMA_VERSION = 1
TRUE_VALUES = {True, 1, "1", "true", "yes", "on"}


class SnapshotError(ValueError):
    """Raised when a bench or snapshot cannot be inspected safely."""


@dataclass(frozen=True)
class SiteState:
    site: str
    status: str
    pause_scheduler: bool
    pause_source: str
    maintenance_mode: bool
    maintenance_source: str


def is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        value = value.strip().lower()
    return value in TRUE_VALUES


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SnapshotError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in {path}: line {exc.lineno}") from exc
    if not isinstance(value, dict):
        raise SnapshotError(f"Expected a JSON object in {path}")
    return value


def discover_sites(bench: Path) -> list[Path]:
    sites_dir = bench / "sites"
    if not sites_dir.is_dir():
        raise SnapshotError(f"Missing sites directory: {sites_dir}")
    return sorted(
        (item for item in sites_dir.iterdir() if item.is_dir() and (item / "site_config.json").is_file()),
        key=lambda item: item.name.casefold(),
    )


def resolve_flag(site_config: dict[str, Any], common_config: dict[str, Any], key: str) -> tuple[bool, str]:
    if key in site_config:
        return is_truthy(site_config[key]), "site"
    if key in common_config:
        return is_truthy(common_config[key]), "common"
    return False, "default"


def status_for(paused: bool, maintenance: bool) -> str:
    if paused and maintenance:
        return "paused+maintenance"
    if paused:
        return "paused"
    if maintenance:
        return "maintenance"
    return "enabled"


def build_snapshot(bench: Path, captured_at: str | None = None) -> dict[str, Any]:
    bench = bench.expanduser().resolve()
    if not bench.is_dir():
        raise SnapshotError(f"Bench directory does not exist: {bench}")

    common_path = bench / "sites" / "common_site_config.json"
    common = load_object(common_path) if common_path.is_file() else {}
    site_states: list[SiteState] = []

    for site_dir in discover_sites(bench):
        site_config = load_object(site_dir / "site_config.json")
        paused, pause_source = resolve_flag(site_config, common, "pause_scheduler")
        maintenance, maintenance_source = resolve_flag(site_config, common, "maintenance_mode")
        site_states.append(
            SiteState(
                site=site_dir.name,
                status=status_for(paused, maintenance),
                pause_scheduler=paused,
                pause_source=pause_source,
                maintenance_mode=maintenance,
                maintenance_source=maintenance_source,
            )
        )

    timestamp = captured_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": SCHEMA_VERSION,
        "captured_at": timestamp,
        "bench": bench.name,
        "site_count": len(site_states),
        "sites": [asdict(state) for state in site_states],
    }


def validate_snapshot(value: Any, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise SnapshotError(f"Unsupported snapshot format: {path}")
    sites = value.get("sites")
    if not isinstance(sites, list) or any(not isinstance(site, dict) or not isinstance(site.get("site"), str) for site in sites):
        raise SnapshotError(f"Invalid site list in snapshot: {path}")
    return value


def load_snapshot(path: Path) -> dict[str, Any]:
    return validate_snapshot(load_object(path), path)


def compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_sites = {site["site"]: site for site in before["sites"]}
    after_sites = {site["site"]: site for site in after["sites"]}
    added = sorted(after_sites.keys() - before_sites.keys(), key=str.casefold)
    removed = sorted(before_sites.keys() - after_sites.keys(), key=str.casefold)
    changed = []
    compared_fields = ("status", "pause_scheduler", "pause_source", "maintenance_mode", "maintenance_source")

    for site in sorted(before_sites.keys() & after_sites.keys(), key=str.casefold):
        fields = [field for field in compared_fields if before_sites[site].get(field) != after_sites[site].get(field)]
        if fields:
            changed.append({"site": site, "fields": fields})

    return {"added": added, "removed": removed, "changed": changed, "has_changes": bool(added or removed or changed)}


def render_snapshot(snapshot: dict[str, Any]) -> str:
    lines = [f"Scheduler snapshot: {snapshot['bench']}", f"Captured: {snapshot['captured_at']}", f"Sites: {snapshot['site_count']}"]
    if not snapshot["sites"]:
        lines.append("- No site_config.json files found")
    for site in snapshot["sites"]:
        lines.append(
            f"- {site['site']}: {site['status']} "
            f"(pause={site['pause_source']}, maintenance={site['maintenance_source']})"
        )
    lines.append("Only allowlisted scheduler state is included; arbitrary configuration values are omitted.")
    return "\n".join(lines)


def render_comparison(result: dict[str, Any]) -> str:
    if not result["has_changes"]:
        return "No scheduler configuration changes detected."
    lines = ["Scheduler configuration changes:"]
    lines.extend(f"- added site: {site}" for site in result["added"])
    lines.extend(f"- removed site: {site}" for site in result["removed"])
    lines.extend(f"- changed {item['site']}: {', '.join(item['fields'])}" for item in result["changed"])
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="Inspect a bench and create a scheduler snapshot")
    snapshot.add_argument("bench", type=Path)
    snapshot.add_argument("--output", type=Path, help="Write the snapshot JSON to this file")
    snapshot.add_argument("--json", action="store_true", help="Print JSON instead of the readable summary")
    compare = commands.add_parser("compare", help="Compare two saved scheduler snapshots")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    compare.add_argument("--json", action="store_true", help="Print JSON instead of the readable summary")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            result = build_snapshot(args.bench)
            if args.output:
                args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2) if args.json else render_snapshot(result))
            return 1 if any(site["status"] != "enabled" for site in result["sites"]) else 0

        before = load_snapshot(args.before)
        after = load_snapshot(args.after)
        result = compare_snapshots(before, after)
        print(json.dumps(result, indent=2) if args.json else render_comparison(result))
        return 1 if result["has_changes"] else 0
    except (SnapshotError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
