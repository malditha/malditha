"""Calculate a simple time-based availability budget using decimal arithmetic."""
import argparse
from decimal import Decimal, InvalidOperation
import json
import sys


def number(value, label):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a finite decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    if len(result.as_tuple().digits) > 18 or result.as_tuple().exponent < -9:
        raise ValueError(f"{label} supports 18 digits and 9 decimal places")
    return result


def render(value):
    return format(value.normalize(), "f") if value else "0"


def calculate(period_days, target_percent, downtime_minutes=0):
    days = number(period_days, "period days")
    target = number(target_percent, "target percent")
    downtime = number(downtime_minutes, "downtime minutes")
    if not 0 < days <= 3660:
        raise ValueError("period days must be greater than zero and at most 3660")
    if not 0 < target <= 100:
        raise ValueError("target percent must be greater than zero and at most 100")
    total = days * 1440
    if not 0 <= downtime <= total:
        raise ValueError("downtime must be between zero and the measurement window")
    allowed = total * (100 - target) / 100
    remaining = allowed - downtime
    availability = (total - downtime) * 100 / total
    return {"period_days": render(days), "target_percent": render(target),
            "window_minutes": render(total), "downtime_minutes": render(downtime),
            "allowed_downtime_minutes": render(allowed),
            "remaining_budget_minutes": render(remaining),
            "observed_availability_percent": format(availability, ".9f"),
            "status": "within_budget" if remaining >= 0 else "over_budget",
            "scope": "Simple time-based model; exclusions, service credits and contract rules are not evaluated."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--period-days", required=True)
    p.add_argument("--target-percent", required=True)
    p.add_argument("--downtime-minutes", default="0")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        result = calculate(args.period_days, args.target_percent, args.downtime_minutes)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Uptime SLA Calculator")
        for key, value in result.items(): print(f"{key}: {value}")
    return 0 if result["status"] == "within_budget" else 1


if __name__ == "__main__": raise SystemExit(main())
