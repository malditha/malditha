# Day 025 — Role Matrix

Role Matrix turns a sanitized list of Frappe DocType permission rows into a compact role-by-action review report.

It aggregates permission levels, shows which standard actions each role receives per DocType, and identifies identical or conflicting rows that share the same DocType, role and permission level. Unknown input properties are discarded so user details and unrelated export metadata do not appear in the report.

## Run

Python 3.10 or newer is sufficient; there are no third-party dependencies.

```bash
python3 role_matrix.py sample-permissions.json
python3 role_matrix.py sample-permissions.json --json
```

Exit codes:

- `0` — matrix created with no duplicate or conflicting keys
- `1` — matrix created with findings to review
- `2` — unreadable or invalid input

Run the tests:

```bash
python3 -m unittest -v
```

## Skills practiced

- Defensive JSON validation
- Frappe role-permission conventions
- Permission-level aggregation
- Deterministic matrix reporting
- Data minimization
- Standard-library CLI testing

## Safety boundary

This tool reads a supplied JSON file only. It does not connect to Frappe, inspect users, decide whether access is appropriate, or change Role Permission Manager settings. Use sanitized rows and have an authorized administrator review the output against actual business policy.

## Next improvement

Add an optional policy file that marks explicitly approved actions for comparison without treating generic permission patterns as security rules.
