#!/usr/bin/env python3
"""Estimate monthly automation costs from a bounded local JSON plan."""

from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 100_000
MAX_WORKFLOWS = 50
MONEY = Decimal("0.01")
INPUT_KEYS = {"currency", "days_per_month", "platform_monthly", "workflows"}
WORKFLOW_KEYS = {"name", "runs_per_day", "operations_per_run", "cost_per_1000_runs", "cost_per_1000_operations", "monthly_fixed_cost"}


class InputError(ValueError):
    """Raised when a plan is invalid or unsafe to estimate."""


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise InputError("file exceeds size limit")
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)
    except InputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("unable to read JSON input") from exc


def _decimal(value: Any, field: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InputError(f"{field} must be numeric")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise InputError(f"{field} must be numeric") from exc
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise InputError(f"{field} is outside the allowed range")
    return result


def estimate(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or set(plan) - INPUT_KEYS:
        raise InputError("plan contains unsupported fields")
    currency = plan.get("currency", "USD")
    if not isinstance(currency, str) or not currency.isalpha() or len(currency) != 3:
        raise InputError("currency must be a three-letter code")
    days = _decimal(plan.get("days_per_month", 30), "days_per_month", positive=True)
    platform = _decimal(plan.get("platform_monthly", 0), "platform_monthly")
    workflows = plan.get("workflows")
    if not isinstance(workflows, list) or not workflows or len(workflows) > MAX_WORKFLOWS:
        raise InputError("workflows must be a non-empty bounded list")

    names: set[str] = set()
    items = []
    variable_total = Decimal("0")
    fixed_total = platform
    for index, workflow in enumerate(workflows):
        if not isinstance(workflow, dict) or set(workflow) - WORKFLOW_KEYS:
            raise InputError(f"workflow {index + 1} contains unsupported fields")
        name = workflow.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise InputError(f"workflow {index + 1} requires a valid name")
        name = " ".join(name.split())
        if name.casefold() in names:
            raise InputError("workflow names must be unique")
        names.add(name.casefold())
        runs_day = _decimal(workflow.get("runs_per_day"), "runs_per_day")
        operations_run = _decimal(workflow.get("operations_per_run", 0), "operations_per_run")
        run_rate = _decimal(workflow.get("cost_per_1000_runs", 0), "cost_per_1000_runs")
        operation_rate = _decimal(workflow.get("cost_per_1000_operations", 0), "cost_per_1000_operations")
        fixed = _decimal(workflow.get("monthly_fixed_cost", 0), "monthly_fixed_cost")
        monthly_runs = runs_day * days
        monthly_operations = monthly_runs * operations_run
        run_cost = monthly_runs / Decimal(1000) * run_rate
        operation_cost = monthly_operations / Decimal(1000) * operation_rate
        total = run_cost + operation_cost + fixed
        variable_total += run_cost + operation_cost
        fixed_total += fixed
        items.append({
            "name": name,
            "monthly_runs": int(monthly_runs) if monthly_runs == monthly_runs.to_integral() else float(monthly_runs),
            "monthly_operations": int(monthly_operations) if monthly_operations == monthly_operations.to_integral() else float(monthly_operations),
            "run_cost": str(run_cost.quantize(MONEY, rounding=ROUND_HALF_UP)),
            "operation_cost": str(operation_cost.quantize(MONEY, rounding=ROUND_HALF_UP)),
            "fixed_cost": str(fixed.quantize(MONEY, rounding=ROUND_HALF_UP)),
            "estimated_total": str(total.quantize(MONEY, rounding=ROUND_HALF_UP)),
        })
    grand_total = variable_total + fixed_total
    return {
        "currency": currency.upper(),
        "days_per_month": float(days),
        "workflows": items,
        "totals": {
            "variable": str(variable_total.quantize(MONEY, rounding=ROUND_HALF_UP)),
            "fixed": str(fixed_total.quantize(MONEY, rounding=ROUND_HALF_UP)),
            "monthly_estimate": str(grand_total.quantize(MONEY, rounding=ROUND_HALF_UP)),
        },
        "note": "Estimate only. Compare the assumptions with current provider pricing before making a decision.",
    }


def format_text(report: dict[str, Any]) -> str:
    lines = ["Automation Cost Estimate", f"Currency: {report['currency']}", f"Days per month: {report['days_per_month']:g}", ""]
    for item in report["workflows"]:
        lines.extend([
            item["name"],
            f"  Runs: {item['monthly_runs']:,} | Operations: {item['monthly_operations']:,}",
            f"  Run cost: {item['run_cost']} | Operation cost: {item['operation_cost']} | Fixed: {item['fixed_cost']}",
            f"  Estimated total: {item['estimated_total']} {report['currency']}",
        ])
    totals = report["totals"]
    lines.extend(["", f"Variable: {totals['variable']} {report['currency']}", f"Fixed: {totals['fixed']} {report['currency']}", f"Monthly estimate: {totals['monthly_estimate']} {report['currency']}", "", report["note"]])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        report = estimate(load_json(args.plan))
    except InputError:
        print("Input error: unable to estimate the supplied plan.", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.as_json else format_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
