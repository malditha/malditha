# Cron Schedule Previewer

Day 056 of the 100 Days of Code challenge.

## Purpose

Cron Schedule Previewer turns a standard five-field cron expression into a short list of upcoming timestamps in one explicit IANA time zone. It helps review a schedule before copying it into an automation.

It does not execute jobs, connect to n8n, interpret seconds or year fields, or guarantee compatibility with every scheduler dialect. Day-of-month and day-of-week follow traditional cron OR semantics when both are restricted.

## Run

Requires Python 3.10 or newer and the system time-zone database.

```bash
python cron_schedule_previewer.py "0 9 * * 1-5" --timezone Asia/Manila --start 2026-10-25T00:00:00Z
python cron_schedule_previewer.py "*/15 * * * *" --timezone UTC --start 2026-10-25T00:00:00Z --json
```

Exit code `0` means a preview was created; `2` means the schedule input was invalid.

Run tests with `python -m unittest -v test_cron_schedule_previewer.py`.

## Boundaries

- Five fields: minute, hour, day of month, month and day of week
- Supports wildcards, lists, ranges and positive steps
- Day of week uses 0 for Sunday through 6 for Saturday
- Produces 1–20 runs and searches at most five years
- Requires an offset-aware ISO 8601 starting timestamp

## Skills practiced

Cron parsing, time-zone conversion, daylight-saving-safe UTC iteration, bounded validation, deterministic reporting and standard-library testing.

## Next improvement

Add named months and weekdays behind an explicit dialect option.
