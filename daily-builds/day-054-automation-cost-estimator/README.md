# Automation Cost Estimator

Day 054 of the 100 Days of Code challenge.

## Purpose

Automation Cost Estimator turns a small local JSON plan into a transparent monthly estimate for workflow runs, operations and fixed service costs. It helps compare assumptions before connecting an automation to paid services.

It does not connect to n8n, inspect billing accounts, fetch provider prices or promise an exact invoice. Users must supply and verify current rates.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
python cost_estimator.py plan.json
python cost_estimator.py plan.json --json
```

Exit code `0` means an estimate was created; `2` means the plan was invalid.

Run the tests:

```bash
python -m unittest -v test_cost_estimator.py
```

## Input boundaries

- Models daily workflow runs, operations per run, per-1,000 rates and fixed monthly costs
- Uses decimal arithmetic and explicit money rounding
- Limits plans to 50 workflows and files to 100 KB
- Rejects negative, non-finite, duplicate-name and undeclared values
- Never reads credentials, billing data or remote accounts

## Skills practiced

- Automation cost modeling
- Precise decimal arithmetic
- Defensive JSON validation
- Deterministic text and JSON reports
- Workflow-friendly exit codes
- Standard-library testing with `unittest`

## Next improvement

Add side-by-side scenarios for expected, low and high workflow volume.
