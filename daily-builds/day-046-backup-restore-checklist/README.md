# Backup Restore Checklist

Day 046 — Linux, DevOps & reliability.

## Purpose

Review a local restore-drill record for six checks: backup identity, integrity, isolated target, completed restore, data validation and application workflow. Failed checks block the record; missing checks or passes without recorded evidence remain unverified.

## Run

Python 3.10+, no dependencies:

```sh
python restore_checklist.py sample.json
python restore_checklist.py sample.json --json
python -m unittest -v
```

Exit `0` means the supplied record is complete, `1` means blocked or incomplete, and `2` means invalid input. The sample intentionally exits `1` because validation remains unfinished.

## Input and boundaries

Use the check IDs in sample.json with status `pass`, `fail` or `unverified`. A pass requires boolean `evidence_recorded: true`. The report omits arbitrary notes and extra record fields. Unknown check IDs are rejected to catch typos. Input is limited to 1 MiB. Keep actual evidence in an appropriate controlled location; the tool does not inspect it, access backups, run restore commands or prove recoverability. Record completion describes declarations, not an independent recovery certification.

## Skills practiced

Recovery-drill modeling, defensive JSON validation, evidence-aware state aggregation, data minimization, CLI exit codes and standard-library tests.

## Next improvement

Add a versioned record format with optional drill dates and repeat-review reminders.
