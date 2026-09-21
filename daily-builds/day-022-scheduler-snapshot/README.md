# Scheduler Snapshot

Scheduler Snapshot is a dependency-free, read-only Python CLI that records the scheduler-related configuration state of each discovered Frappe or ERPNext site and compares saved snapshots for drift.

It reads only `pause_scheduler` and `maintenance_mode`, records where each setting came from, and omits every other configuration key and value. It does not connect to MariaDB or Redis, execute Bench commands, inspect queues, or change the bench.

## Run it

Requires Python 3.11 or newer.

```bash
python3 scheduler_snapshot.py snapshot /path/to/frappe-bench
python3 scheduler_snapshot.py snapshot /path/to/frappe-bench --output before.json
python3 scheduler_snapshot.py compare before.json after.json
python3 scheduler_snapshot.py compare before.json after.json --json
```

Exit code `0` means all discovered sites are enabled or two snapshots match. Exit code `1` means a site is paused/in maintenance or snapshot drift was found. Exit code `2` means the input could not be inspected.

## Test it

```bash
python3 -m unittest -v
```

The tests use fictional temporary benches and require no Frappe installation, database, Redis service, network access or private data.

## Skills practiced

- Frappe common and per-site configuration precedence
- Allowlisted, privacy-conscious configuration inspection
- Deterministic JSON snapshots and drift comparison
- CLI subcommands and automation-friendly exit codes
- Standard-library unit testing

## Limits

This tool reports configuration intent, not runtime scheduler or worker health. A site shown as enabled may still have database, Redis, worker or queue problems.

## Next improvement

Add an explicit opt-in importer for sanitized scheduler status exported separately by an administrator, without executing Bench commands from this tool.
