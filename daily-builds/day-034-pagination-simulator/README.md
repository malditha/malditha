# Pagination Simulator

An offline, dependency-free Python CLI for checking one offset-pagination state before wiring it into an API or interface.

## Purpose

Pagination mistakes often appear at the boundaries: an empty result, a partial final page, an invalid page number, or a navigation bar with too many links. This tool calculates the total pages, item range, `offset` and `limit`, previous and next pages, and an ellipsis-aware navigation window from explicit numbers.

It does not request an API, fetch records, or claim that offset pagination is suitable for every dataset. Frequently changing or very large datasets may need cursor-based pagination instead.

## Run

Requires Python 3.10 or newer.

```bash
python3 pagination_simulator.py --total-items 263 --page-size 25 --page 6
```

Machine-readable output:

```bash
python3 pagination_simulator.py --total-items 263 --page-size 25 --page 6 --json
```

Run the tests:

```bash
python3 -m unittest -v
```

## Skills practiced

- Offset-pagination arithmetic and boundary conditions
- Stable ellipsis-aware navigation windows
- Bounded integer validation
- Human-readable and JSON CLI output
- Standard-library unit and subprocess testing

## Design notes

- Page numbers are one-based; offsets are zero-based.
- Empty collections accept page 1 and return no item range.
- Invalid pages are rejected instead of silently clamped.
- Inputs are bounded to keep accidental values manageable.
- The tool reports math only and never exposes or stores record data.

## Next improvement

Add a separate cursor-pagination simulator that demonstrates opaque cursors, forward-only traversal, and the trade-offs between stable cursors and arbitrary page jumps.
