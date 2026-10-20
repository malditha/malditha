# Workflow Input Validator

Day 051 of the 100 Days of Code challenge.

## Purpose

Workflow Input Validator checks one local JSON payload against a small declarative contract before the data enters an automation. It reports missing, unknown, mistyped, out-of-range and over-limit fields without printing supplied values.

This is an offline preflight utility, not an n8n node or a full JSON Schema implementation. It does not execute workflows, call webhooks, inspect credentials, fetch remote data or prove that downstream business logic is safe.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
python validator.py contract.json payload.json
python validator.py contract.json payload.json --json
```

Exit codes:

- `0`: payload is valid
- `1`: payload is readable but violates the contract
- `2`: contract, payload or file input is invalid

Run the tests:

```bash
python -m unittest -v test_validator.py
```

## Contract

The contract supports:

- Required and optional fields
- String, integer, number, boolean, array, object and null types
- String length and allowlisted string choices
- Array length and homogeneous item types
- Numeric minimum and maximum bounds
- Rejecting or allowing undeclared top-level fields

Both files are limited to 1 MB and 100 top-level fields. Reports include field names, rule codes and generic messages, but never payload values. Field names can still be sensitive, so use sanitized contracts and payloads.

## Skills practiced

- Defensive JSON parsing and duplicate-key rejection
- Declarative validation rules
- Type-safe handling of Python booleans and numbers
- Data-minimized text and JSON reporting
- Automation-friendly exit codes
- Test-first development with `unittest`

## Next improvement

Add an optional mapping layer that converts selected validator issue codes into n8n error-branch labels without exposing payload values.
