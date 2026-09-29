# Patch Log Formatter

Day 030 of the 100 Days of Code challenge.

Patch Log Formatter turns a small, sanitized JSON export of Frappe patch executions into a chronological review report. It summarizes successful, failed, and skipped patches and calculates durations without reading raw logs or connecting to a bench.

## Run it

Requires Python 3.10+ and no third-party packages.

```bash
python3 patch_log_formatter.py sample-patch-log.json
python3 patch_log_formatter.py sample-patch-log.json --format json
```

Exit code `0` means no failed patches were reported, `1` means at least one failed patch was reported, and `2` means the input could not be read or validated.

Run the tests:

```bash
python3 -m unittest -v
```

## Input contract

The input must be a JSON array of at most 200 records. Each record contains only:

- `patch`: a dotted patch identifier
- `status`: `success`, `failed`, or `skipped`
- `started_at`: an ISO-8601 timestamp with timezone
- `finished_at`: an ISO-8601 timestamp with timezone

Unknown fields are rejected deliberately. This prevents raw tracebacks, SQL, credentials, or other arbitrary log content from being copied into the report. The included sample is fictional.

## Skills practiced

- Defensive JSON validation
- Timezone-aware timestamp normalization
- Deterministic sorting and aggregation
- Human-readable and machine-readable CLI output
- Automation-friendly exit codes
- Standard-library unit testing

## Safety boundary

This tool formats already-sanitized records. It does not execute patches, read bench logs, connect to Frappe or ERPNext, inspect a database, or modify any system.

## Next improvement

Add an optional comparison mode for reviewing two sanitized patch summaries across separate deployments.
