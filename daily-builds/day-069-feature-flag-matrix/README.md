# Feature Flag Matrix

Generate an exhaustive, deterministic test matrix for a small set of boolean feature flags. The tool excludes states that violate declared dependencies and repeats valid states across named environments.

## Run and test

Python 3.10+; no external dependencies.

```sh
python3 matrix.py sample.json
python3 -m unittest -v
```

Redirect stdout to save JSON. Exit 0 means success; exit 2 means invalid input.

## Input

Use exactly `flags`, `environments` and `requires`. Flags and environments contain 1–8 unique lowercase identifiers (up to 40 characters). A dependency `["preview","search"]` means preview may be on only when search is on. Both flags must be declared. Duplicate dependencies and self-dependencies are rejected; cycles are allowed and constrain the flags to compatible states.

The limit is eight flags (256 combinations), eight environments and 128 KB of input. Output has stable case IDs, explicit booleans, and counts of valid and excluded combinations. Names are sorted so input ordering does not change the matrix.

This is a test-plan generator, not a flag service. It never connects to environments, changes production configuration, or verifies application behavior. Review dependencies before using the output as a test plan.

## Skills practiced

Combinatorial test design, boolean implication, deterministic generation, defensive JSON validation and standard-library tests.

## Next improvement

Add optional expected-outcome labels for specific scenarios while retaining a clear distinction between planned and executed tests.
