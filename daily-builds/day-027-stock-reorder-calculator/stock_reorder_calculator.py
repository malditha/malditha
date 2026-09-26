#!/usr/bin/env python3
"""Calculate offline stock reorder suggestions from sanitized JSON input."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class InputError(ValueError):
    pass


@dataclass(frozen=True)
class Recommendation:
    item_code: str
    reorder_point: float
    available_supply: float
    shortage: float
    recommended_order_qty: float
    status: str


ALLOWED_KEYS = {
    "item_code", "current_qty", "on_order_qty", "average_daily_usage",
    "lead_time_days", "safety_stock", "minimum_order_qty", "pack_size",
}


def number(row: dict[str, Any], key: str, default: float = 0) -> float:
    value = row.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{key} must be a number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise InputError(f"{key} must be finite and zero or greater")
    return value


def calculate(row: dict[str, Any]) -> Recommendation:
    if not isinstance(row, dict):
        raise InputError("Each item must be a JSON object")
    unknown = set(row) - ALLOWED_KEYS
    if unknown:
        raise InputError(f"Unsupported properties: {', '.join(sorted(unknown))}")

    item_code = row.get("item_code")
    if not isinstance(item_code, str) or not item_code.strip() or len(item_code) > 80:
        raise InputError("item_code must be a non-empty string up to 80 characters")

    current = number(row, "current_qty")
    on_order = number(row, "on_order_qty")
    daily_usage = number(row, "average_daily_usage")
    lead_days = number(row, "lead_time_days")
    safety = number(row, "safety_stock")
    minimum = number(row, "minimum_order_qty")
    pack_size = number(row, "pack_size", 1)
    if pack_size <= 0:
        raise InputError("pack_size must be greater than zero")

    reorder_point = daily_usage * lead_days + safety
    available = current + on_order
    shortage = max(0.0, reorder_point - available)
    if shortage == 0:
        quantity = 0.0
        status = "sufficient"
    else:
        raw_quantity = max(shortage, minimum)
        quantity = math.ceil(raw_quantity / pack_size) * pack_size
        status = "reorder"

    return Recommendation(
        item_code=item_code.strip(),
        reorder_point=round(reorder_point, 4),
        available_supply=round(available, 4),
        shortage=round(shortage, 4),
        recommended_order_qty=round(quantity, 4),
        status=status,
    )


def calculate_all(data: Any) -> list[Recommendation]:
    if not isinstance(data, list):
        raise InputError("Input must be a JSON array")
    if not 1 <= len(data) <= 500:
        raise InputError("Input must contain between 1 and 500 items")
    seen: set[str] = set()
    results: list[Recommendation] = []
    for index, row in enumerate(data):
        try:
            result = calculate(row)
        except InputError as error:
            raise InputError(f"Item {index + 1}: {error}") from error
        normalized = result.item_code.casefold()
        if normalized in seen:
            raise InputError(f"Item {index + 1}: duplicate item_code {result.item_code!r}")
        seen.add(normalized)
        results.append(result)
    return sorted(results, key=lambda item: item.item_code.casefold())


def render_text(results: list[Recommendation]) -> str:
    lines = ["STOCK REORDER REPORT", ""]
    for item in results:
        lines.extend([
            f"{item.item_code}: {item.status.upper()}",
            f"  reorder point: {item.reorder_point:g}",
            f"  available supply: {item.available_supply:g}",
            f"  shortage: {item.shortage:g}",
            f"  suggested order: {item.recommended_order_qty:g}",
        ])
    lines.extend(["", "Planning output only; no stock or purchase order was changed."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calculate offline stock reorder suggestions.")
    parser.add_argument("input", type=Path, help="Sanitized JSON item array")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        results = calculate_all(data)
    except (OSError, json.JSONDecodeError, InputError) as error:
        print(json.dumps({"ok": False, "error": str(error)}) if args.json else f"ERROR: {error}")
        return 2
    if args.json:
        print(json.dumps({"ok": True, "items": [asdict(item) for item in results]}, indent=2))
    else:
        print(render_text(results))
    return 1 if any(item.status == "reorder" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
