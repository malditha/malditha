#!/usr/bin/env python3
"""Create and compare deterministic manifests for local PNG screenshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

MAX_MANIFEST_BYTES = 512_000
MAX_SCREENSHOTS = 500
MAX_SCREENSHOT_BYTES = 25_000_000
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ManifestError(ValueError):
    """Raised when an input cannot produce a trustworthy manifest."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ManifestError(f"duplicate key: {key}")
        value[key] = item
    return value


def png_dimensions(path: Path) -> tuple[int, int]:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError as exc:
        raise ManifestError(f"cannot read {path.name}: {exc}") from exc
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ManifestError(f"not a valid PNG header: {path.name}")
    width, height = struct.unpack(">II", header[16:24])
    if width == 0 or height == 0:
        raise ManifestError(f"invalid PNG dimensions: {path.name}")
    return width, height


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ManifestError(f"cannot hash {path.name}: {exc}") from exc
    return digest.hexdigest()


def create_manifest(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise ManifestError(f"directory not found: {directory}")
    root = directory.resolve()
    files = sorted(directory.rglob("*.png"), key=lambda path: path.as_posix().casefold())
    if len(files) > MAX_SCREENSHOTS:
        raise ManifestError(f"more than {MAX_SCREENSHOTS} screenshots found")
    screenshots = []
    seen: set[str] = set()
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ManifestError(f"symlinks are not allowed: {path.name}")
        resolved = path.resolve()
        if root not in resolved.parents:
            raise ManifestError(f"path leaves screenshot directory: {path.name}")
        size = path.stat().st_size
        if size > MAX_SCREENSHOT_BYTES:
            raise ManifestError(f"screenshot exceeds 25 MB: {path.name}")
        relative = path.relative_to(directory).as_posix()
        key = relative.casefold()
        if key in seen:
            raise ManifestError(f"case-insensitive path collision: {relative}")
        seen.add(key)
        width, height = png_dimensions(path)
        screenshots.append({
            "path": relative,
            "width": width,
            "height": height,
            "bytes": size,
            "sha256": file_hash(path),
        })
    return {"version": 1, "screenshots": screenshots}


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"manifest not found: {path}")
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest exceeds 512 KB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest JSON: {exc}") from exc
    validate_manifest(data)
    return data


def validate_manifest(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"version", "screenshots"}:
        raise ManifestError("manifest must contain only version and screenshots")
    if data["version"] != 1:
        raise ManifestError("unsupported manifest version")
    items = data["screenshots"]
    if not isinstance(items, list) or len(items) > MAX_SCREENSHOTS:
        raise ManifestError("screenshots must be an array of at most 500 items")
    seen: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"screenshots[{index}]"
        if not isinstance(item, dict) or set(item) != {"path", "width", "height", "bytes", "sha256"}:
            raise ManifestError(f"{prefix} has invalid fields")
        path = item["path"]
        if not isinstance(path, str) or not path or path.startswith(("/", "\\")) or ".." in Path(path).parts:
            raise ManifestError(f"{prefix}.path must be a safe relative path")
        if path.casefold() in seen:
            raise ManifestError(f"duplicate screenshot path: {path}")
        seen.add(path.casefold())
        for field in ("width", "height", "bytes"):
            if type(item[field]) is not int or item[field] <= 0:
                raise ManifestError(f"{prefix}.{field} must be a positive integer")
        digest = item["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ManifestError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")


def compare_manifests(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(baseline)
    validate_manifest(current)
    before = {item["path"]: item for item in baseline["screenshots"]}
    after = {item["path"]: item for item in current["screenshots"]}
    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    changed = []
    unchanged = []
    for path in sorted(before.keys() & after.keys()):
        old, new = before[path], after[path]
        fields = [field for field in ("width", "height", "bytes", "sha256") if old[field] != new[field]]
        (changed if fields else unchanged).append({"path": path, "changed_fields": fields} if fields else path)
    return {
        "status": "changed" if added or removed or changed else "unchanged",
        "counts": {"added": len(added), "removed": len(removed), "changed": len(changed), "unchanged": len(unchanged)},
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
        "note": "File differences require human review; this report does not decide whether a visual change is acceptable.",
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [f"Status: {report['status']}",
             "Counts: " + ", ".join(f"{key}={value}" for key, value in report["counts"].items())]
    for label in ("added", "removed"):
        for path in report[label]:
            lines.append(f"{label.upper()}: {path}")
    for item in report["changed"]:
        lines.append(f"CHANGED: {item['path']} ({', '.join(item['changed_fields'])})")
    lines.append(f"Note: {report['note']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="create a manifest from a PNG directory")
    create.add_argument("directory", type=Path)
    create.add_argument("output", type=Path)
    compare = subparsers.add_parser("compare", help="compare baseline and current manifests")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("current", type=Path)
    compare.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            manifest = create_manifest(args.directory)
            args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {len(manifest['screenshots'])} screenshots to {args.output}")
            return 0
        report = compare_manifests(load_manifest(args.baseline), load_manifest(args.current))
        print(json.dumps(report, indent=2) if args.format == "json" else render_text(report))
        return 1 if report["status"] == "changed" else 0
    except (ManifestError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
