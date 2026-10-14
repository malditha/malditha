# Log Rotation Planner

Day 045 — Linux, DevOps & reliability.

## Purpose

Estimate a log storage budget before choosing rotation and retention settings. This dependency-free CLI calculates archive count, active and compressed archive storage, a modeled peak and remaining budget.

## Run

Python 3.10+; no installation required.

```sh
python log_rotation_planner.py --daily-mb 100 --retention-days 14 --compression-ratio 0.25 --budget-mb 1000
python log_rotation_planner.py --daily-mb 100 --budget-mb 1000 --json
python -m unittest -v
```

Exit `0`: modeled peak within budget; `1`: over budget; `2`: invalid assumptions.

## Model and limits

All sizes use decimal MB. Daily growth is assumed constant. Archives are rounded up to whole rotation intervals, so effective archive retention can exceed the requested days. The current active interval is additional to archive retention. The compression ratio is compressed size / original size; `1` means no compression. The peak adds one extra uncompressed interval to cover a modeled rotation overlap. Real compression, bursts, delayed cleanup, temporary copies and filesystem overhead can exceed this estimate. This is a planning model, not a guarantee or a logrotate configuration generator. It reads no logs and changes no files or services.

## Skills practiced

Capacity modeling, interval rounding, finite-number validation, CLI exit codes, JSON reporting, and standard-library testing.

## Next improvement

Compare measured daily growth over several days and show a separate burst allowance.
