# Data Shape Profiler

Day 038 of the 100 Days of Code challenge.

## Purpose

Data Shape Profiler summarizes the structure of a JSON array before you write an importer, validator, or transformation. It reports each field path's presence, missing and null counts, and observed JSON types without printing source values.

The profiler is deliberately bounded and read-only. It accepts object records, recursively inspects nested objects, treats arrays as a type boundary, and rejects inputs that exceed configurable record, field, or depth limits.

## Run

Use Python 3.10 or newer. No third-party packages are required.

```bash
python data_shape_profiler.py records.json
python data_shape_profiler.py records.json --json
```

Optional safety limits:

```bash
python data_shape_profiler.py records.json --max-records 500 --max-fields 200 --max-depth 6
```

Run the tests:

```bash
python -m unittest -v
```

## Skills practiced

- Recursive traversal of nested JSON objects
- Defensive input validation and bounded processing
- Type classification that distinguishes booleans from integers
- Privacy-conscious reporting that omits source values
- Human-readable and machine-readable CLI output
- Standard-library unit and command-line tests

## Next improvement

Add an opt-in array-item profiler that samples a bounded number of elements and reports their shapes separately from the parent field.
