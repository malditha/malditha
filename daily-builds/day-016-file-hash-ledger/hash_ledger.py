#!/usr/bin/env python3
"""Record and verify tamper-evident SHA-256 file history."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def entry_hash(entry: dict) -> str:
    payload = {key: value for key, value in entry.items() if key != "entry_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON on ledger line {number}") from error
        if not isinstance(entry, dict):
            raise ValueError(f"ledger line {number} is not an object")
        entries.append(entry)
    return entries


def verify_entries(entries: list[dict]) -> tuple[bool, str]:
    previous = GENESIS
    required = {"index", "recorded_at", "path", "size", "sha256", "previous", "entry_hash"}
    for position, entry in enumerate(entries, start=1):
        if set(entry) != required:
            return False, f"entry {position} has an invalid shape"
        if entry["index"] != position:
            return False, f"entry {position} has an invalid index"
        if entry["previous"] != previous:
            return False, f"entry {position} breaks the chain"
        calculated = entry_hash(entry)
        if entry["entry_hash"] != calculated:
            return False, f"entry {position} hash does not match its content"
        previous = calculated
    return True, f"{len(entries)} ledger entries verified"


def make_entry(path: Path, display_path: str, index: int, previous: str, recorded_at: str) -> dict:
    entry = {
        "index": index,
        "recorded_at": recorded_at,
        "path": display_path,
        "size": path.stat().st_size,
        "sha256": hash_file(path),
        "previous": previous,
    }
    entry["entry_hash"] = entry_hash(entry)
    return entry


def record(ledger: Path, files: list[Path], recorded_at: str | None = None) -> list[dict]:
    entries = read_ledger(ledger)
    valid, message = verify_entries(entries)
    if not valid:
        raise ValueError(f"refusing to append: {message}")
    stamp = recorded_at or datetime.now(timezone.utc).isoformat()
    previous = entries[-1]["entry_hash"] if entries else GENESIS
    new_entries = []
    for file_path in files:
        if file_path.is_symlink():
            raise ValueError(f"not a regular file: {file_path}")
        path = file_path.resolve()
        if not path.is_file():
            raise ValueError(f"not a regular file: {file_path}")
        entry = make_entry(path, file_path.as_posix(), len(entries) + len(new_entries) + 1, previous, stamp)
        new_entries.append(entry)
        previous = entry["entry_hash"]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        for entry in new_entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return new_entries


def current_status(entries: list[dict], base: Path) -> list[dict]:
    latest: dict[str, dict] = {}
    for entry in entries:
        latest[entry["path"]] = entry
    results = []
    for name, entry in sorted(latest.items()):
        candidate = base / name
        path = candidate.resolve()
        if candidate.is_symlink() or not path.is_file():
            status = "missing"
        else:
            status = "unchanged" if hash_file(path) == entry["sha256"] else "changed"
        results.append({"path": name, "status": status})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    record_parser = subparsers.add_parser("record", help="Append snapshots for one or more files")
    record_parser.add_argument("ledger", type=Path)
    record_parser.add_argument("files", nargs="+", type=Path)
    verify_parser = subparsers.add_parser("verify", help="Verify ledger chain and optionally current files")
    verify_parser.add_argument("ledger", type=Path)
    verify_parser.add_argument("--check-files", action="store_true")
    verify_parser.add_argument("--base", type=Path, default=Path("."))
    verify_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "record":
            added = record(args.ledger, args.files)
            print(f"File Hash Ledger: recorded {len(added)} file snapshot(s).")
            return 0
        entries = read_ledger(args.ledger)
        valid, message = verify_entries(entries)
        statuses = current_status(entries, args.base) if valid and args.check_files else []
        if args.json:
            print(json.dumps({"valid": valid, "message": message, "files": statuses}, indent=2))
        else:
            print(f"File Hash Ledger: {'OK' if valid else 'FAILED'} — {message}")
            for item in statuses:
                print(f"[{item['status'].upper()}] {item['path']}")
        return 0 if valid and all(item["status"] == "unchanged" for item in statuses) else 1
    except (OSError, UnicodeError, ValueError) as error:
        print(f"File Hash Ledger: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
