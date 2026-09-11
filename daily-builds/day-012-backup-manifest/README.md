# Day 012 — Backup Manifest

A dependency-free Python CLI that records a backup directory's files, sizes and SHA-256 checksums, then verifies that snapshot later.

## Purpose

A backup file existing is not proof that its contents stayed intact. Backup Manifest creates a portable JSON inventory and reports missing, changed or unexpected files without uploading the backup or reading anything outside the chosen directory.

## Run

Create a manifest:

```bash
python3 backup_manifest.py create sample-backup --output sample-manifest.json
```

Verify the directory:

```bash
python3 backup_manifest.py verify sample-backup sample-manifest.json
```

Verification exits with status `1` when a difference is found, making it useful in local scripts and scheduled checks.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile backup_manifest.py
```

## Skills practiced

- Recursive file traversal with `pathlib`
- Streaming SHA-256 hashing
- Stable, portable relative paths
- JSON serialization and validation
- CLI subcommands and exit codes
- Temporary-directory integration tests

## Next improvement

Add an opt-in signed-manifest workflow so a verifier can check both the backup files and the manifest's origin.
