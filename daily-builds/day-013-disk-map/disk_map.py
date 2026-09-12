#!/usr/bin/env python3
"""Summarize disk usage for a local directory without following symlinks."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence


def human_size(size: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def file_group(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix else "[no extension]"


def scan_directory(root: Path, top: int = 10) -> dict[str, object]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"directory does not exist: {root}")
    if top < 1:
        raise ValueError("top must be at least 1")

    files: list[dict[str, object]] = []
    groups: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "bytes": 0})
    skipped: list[str] = []

    def on_error(error: OSError) -> None:
        skipped.append(str(Path(error.filename).relative_to(root)) if error.filename else str(error))

    for current, directories, names in os.walk(root, followlinks=False, onerror=on_error):
        current_path = Path(current)
        directories[:] = sorted(
            name for name in directories if not (current_path / name).is_symlink()
        )
        for name in sorted(names):
            path = current_path / name
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                size = path.stat().st_size
            except OSError:
                skipped.append(path.relative_to(root).as_posix())
                continue
            relative = path.relative_to(root).as_posix()
            group = file_group(path)
            groups[group]["files"] += 1
            groups[group]["bytes"] += size
            files.append({"path": relative, "bytes": size})

    ordered_groups = [
        {"extension": extension, **values}
        for extension, values in sorted(
            groups.items(), key=lambda item: (-item[1]["bytes"], item[0])
        )
    ]
    largest = sorted(files, key=lambda item: (-int(item["bytes"]), str(item["path"])))[:top]
    return {
        "root": str(root),
        "files": len(files),
        "bytes": sum(int(item["bytes"]) for item in files),
        "extensions": ordered_groups,
        "largest": largest,
        "skipped": sorted(set(skipped)),
    }


def format_report(report: dict[str, object]) -> str:
    lines = [
        "DISK MAP",
        f"Root: {report['root']}",
        f"Total: {report['files']} files · {human_size(int(report['bytes']))}",
        "",
        "BY FILE TYPE",
    ]
    extensions = report["extensions"]
    if not extensions:
        lines.append("  No files found")
    for item in extensions:
        lines.append(
            f"  {item['extension']:<16} {item['files']:>5} files  {human_size(item['bytes']):>10}"
        )
    lines.extend(["", "LARGEST FILES"])
    largest = report["largest"]
    if not largest:
        lines.append("  No files found")
    for item in largest:
        lines.append(f"  {human_size(item['bytes']):>10}  {item['path']}")
    if report["skipped"]:
        lines.extend(["", f"Skipped: {len(report['skipped'])} unreadable paths"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Map a directory by total size, file type and largest files."
    )
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--top", type=int, default=10, help="number of largest files to show")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = scan_directory(Path(args.directory), args.top)
    except (OSError, ValueError) as error:
        print(f"disk-map: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
