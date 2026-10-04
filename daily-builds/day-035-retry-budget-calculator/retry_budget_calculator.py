#!/usr/bin/env python3
"""Calculate how many retry delays fit inside a fixed wait budget."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING


@dataclass(frozen=True)
class RetryPlan:
    budget_ms: int
    retries_requested: int
    retries_allowed: int
    total_attempts: int
    wait_used_ms: int
    remaining_ms: int
    delays_ms: list[int]
    next_delay_ms: int | None
    fits_all_requested: bool


def decimal_value(value: str | int | float | Decimal, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"{name} must be a number") from error
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result


def calculate_retry_plan(
    budget_ms: int,
    initial_delay_ms: int,
    multiplier: str | Decimal,
    max_delay_ms: int,
    jitter_percent: str | Decimal = "0",
    max_retries: int = 10,
) -> RetryPlan:
    """Return a conservative retry plan; request execution time is excluded."""
    if not 1 <= budget_ms <= 86_400_000:
        raise ValueError("budget_ms must be between 1 and 86400000")
    if not 1 <= initial_delay_ms <= 86_400_000:
        raise ValueError("initial_delay_ms must be between 1 and 86400000")
    if not 1 <= max_delay_ms <= 86_400_000:
        raise ValueError("max_delay_ms must be between 1 and 86400000")
    if initial_delay_ms > max_delay_ms:
        raise ValueError("initial_delay_ms cannot exceed max_delay_ms")
    if not 1 <= max_retries <= 100:
        raise ValueError("max_retries must be between 1 and 100")

    multiplier_value = decimal_value(multiplier, "multiplier")
    jitter_value = decimal_value(jitter_percent, "jitter_percent")
    if not Decimal("1") <= multiplier_value <= Decimal("10"):
        raise ValueError("multiplier must be between 1 and 10")
    if not Decimal("0") <= jitter_value <= Decimal("100"):
        raise ValueError("jitter_percent must be between 0 and 100")

    factor = Decimal("1") + jitter_value / Decimal("100")
    delays: list[int] = []
    wait_used = 0
    next_delay: int | None = None

    for retry_index in range(max_retries):
        uncapped = Decimal(initial_delay_ms) * (multiplier_value ** retry_index)
        base_delay = min(uncapped, Decimal(max_delay_ms))
        reserved_delay = int((base_delay * factor).to_integral_value(rounding=ROUND_CEILING))
        if wait_used + reserved_delay > budget_ms:
            next_delay = reserved_delay
            break
        delays.append(reserved_delay)
        wait_used += reserved_delay

    return RetryPlan(
        budget_ms=budget_ms,
        retries_requested=max_retries,
        retries_allowed=len(delays),
        total_attempts=len(delays) + 1,
        wait_used_ms=wait_used,
        remaining_ms=budget_ms - wait_used,
        delays_ms=delays,
        next_delay_ms=next_delay,
        fits_all_requested=len(delays) == max_retries,
    )


def render_text(plan: RetryPlan) -> str:
    delays = ", ".join(f"{delay} ms" for delay in plan.delays_ms) or "none"
    next_delay = "none" if plan.next_delay_ms is None else f"{plan.next_delay_ms} ms"
    return "\n".join(
        [
            "RETRY BUDGET PLAN",
            f"Retries allowed: {plan.retries_allowed}/{plan.retries_requested}",
            f"Total attempts: {plan.total_attempts} (initial attempt + retries)",
            f"Reserved delays: {delays}",
            f"Wait used: {plan.wait_used_ms} ms",
            f"Wait remaining: {plan.remaining_ms} ms",
            f"Next delay that does not fit: {next_delay}",
            "Note: operation time and network latency are not included.",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-ms", type=int, required=True)
    parser.add_argument("--initial-delay-ms", type=int, required=True)
    parser.add_argument("--multiplier", default="2")
    parser.add_argument("--max-delay-ms", type=int, required=True)
    parser.add_argument("--jitter-percent", default="0")
    parser.add_argument("--max-retries", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = calculate_retry_plan(
            args.budget_ms,
            args.initial_delay_ms,
            args.multiplier,
            args.max_delay_ms,
            args.jitter_percent,
            args.max_retries,
        )
    except ValueError as error:
        raise SystemExit(f"error: {error}") from error
    print(json.dumps(asdict(plan), indent=2) if args.as_json else render_text(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
