#!/usr/bin/env python3
"""Simulate deterministic offset pagination without requesting an API."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any

MAX_ITEMS = 1_000_000_000
MAX_PAGE_SIZE = 10_000
MAX_LINKS = 25


class PaginationError(ValueError):
    """Raised when pagination inputs are invalid or unbounded."""


@dataclass(frozen=True)
class PaginationResult:
    total_items: int
    page_size: int
    current_page: int
    total_pages: int
    offset: int
    limit: int
    first_item: int | None
    last_item: int | None
    previous_page: int | None
    next_page: int | None
    navigation: list[int | str]


def require_integer(name: str, value: Any, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PaginationError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise PaginationError(f"{name} must be between {minimum} and {maximum}")
    return value


def navigation_window(current_page: int, total_pages: int, max_links: int) -> list[int | str]:
    """Return page numbers with stable ellipsis markers and fixed endpoints."""
    if total_pages == 0:
        return []
    if total_pages <= max_links:
        return list(range(1, total_pages + 1))

    interior_slots = max_links - 2
    start = max(2, current_page - interior_slots // 2)
    end = start + interior_slots - 1
    if end >= total_pages:
        end = total_pages - 1
        start = end - interior_slots + 1

    pages: list[int | str] = [1]
    if start > 2:
        pages.append("…")
    pages.extend(range(start, end + 1))
    if end < total_pages - 1:
        pages.append("…")
    pages.append(total_pages)
    return pages


def simulate(total_items: int, page_size: int, current_page: int, max_links: int = 7) -> PaginationResult:
    total_items = require_integer("total items", total_items, minimum=0, maximum=MAX_ITEMS)
    page_size = require_integer("page size", page_size, minimum=1, maximum=MAX_PAGE_SIZE)
    max_links = require_integer("max links", max_links, minimum=5, maximum=MAX_LINKS)
    total_pages = (total_items + page_size - 1) // page_size

    maximum_page = max(1, total_pages)
    current_page = require_integer("current page", current_page, minimum=1, maximum=maximum_page)
    if total_pages == 0:
        return PaginationResult(
            total_items=0,
            page_size=page_size,
            current_page=1,
            total_pages=0,
            offset=0,
            limit=page_size,
            first_item=None,
            last_item=None,
            previous_page=None,
            next_page=None,
            navigation=[],
        )

    offset = (current_page - 1) * page_size
    return PaginationResult(
        total_items=total_items,
        page_size=page_size,
        current_page=current_page,
        total_pages=total_pages,
        offset=offset,
        limit=page_size,
        first_item=offset + 1,
        last_item=min(offset + page_size, total_items),
        previous_page=current_page - 1 if current_page > 1 else None,
        next_page=current_page + 1 if current_page < total_pages else None,
        navigation=navigation_window(current_page, total_pages, max_links),
    )


def render_text(result: PaginationResult) -> str:
    item_range = "none" if result.first_item is None else f"{result.first_item}-{result.last_item}"
    navigation = " ".join(str(item) for item in result.navigation) or "none"
    previous_page = result.previous_page if result.previous_page is not None else "none"
    next_page = result.next_page if result.next_page is not None else "none"
    return "\n".join(
        [
            "Pagination simulation",
            f"Items: {result.total_items}",
            f"Page: {result.current_page} of {result.total_pages}",
            f"Range: {item_range}",
            f"Request: offset={result.offset} limit={result.limit}",
            f"Previous: {previous_page}",
            f"Next: {next_page}",
            f"Navigation: {navigation}",
        ]
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate one offset-pagination state offline.")
    parser.add_argument("--total-items", type=int, required=True, help="number of available records")
    parser.add_argument("--page-size", type=int, required=True, help="records requested per page")
    parser.add_argument("--page", type=int, default=1, help="one-based current page")
    parser.add_argument("--max-links", type=int, default=7, help="numbered links before ellipses (5-25)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of the readable report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = simulate(args.total_items, args.page_size, args.page, args.max_links)
    except PaginationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
