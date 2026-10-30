# Day 061 — Boundary Value Generator

Generate small, deterministic test datasets for the exact edges where input validation often fails. A JSON specification describes integer, number, or string fields; the CLI emits values immediately below, exactly at, and immediately above each configured boundary, with the expected validity of every case.

## Run

```bash
python boundary_value_generator.py example-spec.json
python boundary_value_generator.py example-spec.json --output cases.json
python -m unittest -v
```

The tool uses only Python's standard library. It accepts at most 100 fields, a 256 KB specification, and 1,000 generated cases. Unknown keys, duplicate JSON keys, duplicate field names, inverted ranges, non-finite numbers, and incompatible constraints are rejected.

## Skills practiced

- Equivalence partitions and boundary-value analysis
- Exact decimal stepping and stable case ordering
- Defensive JSON validation and bounded input handling
- Testable CLI design and standard-library unit tests

## Scope

The generator creates candidate cases; it does not run an application, infer business rules, generate personal data, or prove that a validation policy is correct. Review the specification and expected results before using them in a test suite.

## Next improvement

Add optional enumerated values and an adapter that renders cases as parameterized tests for a selected framework.
