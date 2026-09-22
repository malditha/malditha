# Worker Queue Reader

Day 023 of 100 Days of Code.

## Purpose

Worker Queue Reader turns a small, sanitized Frappe worker-queue snapshot into a clear health summary. It shows queue depth, active-worker coverage and the age of the oldest pending job so an operator can spot stale or uncovered queues without opening Redis or changing any jobs.

The tool reads only the supplied JSON file. It does not connect to Redis, execute Bench commands, dequeue jobs or include arbitrary fields from the input in its report.

## Run

```bash
python3 worker_queue_reader.py example-snapshot.json
python3 worker_queue_reader.py example-snapshot.json --stale-after 600 --json
```

Exit codes are `0` for a clear snapshot, `1` when a stale or uncovered queue needs attention, and `2` for invalid input.

Run the tests:

```bash
python3 -m unittest -v
```

## Snapshot format

Provide `captured_at`, a `queues` array with names, pending counts and optional oldest-enqueued timestamps, plus a `workers` array with status and subscribed queue names. Use sanitized operational metadata only—never export job arguments, payloads or credentials.

## Skills practiced

- Frappe worker-queue concepts
- Timezone-aware age calculations
- Defensive JSON validation
- Privacy-conscious reporting
- Automation-friendly exit codes
- Standard-library tests

## Next improvement

Accept separate before-and-after snapshots and report queue-depth trends while keeping individual job data out of the output.
