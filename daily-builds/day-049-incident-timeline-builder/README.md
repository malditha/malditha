# Incident Timeline Builder — Day 049

A dependency-free Python CLI that turns a small, sanitized incident-event record into a chronological timeline. It normalizes explicit timezone offsets to UTC and reports each event's elapsed time from the first event and gap from the previous event.

## Run

Requires Python 3.10 or newer. No installation or external services required.

```sh
python timeline.py sample.json
python timeline.py sample.json --json
python -m unittest -v
```

The synthetic sample spans **720 seconds**, with gaps of **0, 300 and 420 seconds**. Output goes to stdout; files are never changed. Exit codes: `0` for a valid report, `2` for invalid/unreadable input or CLI usage.

## Input

Provide an object with an `events` array (1–1000 records). Each event requires:

- `id`: unique ASCII identifier, 1–64 characters; letters/digits then letters/digits/underscore/dot/hyphen.
- `at`: ISO timestamp with date, `T`, seconds, optional 1–6 fractional digits, and `Z` or an explicit offset up to ±14:00. Input years: 2000–2100. No naive timestamps or leap seconds.
- `kind`: `detected`, `investigating`, `mitigated`, `resolved` or `note`.
- `label`: a nonblank, single-line description up to 160 characters, with Unicode control/format characters rejected.

Input is capped at 1,000,000 bytes; duplicate JSON keys and duplicate event IDs are rejected. Events at the same instant retain their input order. Decimal-second strings preserve microsecond precision without floating-point calculations. Unknown fields are omitted from the report and the input object is not mutated.

## Scope and safety

Use only authorized, manually sanitized records. **IDs and labels are deliberately printed**: this is not an automatic secret or personal-data redactor. Remove sensitive details before use. Error output does not include source values, paths or parser excerpts.

The span is the first-to-last supplied event, **not verified downtime, time to recovery, MTTR or a causal analysis**. Event kinds are annotations, not an enforced incident-state machine. The tool does not fetch logs, probe networks, connect to infrastructure, infer missing events, or modify records. Accurate ordering still depends on accurate clocks and timestamps.

## Skills practiced

Timezone-aware datetime arithmetic, stable sorting, exact duration formatting, defensive JSON/file boundaries, data minimization, CLI exit codes, and standard-library unit/integration tests.

## Next improvement

Add an explicit user-selected measurement interval for separate response/recovery metrics, with tests and clear definitions; do not infer these from labels.
