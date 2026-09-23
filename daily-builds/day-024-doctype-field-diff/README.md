# Day 024 — DocType Field Diff

DocType Field Diff compares the field structure of two exported Frappe DocType JSON files before a schema change is applied.

It reports added, removed, reordered and structurally changed fields. The report intentionally ignores labels, descriptions, defaults and arbitrary properties so confidential text and environment-specific values do not leak into diagnostics.

## Run

Python 3.10 or newer is sufficient; there are no third-party dependencies.

```bash
python3 doctype_field_diff.py baseline-doctype.json candidate-doctype.json
python3 doctype_field_diff.py baseline-doctype.json candidate-doctype.json --json
```

Exit codes:

- `0` — no structural differences
- `1` — differences found
- `2` — invalid input

Run the tests:

```bash
python3 -m unittest -v
```

## Skills practiced

- Defensive JSON validation
- Frappe DocType field conventions
- Deterministic schema comparison
- Privacy-conscious diagnostic output
- CLI text and JSON reporting
- Standard-library automated tests

## Safety boundary

This tool reads supplied JSON files only. It does not connect to Frappe, modify DocTypes, run migrations, or inspect document records. Use sanitized exports and review every reported change before applying it to a real site.

## Next improvement

Add an opt-in rules file for teams that need to compare extra, explicitly allowlisted DocType properties.
