"""Estimate a log rotation storage budget from explicit planning assumptions."""
import argparse
import json
import math
import sys


def plan(daily_mb, interval_days, retention_days, compression_ratio, budget_mb):
    values = [daily_mb, interval_days, retention_days, compression_ratio, budget_mb]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("all inputs must be finite numbers")
    if not 0 < daily_mb <= 1000000 or not 0 < budget_mb <= 1000000000:
        raise ValueError("daily growth and budget must be positive and within bounds")
    if not isinstance(interval_days, int) or not isinstance(retention_days, int):
        raise ValueError("interval and retention must be whole days")
    if not 1 <= interval_days <= retention_days <= 3650:
        raise ValueError("require 1 <= interval <= retention <= 3650 days")
    if not 0 < compression_ratio <= 1:
        raise ValueError("compression ratio must be greater than 0 and at most 1")
    archives = math.ceil(retention_days / interval_days)
    active = daily_mb * interval_days
    archived = active * archives * compression_ratio
    steady = active + archived
    peak = steady + active
    return {
        "assumptions": {"daily_mb": daily_mb, "interval_days": interval_days,
                        "retention_days": retention_days, "compression_ratio": compression_ratio,
                        "budget_mb": budget_mb},
        "archive_count": archives,
        "effective_archive_days": archives * interval_days,
        "active_mb": round(active, 3), "archives_mb": round(archived, 3),
        "steady_mb": round(steady, 3), "peak_mb": round(peak, 3),
        "headroom_mb": round(budget_mb - peak, 3),
        "status": "within_budget" if peak <= budget_mb else "over_budget",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--daily-mb", type=float, required=True)
    p.add_argument("--interval-days", type=int, default=1)
    p.add_argument("--retention-days", type=int, default=14)
    p.add_argument("--compression-ratio", type=float, default=1)
    p.add_argument("--budget-mb", type=float, required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        result = plan(args.daily_mb, args.interval_days, args.retention_days,
                      args.compression_ratio, args.budget_mb)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        print("Log Rotation Planner — estimates in decimal MB")
        for key in ("archive_count", "effective_archive_days", "active_mb", "archives_mb", "steady_mb", "peak_mb", "headroom_mb", "status"):
            print(f"{key}: {result[key]}")
        print("Peak includes one extra uncompressed rotation. Validate actual growth and rotation behavior separately.")
    return 0 if result["status"] == "within_budget" else 1


if __name__ == "__main__":
    raise SystemExit(main())
