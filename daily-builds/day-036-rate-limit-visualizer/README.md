# Rate Limit Visualizer

A dependency-free Python CLI that evaluates sanitized request timestamps against a fixed-window rate limit. It shows usage, remaining capacity, reset timing, status and a compact utilization bar without contacting an API.

## Run

```bash
python rate_limit_visualizer.py \
  --limit 5 \
  --window-seconds 60 \
  --now 2026-10-05T00:00:30Z \
  --timestamps-json '["2026-10-05T00:00:01Z","2026-10-05T00:00:20Z"]'
```

Add `--json` for machine-readable output.

## Test

```bash
python -m unittest -v
```

## What it reports

- requests used and remaining
- utilization percentage and bar
- healthy, warning or blocked status
- current fixed-window boundaries
- seconds until the next window

This is an educational fixed-window model. It does not call an API, bypass limits, or reproduce token-bucket, sliding-window or provider-specific behavior.

## Skills practiced

- fixed-window rate-limit arithmetic
- timezone-aware ISO 8601 parsing
- defensive, bounded input validation
- deterministic text and JSON reporting
- test-first Python development

## Next improvement

Add an explicit sliding-window mode and compare its behavior against the fixed-window result.
