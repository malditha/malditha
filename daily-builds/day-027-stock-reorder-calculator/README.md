# Stock Reorder Calculator

Stock Reorder Calculator is a dependency-free Python CLI that turns sanitized inventory-planning inputs into reviewable reorder suggestions. It combines average daily usage, lead time and safety stock into a reorder point, includes quantities already on order, then applies minimum-order and pack-size rules.

It is an offline planning tool. It does not connect to Frappe or ERPNext, inspect suppliers, change stock, or create purchase orders.

## Run

Requires Python 3.10 or newer.

```bash
cd daily-builds/day-027-stock-reorder-calculator
python3 stock_reorder_calculator.py sample-items.json
python3 stock_reorder_calculator.py sample-items.json --json
```

The command returns exit code `1` when at least one item needs reordering, `0` when every item is sufficient, and `2` for invalid input.

Formula:

```text
reorder point = average daily usage × lead time days + safety stock
available supply = current quantity + quantity already on order
shortage = max(0, reorder point − available supply)
```

When there is a shortage, the suggestion honors the minimum order and rounds upward to a complete pack.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile stock_reorder_calculator.py
```

## Skills practiced

- Inventory reorder-point calculations
- Minimum-order and pack-size rounding
- Defensive JSON validation and bounded input
- Deterministic text and JSON reports
- Standard-library unit testing

## Next improvement

Add optional demand-history input with a clearly documented averaging window while keeping the calculator offline and review-only.
