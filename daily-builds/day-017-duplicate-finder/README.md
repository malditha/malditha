# Day 017 — Duplicate Finder

A read-only Python CLI that finds byte-identical files inside a directory. It groups candidates by file size before calculating SHA-256 hashes, so obviously different files are never hashed against each other.

## Problem

Repeated downloads and copied folders can quietly waste storage. Filenames are not reliable proof of duplication, and an automatic deletion tool is too risky for a small first pass.

Duplicate Finder reports exact matches and the space that extra copies occupy. It never deletes or modifies scanned files.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
cd daily-builds/day-017-duplicate-finder
python3 duplicate_finder.py /path/to/folder
python3 duplicate_finder.py /path/to/folder --json
```

Run the tests:

```bash
python3 -m unittest discover -s tests -v
```

Exit code `0` means the scan completed normally, `1` means one or more files could not be read, and `2` means the directory argument was invalid.

## Safety boundaries

- Read-only: no deletion, moving or renaming
- SHA-256 confirms byte-identical content; matching names alone do not count
- Symbolic links are skipped, including linked directories
- Only relative paths, sizes and hashes appear in reports; file contents are never stored
- “Potentially reclaimable” assumes one copy per group is kept and is not an instruction to delete

## Skills practiced

- Recursive filesystem traversal
- Candidate grouping and streaming SHA-256 hashing
- Immutable report models
- Human-readable and JSON CLI output
- Deterministic standard-library tests

## Next improvement

Add explicit ignore patterns so generated directories and known archives can be excluded before scanning.
