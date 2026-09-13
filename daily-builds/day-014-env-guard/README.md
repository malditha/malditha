# Day 014 — Env Guard

A dependency-free Python CLI that compares environment-variable names with a template without displaying their values.

## Purpose

Configuration mistakes often appear only after an application starts: a required key is missing, an old key remains, or a line is malformed. Env Guard performs a safe local preflight check using key names only. It reports missing, unexpected, duplicate and malformed entries while deliberately discarding values.

## Run

```bash
python3 env_guard.py .env.example sample.env
```

Use JSON output in a local script or CI check:

```bash
python3 env_guard.py .env.example sample.env --json
```

Exit code `0` means the files match, `1` means configuration differences were found, and `2` means an input file could not be read.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile env_guard.py
```

## Skills practiced

- Safe line-oriented configuration parsing
- Input validation and duplicate detection
- Set comparison and deterministic reports
- Data minimization for secret-bearing files
- JSON output and automation-friendly exit codes
- Standard-library unit and CLI integration tests

## Next improvement

Add optional schema rules for variable types and allowed formats while continuing to keep actual values out of reports.
