# Day 013 — Disk Map

A dependency-free Python CLI that summarizes where a local directory uses space without following symbolic links.

## Purpose

Disk usage becomes difficult to investigate when the only visible number is a nearly full drive. Disk Map provides a safe first-pass report: total files and bytes, usage grouped by file extension, and the largest individual files. It reads metadata locally, never deletes anything and does not cross symlink boundaries.

## Run

```bash
python3 disk_map.py sample-directory
```

Choose how many large files to show or produce JSON for another local tool:

```bash
python3 disk_map.py sample-directory --top 5
python3 disk_map.py sample-directory --json
```

## Test

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile disk_map.py
```

## Skills practiced

- Safe recursive traversal with `os.walk` and `pathlib`
- File-size aggregation and stable sorting
- Human-readable binary size formatting
- Symlink boundary handling
- CLI arguments, JSON output and exit codes
- Temporary-directory integration tests

## Next improvement

Add an opt-in comparison mode that shows which directories grew between two saved scans without storing file contents.
