# Day 016 — File Hash Ledger

A dependency-free Python CLI that records sequential SHA-256 file snapshots in a tamper-evident JSONL ledger.

## Purpose

A one-time checksum confirms one version of a file, but it does not explain how that file changed across later checks. File Hash Ledger appends compact metadata snapshots—timestamp, path, size and SHA-256—and cryptographically links each ledger entry to the previous one.

It never stores file contents and never modifies tracked files. The chain is tamper-evident, not a digital signature or a replacement for protected audit storage.

## Run

From this project directory:

```bash
python3 hash_ledger.py record sample-ledger.jsonl sample-files/config.txt
python3 hash_ledger.py verify sample-ledger.jsonl --check-files
```

For a machine-readable verification result:

```bash
python3 hash_ledger.py verify sample-ledger.jsonl --check-files --json
```

Exit code `0` means the ledger and requested file check are valid, `1` means verification or current-file comparison failed, and `2` means the input could not be processed.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile hash_ledger.py
```

## Skills practiced

- Streaming SHA-256 file hashing
- JSON Lines persistence
- Canonical JSON serialization
- Hash-linked, tamper-evident records
- Current-file change detection
- Defensive validation and safe append behavior
- Standard-library unit tests

## Next improvement

Add optional Ed25519 signatures so ledger authenticity can be verified independently with a public key.
