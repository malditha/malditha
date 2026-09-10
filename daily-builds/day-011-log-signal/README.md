# Day 011 — Log Signal

A dependency-free Python CLI that scans plain-text application logs and turns repeated messages into a compact incident summary.

## Purpose

Long log files make it easy to miss the few patterns that matter. Log Signal recognizes common severity labels, groups changing IDs and network addresses into stable signatures, counts unmatched lines and returns a failing exit code when errors are present.

## Run

Use the included sample:

```bash
python3 log_signal.py sample.log
```

Read from standard input and emit JSON:

```bash
cat sample.log | python3 log_signal.py - --json
```

Limit the recurring-signals table:

```bash
python3 log_signal.py sample.log --top 3
```

The command exits with status `1` when `ERROR`, `CRITICAL` or `FATAL` entries are found. Use `--no-fail` when the report is informational.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile log_signal.py
```

## Skills practiced

- Python dataclasses and type hints
- Regular-expression parsing and normalization
- `collections.Counter` aggregation
- CLI design with `argparse`
- JSON and human-readable reporting
- Exit codes and standard-input workflows
- Unit testing with the standard library

## Next improvement

Add opt-in parsers for structured JSON logs while keeping unknown fields and sensitive values out of the summary by default.
