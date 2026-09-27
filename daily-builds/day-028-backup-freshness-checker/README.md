# Backup Freshness Checker

Backup Freshness Checker is a dependency-free Python CLI that evaluates sanitized backup timestamps against an explicit maximum age. It classifies each supplied site as fresh, stale, missing or future-dated and produces deterministic text or JSON output.

It reviews metadata only. It does not connect to Frappe or ERPNext, discover backup files, open archives, verify contents, restore data, delete files or change a backup schedule.

## Run

Requires Python 3.10 or newer.

```bash
cd daily-builds/day-028-backup-freshness-checker
python3 backup_freshness_checker.py sample-backups.json --now 2026-09-27T00:00:00Z
python3 backup_freshness_checker.py sample-backups.json --now 2026-09-27T00:00:00Z --json
```

The explicit `--now` value makes reports and tests reproducible. The command returns exit code `0` when every backup is fresh, `1` when any record is stale, missing or future-dated, and `2` for invalid input.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile backup_freshness_checker.py
```

## Skills practiced

- Timezone-aware timestamp parsing
- Backup freshness policies and status classification
- Defensive, bounded JSON validation
- Deterministic text and JSON reporting
- Standard-library unit testing

## Next improvement

Add an optional second timestamp for the latest file backup so database and file-backup freshness can be reviewed independently, while keeping inputs sanitized and read-only.
