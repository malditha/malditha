# Cron Explainer

A dependency-free Python CLI that validates a standard five-field cron expression, explains each field and previews its next matching local times. It solves a focused problem: reviewing a schedule before placing it in crontab or an automation tool.

Cron Explainer does not install, edit or run scheduled jobs. It supports `*`, lists, ranges, steps, three-letter month names and three-letter weekday names. When both day-of-month and day-of-week are restricted, it follows common cron behavior: either may match.

## Run

Requires Python 3.11 or newer.

```bash
python3 cron_explainer.py "*/15 9-17 * * mon-fri" --from 2026-09-18T09:00
python3 cron_explainer.py "30 8 1 * *" --from 2026-09-18T09:00 --count 3 --json
```

Without `--from`, the preview starts from the computer's current local wall-clock time. Cron behavior can vary by implementation, timezone and daylight-saving configuration, so verify the final expression in the system that will run it.

## Test

```bash
python3 -m unittest discover -s tests -v
```

The tests use fixed dates and do not create or execute scheduled jobs.

## Skills practiced

- Tokenization and validation of a compact schedule language
- Range, list, step and named-value expansion
- Cron day-of-month/day-of-week matching semantics
- Deterministic date-time previews
- Human-readable and JSON CLI reports
- Standard-library unit tests

## Next improvement

Add explicit IANA timezone input with daylight-saving transition warnings while keeping previews deterministic.
