#!/usr/bin/env python3
"""Find byte-identical files without modifying the scanned directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class DuplicateGroup:
    sha256: str
    size_bytes: int
    files: tuple[str, ...]

    @property
    def reclaimable_bytes(self) -> int:
        return self.size_bytes * (len(self.files) - 1)


@dataclass(frozen=True)
class ScanReport:
    root: str
    files_scanned: int
    bytes_scanned: int
    skipped_symlinks: int
    unreadable_files: tuple[str, ...]
    duplicate_groups: tuple[DuplicateGroup, ...]

    @property
    def reclaimable_bytes(self) -> int:
        return sum(group.reclaimable_bytes for group in self.duplicate_groups)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def scan_directory(root: Path) -> ScanReport:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    by_size: dict[int, list[Path]] = defaultdict(list)
    unreadable: list[str] = []
    skipped_symlinks = 0
    files_scanned = 0
    bytes_scanned = 0

    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current_path / name
            if path.is_symlink():
                skipped_symlinks += 1
            else:
                kept_directories.append(name)
        directories[:] = kept_directories

        for name in sorted(filenames):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                skipped_symlinks += 1
                continue
            try:
                size = path.stat().st_size
            except OSError:
                unreadable.append(relative)
                continue
            files_scanned += 1
            bytes_scanned += size
            by_size[size].append(path)

    groups: list[DuplicateGroup] = []
    for size, candidates in sorted(by_size.items()):
        if len(candidates) < 2:
            continue
        by_digest: dict[str, list[str]] = defaultdict(list)
        for path in candidates:
            relative = path.relative_to(root).as_posix()
            try:
                by_digest[sha256_file(path)].append(relative)
            except OSError:
                unreadable.append(relative)
        for digest, files in sorted(by_digest.items()):
            if len(files) > 1:
                groups.append(DuplicateGroup(digest, size, tuple(sorted(files))))

    groups.sort(key=lambda group: (-group.reclaimable_bytes, group.files))
    return ScanReport(
        root=str(root),
        files_scanned=files_scanned,
        bytes_scanned=bytes_scanned,
        skipped_symlinks=skipped_symlinks,
        unreadable_files=tuple(sorted(set(unreadable))),
        duplicate_groups=tuple(groups),
    )


def human_size(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{int(amount)} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    raise AssertionError("unreachable")


def report_as_json(report: ScanReport) -> str:
    payload = {
        "root": report.root,
        "files_scanned": report.files_scanned,
        "bytes_scanned": report.bytes_scanned,
        "skipped_symlinks": report.skipped_symlinks,
        "unreadable_files": list(report.unreadable_files),
        "duplicate_groups": [
            {**asdict(group), "files": list(group.files), "reclaimable_bytes": group.reclaimable_bytes}
            for group in report.duplicate_groups
        ],
        "reclaimable_bytes": report.reclaimable_bytes,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def report_as_text(report: ScanReport) -> str:
    lines = [
        "Duplicate Finder",
        f"Root: {report.root}",
        f"Scanned: {report.files_scanned} files ({human_size(report.bytes_scanned)})",
        f"Duplicate groups: {len(report.duplicate_groups)}",
        f"Potentially reclaimable: {human_size(report.reclaimable_bytes)}",
        f"Skipped symlinks: {report.skipped_symlinks}",
    ]
    if report.unreadable_files:
        lines.append(f"Unreadable files: {len(report.unreadable_files)}")
    for index, group in enumerate(report.duplicate_groups, start=1):
        lines.extend([
            "",
            f"Group {index}: {human_size(group.size_bytes)} each · {human_size(group.reclaimable_bytes)} reclaimable",
            f"SHA-256: {group.sha256}",
            *[f"  - {filename}" for filename in group.files],
        ])
    if not report.duplicate_groups:
        lines.extend(["", "No byte-identical duplicate files found."])
    lines.extend(["", "Read-only report: review files manually before deleting anything."])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory to scan recursively")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = scan_directory(args.directory)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(report_as_json(report) if args.json else report_as_text(report))
    return 1 if report.unreadable_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
