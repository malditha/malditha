# Uptime SLA Calculator

Day 048 — Linux, DevOps & reliability.

## Purpose

Convert a time-based availability target into an allowed downtime budget for an explicit measurement window. Compare supplied downtime with that budget, report observed availability and show remaining or exceeded minutes.

## Run

Python 3.10+, no third-party dependencies:

```sh
python sla.py --period-days 30 --target-percent 99.9 --downtime-minutes 20
python sla.py --period-days 30 --target-percent 99.9 --downtime-minutes 44 --json
python -m unittest -v
```

Exit `0`: within budget (including exact equality); `1`: over budget; `2`: invalid input. JSON numeric results are decimal strings to retain precision. Availability is displayed to nine decimal places, but the status uses the unrounded downtime budget.

## Model and limits

Window minutes = days × 1440. Allowed downtime = window × (100 − target) / 100. Observed availability = (window − downtime) / window × 100. Days may be fractional; no calendar-month length is assumed. Inputs support up to 18 significant digits and nine decimal places. Window is bounded to 3660 days, target to greater than zero through 100%, and downtime to zero through the window length.

Use only downtime that belongs to your chosen measurement definition. Merge overlapping incidents before summing durations. Maintenance exclusions, partial failures, request-based SLIs, service credits and provider contract rules are outside this model. It does not monitor services or certify contractual compliance.

## Skills practiced

Decimal arithmetic, availability modeling, exact boundary comparisons, defensive numeric validation, CLI reports and standard-library testing.

## Next improvement

Add timestamped incident intervals with overlap merging and explicit exclusions.
