#!/usr/bin/env python3
"""Create and verify portable SHA-256 backup manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

CHUNK_SIZE = 1024 * 1024
FORMAT_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path, excluded: Iterable[Path] = ()) -> list[Path]:
    root = root.resolve()
    blocked = {path.resolve() for path in excluded}
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and not path.is_symlink() and path.resolve() not in blocked),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def build_manifest(root: Path, excluded: Iterable[Path] = ()) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"backup directory does not exist: {root}")
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in iter_files(root, excluded)
    ]
    return {
        "format": "backup-manifest",
        "version": FORMAT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "sha256",
        "file_count": len(entries),
        "total_bytes": sum(int(entry["size"]) for entry in entries),
        "files": entries,
    }


def load_manifest(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != "backup-manifest" or data.get("version") != FORMAT_VERSION:
        raise ValueError("unsupported manifest format or version")
    if data.get("algorithm") != "sha256" or not isinstance(data.get("files"), list):
        raise ValueError("manifest is missing required fields")
    return data


def verify_manifest(root: Path, manifest: dict[str, object], excluded: Iterable[Path] = ()) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"backup directory does not exist: {root}")
    expected = {entry["path"]: entry for entry in manifest["files"]}
    actual_paths = {path.relative_to(root).as_posix(): path for path in iter_files(root, excluded)}
    missing = sorted(set(expected) - set(actual_paths))
    unexpected = sorted(set(actual_paths) - set(expected))
    changed = []
    for relative_path in sorted(set(expected) & set(actual_paths)):
        path = actual_paths[relative_path]
        entry = expected[relative_path]
        if path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            changed.append(relative_path)
    return {
        "ok": not (missing or changed or unexpected),
        "checked": len(expected),
        "missing": missing,
        "changed": changed,
        "unexpected": unexpected,
    }


def format_verification(report: dict[str, object]) -> str:
    lines = [
        "BACKUP MANIFEST — " + ("VERIFIED" if report["ok"] else "DIFFERENCES FOUND"),
        f"Checked: {report['checked']} files",
    ]
    for label in ("missing", "changed", "unexpected"):
        values = report[label]
        lines.append(f"{label.title()}: {len(values)}")
        lines.extend(f"  - {value}" for value in values)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and verify SHA-256 manifests for local backup folders.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Create a new manifest")
    create.add_argument("directory")
    create.add_argument("--output", default="backup-manifest.json")
    verify = subparsers.add_parser("verify", help="Verify a directory against a manifest")
    verify.add_argument("directory")
    verify.add_argument("manifest")
    verify.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.directory)
        if args.command == "create":
            output = Path(args.output)
            manifest = build_manifest(root, excluded=[output])
            output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(f"Created {output} with {manifest['file_count']} files ({manifest['total_bytes']} bytes).")
            return 0
        manifest_path = Path(args.manifest)
        report = verify_manifest(root, load_manifest(manifest_path), excluded=[manifest_path])
        print(json.dumps(report, indent=2) if args.json else format_verification(report))
        return 0 if report["ok"] else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"backup-manifest: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
