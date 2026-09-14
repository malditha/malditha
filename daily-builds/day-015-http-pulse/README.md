# Day 015 — HTTP Pulse

A dependency-free Python CLI that checks a small list of HTTP endpoints and summarizes status, latency and failures.

## Purpose

When several websites or health endpoints need a quick first-pass check, opening each one manually is slow and inconsistent. HTTP Pulse validates a plain-text URL list, checks each endpoint with a configurable timeout, and returns a compact human-readable or JSON report.

It performs ordinary HTTP requests only. It does not bypass authentication, crawl pages, inspect response bodies or claim to replace production monitoring.

## Run

Create a local URL file from the safe example, then run:

```bash
cp urls.example.txt urls.txt
python3 http_pulse.py urls.txt
```

For automation-friendly output:

```bash
python3 http_pulse.py urls.txt --timeout 3 --json
```

Exit code `0` means every endpoint returned HTTP 2xx or 3xx, `1` means at least one check failed, and `2` means the input file was invalid or unreadable.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile http_pulse.py
```

Tests use deterministic fake responses and make no external network requests.

## Skills practiced

- URL parsing and input validation
- Python `urllib` requests and error handling
- Monotonic latency measurement
- Immutable result records
- Text and JSON reporting
- Automation-friendly exit codes
- Dependency injection and network-free unit tests

## Next improvement

Add bounded concurrent checks with a configurable worker limit while preserving stable report ordering.
