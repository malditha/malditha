# Service Health Board

Day 044 of the 100 Days of Code challenge.

## Purpose

Service Health Board turns a small local JSON snapshot into a deterministic health summary. It distinguishes healthy, degraded, down, unknown, and stale observations without probing networks, running service commands, or changing infrastructure.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python service_health_board.py sample_snapshot.json
python service_health_board.py sample_snapshot.json --json
python -m unittest -v test_service_health_board.py
```

Exit code `0` means every service is healthy, `1` means the board needs review, and `2` means the input is invalid. Inputs are limited to 2 MiB and 100 services. Extra fields are ignored so notes, tokens, and other arbitrary values are not copied into reports.

## Skills practiced

- Defensive JSON validation and bounded input handling
- Timezone-aware freshness calculations
- Deterministic status aggregation and sorting
- Privacy-conscious reporting and automation-friendly exit codes
- Standard-library unit and CLI testing

## Next improvement

Add an optional HTML export with accessible status labels while keeping data collection outside the tool.
